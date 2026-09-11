"""Golden (AI Butler) business-session bridge — lifecycle tests, DB-free.

What these tests can and cannot prove (stated up front):

  * They run under the pre-import guard that refuses ``psycopg.connect`` and
    every socket path, so a run that touched a database or the network fails
    loudly. The runner reports the count of blocked attempts.
  * The lifecycle runs against a **SQLite double** that mirrors the unique
    constraints, CHECK lists, append-only trigger and one-to-one links of
    migrations 0005/0006. It is not PostgreSQL: it proves the logic, not the
    server. Applying 0006 and re-running against the real cluster is an
    operator step listed in the delivery notes.
  * The HTTP tests use the real FastAPI app with the real dependency chain and
    assert that no business session is minted without a verified Clerk
    identity. Clerk cannot be reached from here, so those calls must fail
    closed — which is exactly the property under test.
  * Compatibility with the *golden* authentication function is a separate file:
    ``test_golden_business_contract.py`` runs the golden SQL itself.
"""

from __future__ import annotations

import asyncio
import pathlib
from datetime import datetime, timedelta, timezone

import pytest

from app import golden_session
from app.config import Settings
from app.main import create_app
from support.sqlite_double import DoubleCursor, connect, count, seed_identity

UTC = timezone.utc
ISSUER = "https://lenient-phoenix-9847.clerk.accounts.dev"
T0 = datetime(2026, 9, 11, 1, 31, 1, tzinfo=UTC)
USER_A = "9606620b-61a5-4a35-92ed-b9fce61500c2"
USER_B = "67b44655-b5a0-4f97-ae9f-5242b4d3121f"
SUBJECT_A = "user_3JA2UKSDA9PB4BiLlf14HnAKiED"
SUBJECT_B = "user_3JA5Mlb7xYq0U3CyThTWNhwwSFn"
APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"


def database_with_two_identities(email_a: str | None = "shared@example.com",
                                 email_b: str | None = None):
    """Two distinct Clerk subjects; the second one has no verified address.

    A shared address cannot even be represented here: ``users_email_lower_key``
    refuses two rows with the same address, which is why an address clash is
    handled *upstream* by ``clerk_identity`` (fail closed) and never reaches
    this bridge. What matters here is that the bridge would not join on an
    address even if one were passed to it.
    """

    conn = connect()
    seed_identity(conn, user_id=USER_A, subject=SUBJECT_A, issuer=ISSUER, email=email_a)
    seed_identity(conn, user_id=USER_B, subject=SUBJECT_B, issuer=ISSUER, email=email_b)
    return conn


def link(conn, user_id=USER_A, subject=SUBJECT_A, email="someone@example.com"):
    return golden_session.ensure_subject(
        conn, user_id=user_id, issuer=ISSUER, subject=subject, email=email, now=T0
    )


def issue(conn, user_id=USER_A, subject=SUBJECT_A, now=T0):
    return golden_session.issue_token(
        conn, user_id=user_id, issuer=ISSUER, subject=subject, now=now
    )


# ---------------------------------------------------------------------------
# linking: the identity -> business-principal binding
# ---------------------------------------------------------------------------
def test_linking_creates_one_principal_and_is_idempotent():
    conn = database_with_two_identities()

    first = link(conn)
    again = link(conn)

    assert first["created"] is True
    assert again["created"] is False
    assert first["user_id"] == again["user_id"]
    assert count(conn, "business_subjects") == 1
    assert count(conn, "business_subject_links") == 1
    assert count(conn, "identity_events", "where event_type = 'business.subject_linked'") == 1


def test_two_identities_never_share_one_business_principal():
    conn = database_with_two_identities()

    a = link(conn, user_id=USER_A, subject=SUBJECT_A)
    b = link(conn, user_id=USER_B, subject=SUBJECT_B)

    assert a["user_id"] != b["user_id"]
    assert count(conn, "business_subjects") == 2


def test_the_link_is_one_to_one_in_both_directions():
    conn = database_with_two_identities()
    principal = link(conn)["user_id"]

    # one principal cannot be linked twice (subject_id is UNIQUE)
    with pytest.raises(Exception):
        with DoubleCursor(conn) as cur:
            cur.execute(
                "insert into business_subject_links "
                "(user_id, subject_id, linked_via, issuer, subject, created_at) "
                "values (?, ?, 'clerk_issuer_subject', ?, ?, ?)",
                (USER_B, principal, ISSUER, SUBJECT_B, T0),
            )

    # one identity cannot own two principals (user_id is the PRIMARY KEY)
    with DoubleCursor(conn) as cur:
        cur.execute(
            "insert into business_subjects (id, kind) values (?, 'customer')",
            ("11111111-1111-1111-1111-111111111111",),
        )
    with pytest.raises(Exception):
        with DoubleCursor(conn) as cur:
            cur.execute(
                "insert into business_subject_links "
                "(user_id, subject_id, linked_via, issuer, subject, created_at) "
                "values (?, ?, 'clerk_issuer_subject', ?, ?, ?)",
                (USER_A, "11111111-1111-1111-1111-111111111111", ISSUER, SUBJECT_A, T0),
            )


