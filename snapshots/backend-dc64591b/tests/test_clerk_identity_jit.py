"""Mapping tests: a verified Clerk subject becomes exactly one local user.

These run against the real ``goaa_c2test`` schema (the session fixture rebuilds
it from the migration files) but never against a real Clerk instance: the
verifier is monkeypatched where the HTTP surface is exercised.

NOT EXECUTED so far: they are database-backed, and the repository's
``conftest.py`` rebuilds ``schema public`` through a session-scoped autouse
fixture. They are updated here to the current contract — a verified address is
never an identity key, and an address owned by another account refuses the
log-in instead of being dropped — and must be run deliberately, with a backup
taken first.
"""

from __future__ import annotations

import pytest

from app import clerk_auth, clerk_identity
from app.db import connection, fetch_all, fetch_one
from tests.conftest import app_settings

ISSUER = "https://goaa-c2-auth-test.clerk.accounts.dev"
OTHER_ISSUER = "https://some-other-instance.clerk.accounts.dev"


def _provider(email):
    """The verified-address callback the API layer hands to the resolver.

    ``None`` stands for "no verified primary address could be read".
    """
    return (lambda: email) if email is not None else None


def _resolve(settings, subject, issuer=ISSUER, email=None):
    return clerk_identity.resolve_clerk_user(
        settings, issuer=issuer, subject=subject, email_provider=_provider(email)
    )


def _one(settings, sql, params=()):
    with connection(settings) as conn:
        return fetch_one(conn, sql, params)


def _all(settings, sql, params=()):
    with connection(settings) as conn:
        return fetch_all(conn, sql, params)


# ---------------------------------------------------------------------------
# just-in-time provisioning
# ---------------------------------------------------------------------------
def test_first_login_creates_a_credential_less_user_with_the_default_role(settings):
    user = _resolve(settings, "user_first_login")

    assert user["roles"] == [clerk_identity.DEFAULT_ROLE]
    assert user["email"] is None
    assert user["email_verified_at"] is None

    row = _one(
        settings,
        "select u.password_hash, i.provider, i.issuer, i.subject, i.email_verified "
        "from users u join user_identities i on i.user_id = u.id where i.subject = %s",
        ("user_first_login",),
    )
    assert row["password_hash"] is None
    assert row["provider"] == "clerk"
    assert row["issuer"] == ISSUER
    assert row["email_verified"] is False


def test_the_same_subject_reuses_the_same_user(settings):
    first = _resolve(settings, "user_repeat_login")
    second = _resolve(settings, "user_repeat_login")
    assert first["user_id"] == second["user_id"]
    assert _one(settings, "select count(*) as n from users where id = %s", (first["user_id"],))["n"] == 1



def test_two_subjects_sharing_an_address_never_share_an_account(settings):
    """The first subject may hold the address; the second is refused, not merged."""
    one = _resolve(settings, "user_subject_one", email="clerk-jit-shared@example.test")
    assert one["email"] == "clerk-jit-shared@example.test"

    with pytest.raises(clerk_identity.IdentityConflict):
        _resolve(settings, "user_subject_two", email="clerk-jit-shared@example.test")

    assert _one(
        settings, "select count(*) as n from user_identities where subject = %s", ("user_subject_two",)
    )["n"] == 0


def test_the_same_subject_under_another_issuer_is_a_different_user(settings):
    here = _resolve(settings, "user_shared_subject", issuer=ISSUER)
    there = _resolve(settings, "user_shared_subject", issuer=OTHER_ISSUER)
    assert here["user_id"] != there["user_id"]


def test_a_verified_email_is_snapshotted(settings):
    user = _resolve(settings, "user_with_email", email="Applicant@Example.Test")
    assert user["email"] == "Applicant@Example.Test"

    row = _one(
        settings,
        "select email_snapshot, email_verified from user_identities where subject = %s",
        ("user_with_email",),
    )
    assert row["email_verified"] is True
    assert row["email_snapshot"] == "Applicant@Example.Test"



def test_a_missing_verified_address_is_never_stored(settings):
    """When no verified address can be read, the column simply stays NULL."""
    user = _resolve(settings, "user_unverified_email")
    assert user["email"] is None
    row = _one(
        settings,
        "select email_snapshot, email_verified from user_identities where subject = %s",
        ("user_unverified_email",),
    )
    assert row["email_snapshot"] is None
    assert row["email_verified"] is False


def test_creation_is_recorded_as_an_append_only_event(settings):
    user = _resolve(settings, "user_audited")
    rows = _all(
        settings,
        "select event_type, subject_user_id, provider from identity_events where subject = %s",
        ("user_audited",),
    )
    assert [row["event_type"] for row in rows] == ["identity.jit_create"]
    assert str(rows[0]["subject_user_id"]) == user["user_id"]
    assert rows[0]["provider"] == "clerk"



