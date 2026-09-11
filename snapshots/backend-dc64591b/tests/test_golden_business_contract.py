"""Business-contract compatibility: does the *golden* auth accept our token?

The bridge is only worth anything if the credential it mints is the credential
the golden business surface already knows how to authenticate. Asserting that
our own `verify` route returns 200 proves nothing about that: it would also
pass for a private session system invented for the test page.

So this file does the opposite: it reads the golden runtime's authentication
source **out of the golden clone**, takes its SQL verbatim, and runs it against
the same rows this service writes.

Reading the source instead of restating it is the point:

  * `runtime/order_db.py` is read from the git object store at a pinned ref, so
    the statements in this test are the ones that were archived, not ones this
    test paraphrases (the blob sha256 is asserted, see GOLDEN_BLOB_SHA256);
  * the only rewrites allowed are mechanical and are asserted to be the only
    ones: the table name, and PostgreSQL's `now()` for SQLite's clock (the
    double is SQLite, so the statement has to be runnable there).

What this proves, and what it does not:

  * proves the *contract*: the columns, the lookup predicate and the revocation
    mechanism this service uses are exactly the ones the golden function reads
    and writes, and a token minted through the bridge resolves to the right
    business principal — and to nothing after revocation;
  * does not prove PostgreSQL execution. These statements run against the
    SQLite double, which mirrors 0005/0006. Applying 0006 and re-running
    against the real cluster remains an operator step.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

from app import golden_session
from support.sqlite_double import DoubleCursor, connect, count, seed_identity

CLONE = pathlib.Path("/home/aika/Projects/goaa-ai-main")
REF = "HEAD"
GOLDEN_PATH = "runtime/order_db.py"

#: sha256 of the golden blob this test was written against. If the clone moves
#: on, the test fails loudly instead of silently testing a different contract.
GOLDEN_BLOB_SHA256 = "74a2573f1f5686467e5ca8878b3d89bcf501b2e49ea70e778dee6085863481d4"

BUSINESS_TABLE = "business_tokens"
MIGRATION = pathlib.Path(__file__).resolve().parents[1] / "migrations" / "0006_golden_business_session.sql"

UTC_ISSUER = "https://lenient-phoenix-9847.clerk.accounts.dev"
IDENTITY_USER = "9606620b-61a5-4a35-92ed-b9fce61500c2"
SUBJECT = "user_3JA2UKSDA9PB4BiLlf14HnAKiED"


def _golden_source() -> str:
    """The golden `order_db.py`, from git when possible, from disk otherwise."""

    if not CLONE.exists():
        pytest.skip(f"golden clone not present at {CLONE}")
    try:
        out = subprocess.run(
            ["git", "-C", str(CLONE), "show", f"{REF}:{GOLDEN_PATH}"],
            capture_output=True,
            check=True,
            text=True,
        )
        return out.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return (CLONE / GOLDEN_PATH).read_text()


def _blob_sha256() -> str:
    out = subprocess.run(
        ["git", "-C", str(CLONE), "show", f"{REF}:{GOLDEN_PATH}"],
        capture_output=True,
        check=True,
    )
    import hashlib

    return hashlib.sha256(out.stdout).hexdigest()


def _function_body(source: str, name: str) -> str:
    start = source.index(f"def {name}(")
    rest = source[start:]
    end = rest.find("\ndef ", 1)
    return rest if end == -1 else rest[:end]


def _extract_sql(source: str, name: str) -> list[str]:
    """Every `cur.execute(...)` SQL literal in a function, concatenated."""

    body = _function_body(source, name)
    statements = []
    for match in re.finditer(r'cur\.execute\(\s*((?:"[^"]*"\s*)+)', body):
        statements.append("".join(re.findall(r'"([^"]*)"', match.group(1))))
    return statements


@pytest.fixture(scope="module")
def golden_sql() -> dict[str, str]:
    source = _golden_source()
    lookup = _extract_sql(source, "authenticate_order_token")
    issue = _extract_sql(source, "issue_order_token")
    revoke = _extract_sql(source, "revoke_order_tokens")
    assert len(lookup) == 1 and len(issue) == 1 and len(revoke) == 1
    return {"lookup": lookup[0], "issue": issue[0], "revoke": revoke[0]}


def _as_sqlite(statement: str) -> tuple[str, list[str]]:
    """Apply, and report, the *only* rewrites allowed to reach the double."""

    rewrites = []
    mapped = statement
    if "goaa_order_tokens" in mapped:
        assert mapped.count("goaa_order_tokens") == 1
        mapped = mapped.replace("goaa_order_tokens", BUSINESS_TABLE)
        rewrites.append("table name goaa_order_tokens -> business_tokens")
    if "now()" in mapped:
        assert mapped.count("now()") == 1
        mapped = mapped.replace("now()", "strftime('%Y-%m-%dT%H:%M:%f+00:00','now')")
        rewrites.append("postgres now() -> sqlite clock")
    return mapped, rewrites


def _golden_authenticate(conn, token: str) -> dict | None:
    """The golden function's own semantics: `return dict(row) if row else None`."""

    statement, _ = _as_sqlite(_extract_sql(_golden_source(), "authenticate_order_token")[0])
    with DoubleCursor(conn) as cur:
        cur.execute(statement, (token,))
        row = cur.fetchone()
    return dict(row) if row else None