def test_the_identity_id_is_never_the_business_id():
    """The C2 *test* identity table must not leak into the business identity."""

    conn = database_with_two_identities()
    principal = link(conn)["user_id"]

    assert principal != USER_A
    assert principal != USER_B
    with DoubleCursor(conn) as cur:
        cur.execute("select id from users")
        assert principal not in {row["id"] for row in cur.fetchall()}


def test_an_address_is_never_an_input_to_ownership():
    """Two identities may never be fused by an address, and none is stored."""

    conn = database_with_two_identities(email_a="shared@example.com", email_b=None)
    a = link(conn, user_id=USER_A, subject=SUBJECT_A, email="shared@example.com")
    b = link(conn, user_id=USER_B, subject=SUBJECT_B, email="shared@example.com")

    assert a["user_id"] != b["user_id"]
    with DoubleCursor(conn) as cur:
        cur.execute("select count(*) as n from business_subject_links where issuer is null or subject is null")
        assert cur.fetchone()["n"] == 0
    # no column anywhere in the bridge decides ownership by address
    links_ddl = (APP_DIR / "golden_session.py").read_text()
    assert "email_snapshot" not in links_ddl


# ---------------------------------------------------------------------------
# issuing and using
# ---------------------------------------------------------------------------
def test_login_issues_exactly_one_live_opaque_token():
    conn = database_with_two_identities()
    principal = link(conn)["user_id"]

    session = issue(conn)

    assert session["user_id"] == principal
    assert session["role"] == "customer"
    assert golden_session.looks_like_token(session["token"])
    assert golden_session.live_token_count(conn, principal) == 1
    assert count(conn, "business_tokens") == 1


def test_the_row_stores_the_value_the_caller_presents():
    """The golden mechanism stores the token itself, and so does this bridge."""

    conn = database_with_two_identities()
    link(conn)
    session = issue(conn)

    with DoubleCursor(conn) as cur:
        cur.execute("select token, role from business_tokens")
        rows = cur.fetchall()

    assert [row["token"] for row in rows] == [session["token"]]
    assert rows[0]["role"] == "customer"


def test_the_token_value_is_never_read_back_out_of_the_database():
    """Metadata helpers return no credential, so nothing can leak it later."""

    conn = database_with_two_identities()
    principal = link(conn)["user_id"]
    session = issue(conn)

    live = golden_session.list_live_tokens(conn, principal)

    assert len(live) == 1
    assert session["token"] not in repr(live)


def test_refresh_re_presents_the_same_token_and_changes_nothing():
    conn = database_with_two_identities()
    principal = link(conn)["user_id"]
    session = issue(conn)

    with DoubleCursor(conn) as cur:
        cur.execute("select id, revoked_at from business_tokens")
        before = cur.fetchall()

    for _ in range(3):
        again = golden_session.authenticate_token(conn, session["token"], now=T0 + timedelta(seconds=30))
        assert again["user_id"] == principal
        assert again["role"] == "customer"

    with DoubleCursor(conn) as cur:
        cur.execute("select id, revoked_at from business_tokens")
        after = cur.fetchall()

    assert before == after
    assert golden_session.live_token_count(conn, principal) == 1


def test_a_second_login_rotates_and_the_previous_token_stops_working():
    conn = database_with_two_identities()
    principal = link(conn)["user_id"]

    first = issue(conn)
    second = issue(conn, now=T0 + timedelta(seconds=31))

    assert first["token"] != second["token"]
    assert golden_session.live_token_count(conn, principal) == 1
    with pytest.raises(golden_session.BusinessTokenInvalid) as excinfo:
        golden_session.authenticate_token(conn, first["token"])
    assert excinfo.value.reason == golden_session.REASON_REVOKED
    assert golden_session.authenticate_token(conn, second["token"])["user_id"] == principal


