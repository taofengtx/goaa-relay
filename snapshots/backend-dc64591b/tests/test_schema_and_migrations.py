"""Schema, migration and privilege guarantees (real PostgreSQL)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from conftest import APP_USER, MIGRATE_PASSFILE, SERVICE_ROOT, psql

EXPECTED_TABLES = {
    "schema_migrations",
    "users",
    "user_roles",
    "email_verifications",
    "user_sessions",
    "agent_applications",
    "agent_licenses",
    "agent_license_documents",
    "agent_review_events",
    "idempotency_keys",
    "user_identities",
    "identity_events",
}


def _rows(sql: str, *, as_migrate: bool = True) -> list[str]:
    result = psql(sql, as_migrate=as_migrate)
    assert result.returncode == 0, result.stderr
    return [line for line in result.stdout.strip().splitlines() if line]


def test_all_migrations_are_applied():
    versions = _rows("select version from schema_migrations order by version")
    assert versions == [
        "0001_identity",
        "0002_applications",
        "0003_audit_append_only",
        "0004_role_grant_guard",
        "0005_user_identities",
    ]


def test_expected_tables_exist():
    found = set(_rows("select tablename from pg_tables where schemaname = 'public'"))
    assert EXPECTED_TABLES <= found, EXPECTED_TABLES - found


def test_email_uniqueness_is_case_insensitive():
    index = _rows(
        "select indexdef from pg_indexes where tablename = 'users' and indexname = 'users_email_lower_key'"
    )
    assert index, "the case-insensitive unique index is missing"
    assert "lower(email)" in index[0]


def test_migrations_are_re_runnable():
    """Every migration file is forward-only and can be applied again safely."""
    for path in sorted((SERVICE_ROOT / "migrations").glob("*.sql")):
        result = psql(file=path)
        assert result.returncode == 0, f"re-running {path.name} failed: {result.stderr}"


def test_migration_tool_reports_nothing_pending():
    result = subprocess.run(
        [sys.executable, "-m", "tools.migrate", "--status"],
        cwd=str(SERVICE_ROOT),
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GOAA_C2_DB_NAME": "goaa_c2test",
            "GOAA_C2_MIGRATE_PASSFILE": MIGRATE_PASSFILE,
        },
    )
    assert result.returncode == 0, result.stderr
    assert "pending : (none)" in result.stdout, result.stdout


def test_audit_trail_is_append_only_in_the_database():
    trigger = _rows(
        "select tgname from pg_trigger where tgrelid = 'agent_review_events'::regclass and not tgisinternal"
    )
    assert "trg_agent_review_events_append_only" in trigger

    # layer 1: even the table owner (the migration role) cannot rewrite history
    update_attempt = psql("update agent_review_events set action = 'tampered'")
    assert update_attempt.returncode != 0
    assert "append-only" in update_attempt.stderr

    delete_attempt = psql("delete from agent_review_events")
    assert delete_attempt.returncode != 0
    assert "append-only" in delete_attempt.stderr


def test_audit_trail_is_unwritable_by_the_application_role():
    # layer 2: the runtime role does not even hold UPDATE/DELETE
    update_attempt = psql("update agent_review_events set action = 'tampered'", as_migrate=False)
    assert update_attempt.returncode != 0
    assert "permission denied" in update_attempt.stderr or "append-only" in update_attempt.stderr

    delete_attempt = psql("delete from agent_review_events", as_migrate=False)
    assert delete_attempt.returncode != 0
    assert "permission denied" in delete_attempt.stderr or "append-only" in delete_attempt.stderr


def test_app_role_cannot_update_or_delete_the_audit_trail():
    assert _rows(
        "select has_table_privilege('goaa_c2_app', 'agent_review_events', 'UPDATE')::text"
    ) == ["false"]
    assert _rows(
        "select has_table_privilege('goaa_c2_app', 'agent_review_events', 'DELETE')::text"
    ) == ["false"]
    assert _rows("select has_table_privilege('goaa_c2_app', 'agent_review_events', 'INSERT')::text") == ["true"]


def test_app_role_is_not_privileged():
    flags = _rows(
        "select rolsuper::text, rolcreatedb::text, rolcreaterole::text from pg_roles where rolname = 'goaa_c2_app'"
    )
    assert flags == ["false|false|false"]

    assert psql("create table nope (x int)", as_migrate=False).returncode != 0
    assert psql("create database nope", as_migrate=False).returncode != 0


def test_application_role_cannot_mint_an_administrator():
    psql("insert into users (email, password_hash) values ('guard@example.test', 'x')")
    attempt = psql(
        "insert into user_roles (user_id, role) "
        "select id, 'admin' from users where email = 'guard@example.test'",
        as_migrate=False,
    )
    assert attempt.returncode != 0
    assert "may not grant the admin role" in attempt.stderr

    # ... while the operator (migration) role may
    allowed = psql(
        "insert into user_roles (user_id, role) "
        "select id, 'admin' from users where email = 'guard@example.test' "
        "on conflict (user_id, role) do nothing"
    )
    assert allowed.returncode == 0, allowed.stderr


def test_service_is_postgres_native_not_a_sqlite_port():
    sources = list((SERVICE_ROOT / "app").glob("*.py")) + list((SERVICE_ROOT / "tools").glob("*.py"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    assert "sqlite3" not in text
    assert "psycopg" in text
    assert list((SERVICE_ROOT / "migrations").glob("*.sql"))
    assert APP_USER == "goaa_c2_app"