def _golden_revoke(conn, user_id: str) -> None:
    statement, _ = _as_sqlite(_extract_sql(_golden_source(), "revoke_order_tokens")[0])
    with DoubleCursor(conn) as cur:
        cur.execute(statement, (user_id,))
    conn.commit()


def _golden_issue(conn, user_id: str, token: str) -> None:
    statement, _ = _as_sqlite(_extract_sql(_golden_source(), "issue_order_token")[0])
    with DoubleCursor(conn) as cur:
        cur.execute(statement, (user_id, token, "customer"))
    conn.commit()


def _bridge_database():
    conn = connect()
    seed_identity(conn, user_id=IDENTITY_USER, subject=SUBJECT, issuer=UTC_ISSUER,
                  email="someone@example.com")
    linked = golden_session.ensure_subject(
        conn, user_id=IDENTITY_USER, issuer=UTC_ISSUER, subject=SUBJECT, email="someone@example.com"
    )
    return conn, linked["user_id"]


# ---------------------------------------------------------------------------
# the statements really come from the golden source
# ---------------------------------------------------------------------------
def test_the_golden_statements_were_read_from_the_golden_source(golden_sql):
    assert _blob_sha256() == GOLDEN_BLOB_SHA256, "the golden source moved; re-read the contract"

    assert golden_sql["lookup"] == (
        "SELECT user_id, role FROM goaa_order_tokens WHERE token=%s AND revoked_at IS NULL"
    )
    assert golden_sql["issue"] == (
        "INSERT INTO goaa_order_tokens (user_id, token, role) "
        "VALUES (%s,%s,%s) ON CONFLICT (user_id, token) DO NOTHING"
    )
    assert golden_sql["revoke"] == "UPDATE goaa_order_tokens SET revoked_at=now() WHERE user_id=%s"
    for statement in golden_sql.values():
        assert "goaa_order_tokens" in statement


def test_only_mechanical_rewrites_are_applied_to_reach_our_table(golden_sql):
    for statement in golden_sql.values():
        mapped, rewrites = _as_sqlite(statement)
        for rewrite in rewrites:
            assert rewrite in ("table name goaa_order_tokens -> business_tokens",
                               "postgres now() -> sqlite clock")
        # everything else is byte-identical
        assert mapped.replace(BUSINESS_TABLE, "goaa_order_tokens").replace(
            "strftime('%Y-%m-%dT%H:%M:%f+00:00','now')", "now()"
        ) == statement


def test_our_table_carries_every_column_the_golden_statements_use(golden_sql):
    ddl = MIGRATION.read_text()
    table = ddl[ddl.index(f"create table if not exists {BUSINESS_TABLE}") :]
    table = table[: table.index(");")]
    body = table.split("constraint")[0]

    # every column the golden statements touch must exist on our table
    for column in ("user_id", "token", "role", "revoked_at"):
        assert re.search(rf"\b{column}\b", " ".join(golden_sql.values()))
        assert re.search(rf"\b{column}\b", body), f"{column} missing from {BUSINESS_TABLE}"
    assert "unique" in body, "the golden lookup needs a unique token"
    # ...and the ON CONFLICT clause needs a unique constraint on exactly the pair
    assert "unique (user_id, token)" in table

    # columns we carry on top of the golden contract, for the record
    for extra in ("created_at", "issued_at", "last_used_at"):
        assert re.search(rf"\b{extra}\b", body)