def test_a_verified_email_owned_by_another_account_refuses_the_login(settings):
    """A shared address never adopts an account — and never creates a second one."""
    with connection(settings) as conn:
        existing = fetch_one(
            conn,
            "insert into users (email) values (%s) returning id",
            ("owned@example.test",),
        )

    with pytest.raises(clerk_identity.IdentityConflict):
        _resolve(settings, "user_email_clash", email="Owned@Example.Test")

    # nothing was created: no adopted account, no merged account, and no
    # NULL-address fallback account either
    assert _one(
        settings, "select count(*) as n from user_identities where subject = %s", ("user_email_clash",)
    )["n"] == 0
    # the pre-existing account keeps its address and gains nothing
    assert _one(settings, "select email from users where id = %s", (str(existing["id"]),))["email"] == (
        "owned@example.test"
    )
    # and the refusal is on the record, with a masked address
    rows = _all(
        settings,
        "select event_type, detail, email_masked from identity_events where subject = %s "
        "order by occurred_at",
        ("user_email_clash",),
    )
    assert [row["event_type"] for row in rows] == ["identity.conflict"]
    assert rows[0]["email_masked"] != "owned@example.test"
    assert "users_email_lower_key" in rows[0]["detail"]["reason"]


def test_blank_subjects_are_refused(settings):
    for subject in ("", "   "):
        with pytest.raises(clerk_identity.IdentityError):
            _resolve(settings, subject)


# ---------------------------------------------------------------------------
# HTTP surface: the BFF is not trusted, roles come from the local database
# ---------------------------------------------------------------------------
@pytest.fixture()
def clerk_client(private_files_dir, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import create_app

    settings = app_settings(
        private_files_dir,
        clerk_auth_enabled=True,
        clerk_issuer=ISSUER,
        clerk_secret_key="sk_test_unit_not_a_real_key",
        clerk_authorized_parties=("http://127.0.0.1:3102",),
    )
    monkeypatch.setattr(clerk_auth, "verified_primary_email", lambda cfg, subject: None)

    def verify(authorization, cfg):
        if not authorization or not authorization.lower().startswith("bearer "):
            raise clerk_auth.ClerkAuthError("missing_clerk_session", "a sign-in is required")
        return clerk_auth.ClerkIdentity(
            issuer=ISSUER,
            subject=authorization.split(" ", 1)[1],
            session_id="sess",
            session_status="active",
        )

    monkeypatch.setattr(clerk_auth, "verify_session_token", verify)

    with TestClient(create_app(settings)) as test_client:
        yield test_client, settings


def test_http_clerk_login_creates_and_returns_the_local_user(clerk_client, api_base):
    client, _ = clerk_client
    response = client.get(f"{api_base}/auth/me", headers={"Authorization": "Bearer user_http_first"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"]["roles"] == [clerk_identity.DEFAULT_ROLE]
    assert body["user"]["email"] is None


def test_http_second_call_returns_the_same_user(clerk_client, api_base):
    client, _ = clerk_client
    headers = {"Authorization": "Bearer user_http_repeat"}
    first = client.get(f"{api_base}/auth/me", headers=headers).json()
    second = client.get(f"{api_base}/auth/me", headers=headers).json()
    assert first["user"]["id"] == second["user"]["id"]


def test_http_without_a_token_is_401(clerk_client, api_base):
    client, _ = clerk_client
    response = client.get(f"{api_base}/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_clerk_session"


def test_http_legacy_session_cookie_is_not_clerk_proof(clerk_client, api_base):
    client, settings = clerk_client
    client.cookies.set(settings.session_cookie_name, "legacy-token-value")
    response = client.get(f"{api_base}/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_clerk_session"


def test_http_never_issues_a_cookie(clerk_client, api_base):
    client, settings = clerk_client
    response = client.get(f"{api_base}/auth/me", headers={"Authorization": "Bearer user_http_cookie"})
    assert settings.session_cookie_name not in response.cookies
    assert "set-cookie" not in {key.lower() for key in response.headers}


def test_http_roles_come_from_the_local_database(clerk_client, api_base):
    client, _ = clerk_client
    headers = {"Authorization": "Bearer user_http_roles"}
    # a fresh Clerk identity is not an agent, whatever the client claims
    assert client.get(f"{api_base}/agent/panel", headers=headers).status_code == 403
    assert (
        client.get(
            f"{api_base}/agent/panel",
            headers={**headers, "X-Goaa-Role": "agent", "X-Goaa-Internal-Token": "agent"},
        ).status_code
        == 403
    )


def test_http_client_supplied_identity_fields_are_ignored(clerk_client, api_base):
    client, settings = clerk_client
    headers = {
        "Authorization": "Bearer user_http_forged",
        "Content-Type": "application/json",
        "X-Goaa-Email": "admin@example.test",
        "X-Goaa-User-Id": "00000000-0000-0000-0000-000000000000",
        "X-Goaa-Role": "admin",
    }
    response = client.put(
        f"{api_base}/applications/me",
        headers=headers,
        json={"full_name": "Someone", "phone": "+15550100", "address": "1 Test Way", "email": None},
    )
    assert response.status_code in {200, 201, 422}, response.text

    row = _one(
        settings,
        "select i.email_snapshot, i.subject from user_identities i where i.subject = %s",
        ("user_http_forged",),
    )
    assert row["subject"] == "user_http_forged"
    assert row["email_snapshot"] is None
    user_id = _one(
        settings, "select user_id from user_identities where subject = %s", ("user_http_forged",)
    )["user_id"]
    assert _one(
        settings,
        "select count(*) as n from user_roles where user_id = %s and role in ('admin', 'agent')",
        (user_id,),
    )["n"] == 0
