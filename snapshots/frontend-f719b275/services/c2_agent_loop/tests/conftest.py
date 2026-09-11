"""pytest fixtures for the C2 agent-application loop service.

The tests run against a **real PostgreSQL 16 cluster** on ``127.0.0.1:5433``,
using the dedicated ``goaa_c2test`` database (never the ``goaa_c2`` database and
never anything production). The whole ``public`` schema is dropped and rebuilt
from the migration files at session start, so every run starts from a known
empty state.

Run them on the C2 host with::

    GOAA_C2_DB_NAME=goaa_c2test /opt/goaa-test/venv/bin/python -m pytest -q
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import app as app_package  # noqa: E402

if SERVICE_ROOT not in Path(app_package.__file__).resolve().parents:
    raise RuntimeError(f"the wrong 'app' package was importable: {app_package.__file__}")

from app.config import Settings  # noqa: E402

TEST_DB = os.environ.get("GOAA_C2_TEST_DB_NAME", "goaa_c2test")
DB_HOST = os.environ.get("GOAA_C2_DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("GOAA_C2_DB_PORT", "5433")
APP_USER = os.environ.get("GOAA_C2_DB_USER", "goaa_c2_app")
APP_PASSFILE = os.environ.get("GOAA_C2_DB_PASSFILE", "/opt/goaa-test/env/app.pgpass")
MIGRATE_USER = os.environ.get("GOAA_C2_MIGRATE_USER", "goaa_c2_migrate")
MIGRATE_PASSFILE = os.environ.get("GOAA_C2_MIGRATE_PASSFILE", "/opt/goaa-test/env/migrate.pgpass")
PSQL = os.environ.get("GOAA_C2_PSQL", "/usr/lib/postgresql/16/bin/psql")
MIGRATIONS_DIR = SERVICE_ROOT / "migrations"

SESSION_SECRET = "test-only-session-secret-0123456789abcdef"
COOKIE_NAME = "goaa_c2_loop_test_session"


# ---------------------------------------------------------------------------
# database helpers
# ---------------------------------------------------------------------------
def psql(sql: str = "", *, file: Path | None = None, as_migrate: bool = True, db: str = TEST_DB):
    args = [PSQL, "-h", DB_HOST, "-p", DB_PORT, "-U", MIGRATE_USER if as_migrate else APP_USER,
            "-d", db, "-v", "ON_ERROR_STOP=1", "-X", "-At"]
    if file is not None:
        args += ["-1", "-f", str(file)]
    else:
        args += ["-c", sql]
    env = dict(os.environ)
    env["PGPASSFILE"] = MIGRATE_PASSFILE if as_migrate else APP_PASSFILE
    return subprocess.run(args, env=env, capture_output=True, text=True)


def app_sql(sql: str) -> str:
    """Run one query as the runtime application role; return the tuple-only output."""
    result = psql(sql, as_migrate=False)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def app_settings(private_dir: str, **overrides) -> Settings:
    base = dict(
        environment="c2-test",
        db_host=DB_HOST,
        db_port=int(DB_PORT),
        db_name=TEST_DB,
        db_user=APP_USER,
        db_passfile=APP_PASSFILE,
        migrate_user=MIGRATE_USER,
        migrate_passfile=MIGRATE_PASSFILE,
        psql_binary=PSQL,
        session_secret=SESSION_SECRET,
        session_cookie_name=COOKIE_NAME,
        private_files_dir=private_dir,
        storage_label="c2-local-private",
        scanner_label="stub",
        ocr_label="rules-only",
    )
    base.update(overrides)
    return Settings(**base)


@pytest.fixture(scope="session")
def private_files_dir():
    with tempfile.TemporaryDirectory(prefix="goaa-c2-loop-tests-") as tmp:
        yield tmp


@pytest.fixture(scope="session", autouse=True)
def prepared_database(private_files_dir):
    """Rebuild the test schema from the migration files."""
    check = psql("select 1", db="postgres")
    if check.returncode != 0:
        pytest.skip(f"test database unreachable: {check.stderr.strip()[:200]}")

    reset = psql(
        """
        drop schema if exists public cascade;
        create schema public;
        revoke all on schema public from public;
        grant all on schema public to goaa_c2_migrate;
        grant usage on schema public to goaa_c2_app;
        alter default privileges for role goaa_c2_migrate in schema public
            grant select, insert, update, delete on tables to goaa_c2_app;
        alter default privileges for role goaa_c2_migrate in schema public
            grant usage, select on sequences to goaa_c2_app;
        """
    )
    assert reset.returncode == 0, reset.stderr

    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        result = psql(file=path)
        assert result.returncode == 0, f"{path.name}: {result.stderr}"
    return True


@pytest.fixture()
def settings(private_files_dir) -> Settings:
    return app_settings(private_files_dir)


@pytest.fixture()
def client(settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def api_base():
    return "/api/v1/agent-loop"


# ---------------------------------------------------------------------------
# small helpers used by the tests
# ---------------------------------------------------------------------------
def register(client, email: str, password: str = "correct-horse-battery", **extra):
    return client.post(
        "/api/v1/agent-loop/auth/register",
        json={"email": email, "password": password, **extra},
    )


def login(client, email: str, password: str = "correct-horse-battery") -> str:
    response = client.post("/api/v1/agent-loop/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def grant_role_via_operator(email: str, role: str) -> None:
    """Mirror tools/grant_role.py: the *migration* role grants admin, not the app role."""
    result = psql(
        f"insert into user_roles (user_id, role) "
        f"select id, '{role}' from users where lower(email) = lower('{email}') "
        f"on conflict (user_id, role) do nothing"
    )
    assert result.returncode == 0, result.stderr


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