# ---------------------------------------------------------------------------
# the actual compatibility assertions
# ---------------------------------------------------------------------------
def test_a_token_our_service_issued_is_accepted_by_the_golden_authentication(golden_sql):
    conn, principal = _bridge_database()
    session = golden_session.issue_token(
        conn, user_id=IDENTITY_USER, issuer=UTC_ISSUER, subject=SUBJECT
    )

    assert re.fullmatch(r"[0-9a-f]{32}", session["token"]), "the golden mints uuid4().hex"

    accepted = _golden_authenticate(conn, session["token"])

    assert accepted is not None, "the golden authentication did not recognise our token"
    assert accepted["user_id"] == principal
    assert accepted["role"] == "customer"

    # and both sides see the same principal for the same credential
    ours = golden_session.authenticate_token(conn, session["token"])
    assert ours["user_id"] == accepted["user_id"]
    assert ours["role"] == accepted["role"]


def test_the_golden_sign_out_statement_revokes_a_token_we_issued():
    conn, principal = _bridge_database()
    session = golden_session.issue_token(
        conn, user_id=IDENTITY_USER, issuer=UTC_ISSUER, subject=SUBJECT
    )
    assert _golden_authenticate(conn, session["token"]) is not None

    _golden_revoke(conn, principal)

    assert _golden_authenticate(conn, session["token"]) is None
    with pytest.raises(golden_session.BusinessTokenInvalid) as excinfo:
        golden_session.authenticate_token(conn, session["token"])
    assert excinfo.value.reason == golden_session.REASON_REVOKED


def test_our_sign_out_is_visible_to_the_golden_authentication():
    """The other direction: our revocation must be the golden's revocation."""

    conn, principal = _bridge_database()
    session = golden_session.issue_token(
        conn, user_id=IDENTITY_USER, issuer=UTC_ISSUER, subject=SUBJECT
    )

    golden_session.revoke_subject(conn, subject_id=principal, reason="sign_out")

    assert _golden_authenticate(conn, session["token"]) is None


def test_the_golden_issue_statement_is_accepted_by_our_table():
    """A token minted by the golden itself works through our authentication."""

    conn, principal = _bridge_database()
    token = golden_session.new_token()

    _golden_issue(conn, principal, token)

    assert count(conn, BUSINESS_TABLE) == 1
    resolved = golden_session.authenticate_token(conn, token)
    assert resolved["user_id"] == principal
    assert resolved["role"] == "customer"


def test_refresh_and_re_login_seen_through_the_golden_authentication():
    conn, principal = _bridge_database()
    first = golden_session.issue_token(conn, user_id=IDENTITY_USER, issuer=UTC_ISSUER, subject=SUBJECT)

    # refresh: the same credential, still the same principal
    assert _golden_authenticate(conn, first["token"])["user_id"] == principal
    assert _golden_authenticate(conn, first["token"])["user_id"] == principal

    # re-login: a new credential, and the previous one is gone for the golden too
    second = golden_session.issue_token(conn, user_id=IDENTITY_USER, issuer=UTC_ISSUER, subject=SUBJECT)
    assert second["token"] != first["token"]
    assert _golden_authenticate(conn, first["token"]) is None
    assert _golden_authenticate(conn, second["token"])["user_id"] == principal

    with DoubleCursor(conn) as cur:
        cur.execute("select count(*) as n from business_tokens where revoked_at is null")
        assert cur.fetchone()["n"] == 1


def test_the_golden_authentication_never_sees_the_c2_test_identity_id(golden_sql):
    """The principal in the token row is a business id, not the test user id."""

    conn, principal = _bridge_database()
    session = golden_session.issue_token(conn, user_id=IDENTITY_USER, issuer=UTC_ISSUER, subject=SUBJECT)

    accepted = _golden_authenticate(conn, session["token"])

    assert accepted["user_id"] == principal
    assert accepted["user_id"] != IDENTITY_USER
    assert count(conn, "business_tokens", "where user_id = ?", (IDENTITY_USER,)) == 0
