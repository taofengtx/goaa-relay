"""Clerk identity-mapping invariants (real PostgreSQL, ``goaa_c2test`` only).

These are the database-level guarantees behind the "Clerk is the only identity
authority" rule. Every statement runs inside an explicit transaction that is
always rolled back, so the suite leaves no rows behind and ``identity_events``
(which is append-only by design) never needs to be cleaned up.

Note: ``psql`` echoes command tags (``BEGIN`` / ``INSERT 0 1`` / ``ROLLBACK``)
to stdout, so scalar assertions filter those out instead of using the raw text.
"""

from __future__ import annotations

import re

from conftest import MIGRATIONS_DIR, SERVICE_ROOT, psql

# A distinct issuer per test keeps the fixtures independent of each other.
ISSUER_A = "https://clerk.goaa-c2test.example.test"
ISSUER_B = "https://clerk-production.goaa.example.test"

_TAG = re.compile(
    r"^(BEGIN|COMMIT|ROLLBACK|SET|RESET|SAVEPOINT|RELEASE|"
    r"INSERT \d+ \d+|UPDATE \d+|DELETE \d+|COPY \d+|TRUNCATE TABLE)$"
)


def _exec(*statements: str):
    """Run statements in one transaction that is always rolled back."""
    body = "\n".join(s.strip().rstrip(";") + ";" for s in statements)
    return psql(f"begin;\n{body}\nrollback;")


def _scalar(*statements: str) -> str:
    """Last non-tag line of stdout, i.e. the value the last SELECT produced."""
    result = _exec(*statements)
    assert result.returncode == 0, result.stderr
    lines = [ln.strip() for ln in result.stdout.splitlines()]
    values = [ln for ln in lines if ln and not _TAG.match(ln)]
    assert values, f"no scalar output; stdout={result.stdout!r}"
    return values[-1]


def _mk_user(email: str | None) -> str:
    email_sql = "null" if email is None else f"'{email}'"
    return f"insert into users (email, password_hash) values ({email_sql}, null)"


def _bind(email: str, issuer: str, subject: str, snapshot: str | None = None) -> str:
    snap = "null" if snapshot is None else f"'{snapshot}'"
    return (
        "insert into user_identities (user_id, issuer, subject, email_snapshot, email_verified) "
        f"select id, '{issuer}', '{subject}', {snap}, true from users where email = '{email}'"
    )


# ---------------------------------------------------------------------------
# credential storage
# ---------------------------------------------------------------------------
def test_credential_less_and_emailless_user_is_representable():
    """A `+1` SMS-OTP sign-up has neither a GOAA password nor an e-mail."""
    result = _exec(_mk_user(None), "select 1")
    assert result.returncode == 0, result.stderr
    for column in ("email", "password_hash"):
        assert (
            _scalar(
                "select is_nullable from information_schema.columns "
                f"where table_name = 'users' and column_name = '{column}'"
            )
            == "YES"
        ), column


def test_goaa_never_requires_a_password_column():
    got = _scalar(
        "select is_nullable from information_schema.columns "
        "where table_name = 'users' and column_name = 'password_hash'"
    )
    assert got == "YES", "users.password_hash must stay nullable for Clerk"


# ---------------------------------------------------------------------------
# mapping cardinality
# ---------------------------------------------------------------------------
def test_clerk_subject_is_unique_per_issuer():
    """One Clerk user must never map to two GOAA users."""
    result = _exec(
        _mk_user("dupe-a@example.test"),
        _mk_user("dupe-b@example.test"),
        _bind("dupe-a@example.test", ISSUER_A, "user_clerk_dupe", "dupe-a@example.test"),
        _bind("dupe-b@example.test", ISSUER_A, "user_clerk_dupe", "dupe-b@example.test"),
    )
    assert result.returncode != 0
    assert "user_identities_issuer_subject_key" in result.stderr


def test_same_subject_under_a_different_issuer_is_allowed():
    """Development and production issuers are separate namespaces."""
    got = _scalar(
        _mk_user("iss-a@example.test"),
        _mk_user("iss-b@example.test"),
        _bind("iss-a@example.test", ISSUER_A, "user_clerk_same"),
        _bind("iss-b@example.test", ISSUER_B, "user_clerk_same"),
        "select count(*) from user_identities where subject = 'user_clerk_same'",
    )
    assert got == "2"


def test_one_goaa_user_cannot_hold_two_clerk_identities():
    result = _exec(
        _mk_user("one-user@example.test"),
        _bind("one-user@example.test", ISSUER_A, "user_clerk_one"),
        _bind("one-user@example.test", ISSUER_A, "user_clerk_two"),
    )
    assert result.returncode != 0
    assert "user_identities_user_provider_key" in result.stderr


