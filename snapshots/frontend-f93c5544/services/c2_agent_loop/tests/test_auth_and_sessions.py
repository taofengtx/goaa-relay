"""Authentication, session and capability-reporting behaviour."""

from __future__ import annotations

import uuid

from conftest import COOKIE_NAME, app_sql, bearer, login, register

BASE = "/api/v1/agent-loop"


def _email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.test"


def test_health_reports_honest_capabilities(client):
    response = client.get(f"{BASE}/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["production_ready"] is False
    assert body["production_resources_used"] is False
    assert body["capabilities"] == {
        "storage_mode": "c2-local-private",
        "scanner_mode": "stub",
        "ocr_mode": "rules-only",
        "email_delivery": "disabled",
    }
    assert body["database"]["name"] == "goaa_c2test"
    assert body["database"]["port"] == 5433
    assert body["database"]["server_port"] == 5433
    assert body["database"]["server_addr"] == "127.0.0.1"


def test_register_never_returns_credentials(client):
    email = _email("reg")
    response = register(client, email, full_name="Test Applicant")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["email"] == email
    assert body["user"]["roles"] == ["user"]
    text = response.text
    assert "correct-horse-battery" not in text
    assert "$2b$" not in text
    assert "password_hash" not in text

    password_hash = app_sql(f"select password_hash from users where email = '{email}'")
    assert password_hash.startswith("$2"), "the password must be stored as a bcrypt hash"
    assert "correct-horse-battery" not in password_hash


def test_registration_rejects_duplicate_email_ignoring_case(client):
    email = _email("dup")
    assert register(client, email).status_code == 201
    again = register(client, email.upper())
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "email_in_use"


def test_registration_rejects_weak_password_and_bad_email(client):
    assert register(client, _email("weak"), password="short").status_code == 422
    assert register(client, "not-an-email").status_code == 422


def test_login_and_session_lifecycle(client):
    email = _email("sess")
    register(client, email)
    token = login(client, email)
    assert client.cookies.get(COOKIE_NAME)

    me = client.get(f"{BASE}/auth/me", headers=bearer(token))
    assert me.status_code == 200
    assert me.json()["user"]["email"] == email

    client.cookies.clear()  # from here on the caller presents no credentials
    assert client.get(f"{BASE}/auth/me").status_code == 401
    assert client.get(f"{BASE}/auth/me", headers=bearer("not-a-token")).status_code == 401

    assert client.post(f"{BASE}/auth/logout", headers=bearer(token)).status_code == 200
    assert client.get(f"{BASE}/auth/me", headers=bearer(token)).status_code == 401


def test_wrong_password_is_rejected(client):
    email = _email("wrongpw")
    register(client, email)
    response = client.post(f"{BASE}/auth/login", json={"email": email, "password": "definitely-not-it"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_unknown_account_is_rejected_without_disclosure(client):
    response = client.post(
        f"{BASE}/auth/login", json={"email": "nobody@example.test", "password": "whatever-1234"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_bearer_token_takes_priority_over_an_ambient_cookie(client):
    email = _email("prio")
    register(client, email)
    token = login(client, email)

    # a stale/forged cookie must never silently authenticate the request
    client.cookies.set(COOKIE_NAME, "forged.cookie")
    assert client.get(f"{BASE}/auth/me").status_code == 401
    ok = client.get(f"{BASE}/auth/me", headers=bearer(token))
    assert ok.status_code == 200
    assert ok.json()["user"]["email"] == email


def test_session_tokens_are_not_stored_in_plaintext(client):
    email = _email("hash")
    register(client, email)
    token = login(client, email)
    count = app_sql(f"select count(*) from user_sessions where token_hash = '{token}'")
    assert count == "0", "the raw session token must never be stored"
    stored = app_sql(f"select count(*) from user_sessions where token_hash = "
                     f"encode(sha256('{token}'::bytea), 'hex')")
    assert stored == "1", "the SHA-256 fingerprint of the token is what gets persisted"


def test_anonymous_callers_cannot_reach_agent_or_admin_surfaces(client):
    assert client.get(f"{BASE}/agent/panel").status_code == 401
    assert client.get(f"{BASE}/admin/applications").status_code == 401


def test_non_admin_cannot_reach_admin_surfaces(client):
    email = _email("plain")
    register(client, email)
    token = login(client, email)
    response = client.get(f"{BASE}/admin/applications", headers=bearer(token))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_required"