# ---------------------------------------------------------------------------
# sign-out
# ---------------------------------------------------------------------------
def test_sign_out_revokes_the_live_token_and_is_audited():
    conn = database_with_two_identities()
    principal = link(conn)["user_id"]
    session = issue(conn)

    revoked = golden_session.revoke_all(
        conn, user_id=USER_A, issuer=ISSUER, subject=SUBJECT_A, email="someone@example.com"
    )

    assert revoked == 1
    assert golden_session.live_token_count(conn, principal) == 0
    with pytest.raises(golden_session.BusinessTokenInvalid) as excinfo:
        golden_session.authenticate_token(conn, session["token"])
    assert excinfo.value.reason == golden_session.REASON_REVOKED
    assert count(conn, "identity_events", "where event_type = 'business.token_revoked'") == 1


def test_sign_out_after_clerk_is_gone_still_revokes_using_the_token_itself():
    """The out-of-order sign-out: no Clerk session left, token still presented.

    Without this path a credential captured before a sign-out would survive it,
    which is exactly the overlap the bridge must not allow.
    """

    conn = database_with_two_identities()
    link(conn)
    session = issue(conn)

    resolved = golden_session.authenticate_token(conn, session["token"], now=T0)
    revoked = golden_session.revoke_subject(conn, subject_id=resolved["user_id"], reason="sign_out")

    assert revoked == 1
    assert golden_session.live_token_count(conn, resolved["user_id"]) == 0
    with pytest.raises(golden_session.BusinessTokenInvalid) as excinfo:
        golden_session.authenticate_token(conn, session["token"])
    assert excinfo.value.reason == golden_session.REASON_REVOKED

    # idempotent: a retry after the first success revokes nothing further
    assert golden_session.revoke_subject(conn, subject_id=resolved["user_id"], reason="sign_out") == 0


def test_sign_out_of_one_identity_leaves_the_other_alone():
    conn = database_with_two_identities()
    a = link(conn, user_id=USER_A, subject=SUBJECT_A)
    b = link(conn, user_id=USER_B, subject=SUBJECT_B)
    token_a = issue(conn, user_id=USER_A, subject=SUBJECT_A)["token"]
    token_b = issue(conn, user_id=USER_B, subject=SUBJECT_B)["token"]

    golden_session.revoke_all(conn, user_id=USER_A, issuer=ISSUER, subject=SUBJECT_A)

    with pytest.raises(golden_session.BusinessTokenInvalid):
        golden_session.authenticate_token(conn, token_a)
    assert golden_session.authenticate_token(conn, token_b)["user_id"] == b["user_id"]
    assert golden_session.live_token_count(conn, a["user_id"]) == 0
    assert golden_session.live_token_count(conn, b["user_id"]) == 1


# ---------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------
def test_an_unknown_token_is_refused():
    conn = database_with_two_identities()
    link(conn)
    issue(conn)

    with pytest.raises(golden_session.BusinessTokenInvalid) as excinfo:
        golden_session.authenticate_token(conn, golden_session.new_token())
    assert excinfo.value.reason == golden_session.REASON_UNKNOWN


def test_a_malformed_credential_is_refused_without_any_lookup():
    for value in ("forged", "Bearer", "", "   ", "0" * 31, "0" * 33, "Z" * 32, "not/a/token!"):
        assert golden_session.looks_like_token(value) is False
    assert golden_session.looks_like_token(golden_session.new_token()) is True
    # a well-formed value is only refused by the row lookup, never by the shape
    conn = database_with_two_identities()
    link(conn)
    with pytest.raises(golden_session.BusinessTokenInvalid):
        golden_session.authenticate_token(conn, "f" * 32)


def test_a_rejection_can_be_audited_without_storing_the_credential():
    conn = database_with_two_identities()
    presented = golden_session.new_token()

    golden_session.record_rejection(conn, token=presented, reason=golden_session.REASON_UNKNOWN)

    with DoubleCursor(conn) as cur:
        cur.execute("select detail, email_masked from identity_events")
        row = cur.fetchone()
    assert row["email_masked"] is None
    assert presented not in repr(row["detail"])


def test_issuing_without_a_linked_principal_is_refused():
    conn = database_with_two_identities()
    with pytest.raises(golden_session.BusinessSessionError):
        issue(conn)
    assert count(conn, "business_tokens") == 0


# ---------------------------------------------------------------------------
# the audit stream keeps its append-only guarantee
# ---------------------------------------------------------------------------
def test_the_audit_stream_stays_append_only():
    conn = database_with_two_identities()
    link(conn)
    issue(conn)

    with pytest.raises(Exception):
        with DoubleCursor(conn) as cur:
            cur.execute("update identity_events set detail = '{}' where id is not null")

    with pytest.raises(Exception):
        with DoubleCursor(conn) as cur:
            cur.execute("delete from identity_events")