def test_provider_is_fixed_to_clerk():
    result = _exec(
        _mk_user("bad-provider@example.test"),
        "insert into user_identities (user_id, provider, issuer, subject) "
        f"select id, 'openclaw', '{ISSUER_A}', 'user_clerk_bad' from users "
        "where email = 'bad-provider@example.test'",
    )
    assert result.returncode != 0
    assert "user_identities_provider_fixed" in result.stderr


def test_blank_subject_is_rejected():
    result = _exec(
        _mk_user("blank-subject@example.test"),
        "insert into user_identities (user_id, issuer, subject) "
        f"select id, '{ISSUER_A}', '   ' from users where email = 'blank-subject@example.test'",
    )
    assert result.returncode != 0
    assert "user_identities_subject_not_blank" in result.stderr


def test_unverified_snapshot_is_allowed_but_flagged():
    """email_verified defaults to false; nothing may treat a snapshot as proof."""
    got = _scalar(
        _mk_user("unverified@example.test"),
        "insert into user_identities (user_id, issuer, subject, email_snapshot) "
        f"select id, '{ISSUER_A}', 'user_clerk_unverified', 'unverified@example.test' "
        "from users where email = 'unverified@example.test'",
        "select email_verified::text from user_identities where subject = 'user_clerk_unverified'",
    )
    assert got == "false"


# ---------------------------------------------------------------------------
# e-mail must never decide account ownership
# ---------------------------------------------------------------------------
def test_same_email_snapshot_on_two_subjects_does_not_merge_accounts():
    got = _scalar(
        _mk_user("shared-1@example.test"),
        _mk_user("shared-2@example.test"),
        _bind("shared-1@example.test", ISSUER_A, "user_clerk_shared_1", "shared@example.test"),
        _bind("shared-2@example.test", ISSUER_A, "user_clerk_shared_2", "shared@example.test"),
        "select count(distinct subject) from user_identities "
        "where lower(email_snapshot) = 'shared@example.test'",
    )
    # Two distinct subjects coexist on the same snapshot address: no auto-merge.
    assert got == "2"


def test_no_unique_index_on_email_snapshot():
    got = _scalar(
        "select count(*) from pg_indexes where tablename = 'user_identities' "
        "and indexdef ilike '%unique%' and indexdef ilike '%email_snapshot%'"
    )
    assert got == "0", "a unique e-mail index would invite silent account merging"


# ---------------------------------------------------------------------------
# audit trail
# ---------------------------------------------------------------------------
def test_identity_events_are_append_only():
    updated = _exec(
        "insert into identity_events (event_type, issuer, subject, email_masked) "
        f"values ('identity.jit_create', '{ISSUER_A}', 'user_clerk_evt', 's***@example.test')",
        "update identity_events set event_type = 'identity.bind'",
    )
    assert updated.returncode != 0
    assert "append-only" in updated.stderr

    deleted = _exec(
        "insert into identity_events (event_type, issuer, subject) "
        f"values ('identity.bind', '{ISSUER_A}', 'user_clerk_evt2')",
        "delete from identity_events",
    )
    assert deleted.returncode != 0
    assert "append-only" in deleted.stderr


def test_identity_events_are_not_rewritable_by_the_application_role():
    for privilege in ("UPDATE", "DELETE"):
        rows = psql(
            f"select has_table_privilege('goaa_c2_app', 'identity_events', '{privilege}')::text"
        )
        assert rows.returncode == 0, rows.stderr
        assert rows.stdout.strip() == "false", privilege

    insert_rows = psql(
        "select has_table_privilege('goaa_c2_app', 'identity_events', 'INSERT')::text"
    )
    assert insert_rows.stdout.strip() == "true"


def test_identity_event_types_are_constrained():
    result = _exec("insert into identity_events (event_type) values ('identity.whatever')")
    assert result.returncode != 0
    assert "identity_events_type_known" in result.stderr


def test_identity_events_reject_non_object_detail():
    result = _exec(
        "insert into identity_events (event_type, detail) "
        "values ('identity.bind', '\"not-an-object\"'::jsonb)"
    )
    assert result.returncode != 0
    assert "identity_events_detail_is_object" in result.stderr


# ---------------------------------------------------------------------------
# migration plumbing
# ---------------------------------------------------------------------------
def test_rollback_file_is_never_auto_applied():
    migrations = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert "0005_user_identities.sql" in migrations
    assert not any("down" in name or "rollback" in name for name in migrations)
    assert (SERVICE_ROOT / "migrations" / "rollback" / "0005_user_identities.down.sql").is_file()