def test_only_customer_tokens_can_be_stored():
    conn = database_with_two_identities()
    principal = link(conn)["user_id"]

    with pytest.raises(Exception):
        with DoubleCursor(conn) as cur:
            cur.execute(
                "insert into business_tokens (user_id, token, role, issued_at) values (?, ?, 'agent', ?)",
                (principal, "a" * 32, T0),
            )
    assert count(conn, "business_tokens") == 0


# ---------------------------------------------------------------------------
# HTTP surface: nothing is minted without a verified Clerk identity
# ---------------------------------------------------------------------------
def _clerk_settings() -> Settings:
    return Settings(
        environment="c2-test",
        db_name="goaa_c2test",
        clerk_auth_enabled=True,
        clerk_issuer=ISSUER,
        clerk_secret_key="sk_test_not-a-real-key",
        clerk_authorized_parties=("http://localhost:13102",),
    )


def call_app(app, method: str, path: str, headers: dict[str, str] | None = None):
    """Invoke the real ASGI app in-process.

    ``httpx``'s test client cannot be used here: the guard blocks every HTTP
    client, which is the point of the run. Building the ASGI scope by hand
    exercises the same app, dependencies, middleware and error handler without
    opening any client.
    """

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": ("127.0.0.1", 44100),
        "server": ("127.0.0.1", 3102),
    }
    messages: list[dict] = []
    body = {"type": "http.request", "body": b"", "more_body": False}

    async def receive():
        return body

    async def send(message):
        messages.append(message)

    asyncio.run(app(scope, receive, send))

    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, payload.decode()


@pytest.mark.parametrize("method", ["get", "post"])
def test_no_business_session_is_minted_without_a_verified_clerk_identity(method):
    app = create_app(_clerk_settings())
    path = "/api/v1/agent-loop/golden/session"

    status, body = call_app(app, method, path)
    assert status in (401, 503), body
    assert "token" not in body

    status, body = call_app(app, method, path, {"authorization": "Bearer forged-token"})
    assert status in (401, 503), body
    assert "token" not in body


def test_verify_refuses_an_unproven_business_credential_before_any_lookup():
    """`verify` resolves the *business* token and holds no other credential.

    Only shapes that cannot be one of ours are exercised here: a well-formed
    but unknown token is refused by the row lookup, which needs a database and
    is covered against the SQLite double instead.
    """

    app = create_app(_clerk_settings())
    path = "/api/v1/agent-loop/golden/session/verify"

    status, body = call_app(app, "get", path)
    assert status in (401, 503), body

    for forged in ("forged", "Bearer", "customer", "0" * 31, "0" * 33):
        status, body = call_app(app, "get", path, {"authorization": f"Bearer {forged}"})
        assert status in (401, 503), body
        assert "customer" not in body
        assert "user_id" not in body


def test_revoke_also_requires_a_verifiable_credential():
    app = create_app(_clerk_settings())

    status, body = call_app(
        app, "post", "/api/v1/agent-loop/golden/session/revoke", {"authorization": "Bearer forged"}
    )
    assert status in (401, 503), body
    assert "revoked" not in body

    # the shape guard runs before any lookup, so a malformed credential cannot
    # reach the database even through the token-based sign-out path
    status, body = call_app(app, "post", "/api/v1/agent-loop/golden/session/revoke")
    assert status in (401, 503), body


def test_every_golden_route_refuses_when_clerk_is_not_the_identity_authority():
    """No business session exists while Clerk is not the identity authority.

    Two halves, both DB-free by construction:
      * the credential-free routes (`verify`, `revoke`) refuse with
        `clerk_auth_disabled` — they refuse before reading anything;
      * the identity-bridge routes refuse through the ordinary dependency
        chain, so a caller with no proof at all gets 401 and nothing is minted.

    What this deliberately does *not* claim: that a legacy session cookie is
    rejected. That comparison needs the database, and the point being pinned
    here is weaker and checkable — nothing is issued without a verified Clerk
    identity.
    """

    legacy = Settings(environment="c2-test", db_name="goaa_c2test")
    assert legacy.clerk_auth_enabled is False
    app = create_app(legacy)

    for method, path in (
        ("get", "/api/v1/agent-loop/golden/session/verify"),
        ("post", "/api/v1/agent-loop/golden/session/revoke"),
    ):
        status, body = call_app(app, method, path)
        assert status == 409, f"{method} {path}: {status} {body}"
        assert "clerk_auth_disabled" in body

    for method, path in (
        ("get", "/api/v1/agent-loop/golden/session"),
        ("post", "/api/v1/agent-loop/golden/session"),
    ):
        status, body = call_app(app, method, path)
        assert status == 401, f"{method} {path}: {status} {body}"
        assert "token" not in body
