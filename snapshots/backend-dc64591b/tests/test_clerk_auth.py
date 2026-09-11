"""Unit tests for :mod:`app.clerk_auth`.

The official SDK is replaced by a fake, so these tests never touch the network
and never need a real Clerk instance. They pin down the properties the fixed
architecture depends on:

* only a ``session_token`` may ever become an identity;
* the SDK request carries an ``Authorization`` header and *nothing* else (so a
  ``__session`` cookie can never be smuggled in);
* the configured issuer and the authorized-party list are always enforced;
* every SDK failure fails closed instead of degrading to "anonymous".
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app import clerk_auth
from app.config import Settings

ISSUER = "https://goaa-c2-auth-test.clerk.accounts.dev"
PARTIES = ("http://127.0.0.1:3102", "http://localhost:13102")


def clerk_settings(**overrides) -> Settings:
    base = dict(
        clerk_auth_enabled=True,
        clerk_issuer=ISSUER,
        clerk_secret_key="sk_test_unit_not_a_real_key",
        clerk_authorized_parties=PARTIES,
    )
    base.update(overrides)
    return Settings(**base)


@dataclass
class _State:
    status: object
    payload: dict | None
    reason: object = None
    token: object = None


class _FakeClerk:
    """Minimal stand-in for ``clerk_backend_api.Clerk``."""

    def __init__(self, state=None, error=None, user=None, user_error=None):
        self._state = state
        self._error = error
        self._user = user
        self._user_error = user_error
        self.requests = []
        self.options = []
        self.lookups = []
        self.users = self

    def authenticate_request(self, request, options):
        self.requests.append(request)
        self.options.append(options)
        if self._error is not None:
            raise self._error
        return self._state

    def get(self, *, user_id: str):
        self.lookups.append(user_id)
        if self._user_error is not None:
            raise self._user_error
        return self._user


@pytest.fixture()
def fake(monkeypatch):
    holder = {}

    def install(**kwargs):
        client = _FakeClerk(**kwargs)
        holder["client"] = client
        monkeypatch.setattr(clerk_auth, "_client", lambda secret: client)
        return client

    return install


def _signed_in(payload: dict) -> _State:
    return _State(status=clerk_auth.AuthStatus.SIGNED_IN, payload=payload)


# ---------------------------------------------------------------------------
# the verifier itself
# ---------------------------------------------------------------------------
def test_missing_authorization_header_is_rejected():
    with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
        clerk_auth.verify_session_token(None, clerk_settings())
    assert excinfo.value.status == 401
    assert excinfo.value.code == "missing_clerk_session"


def test_non_bearer_scheme_is_rejected():
    for header in ("Basic abc", "Bearer", "bearer   ", "Token abc"):
        with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
            clerk_auth.verify_session_token(header, clerk_settings())
        assert excinfo.value.status == 401


def test_unconfigured_service_fails_closed():
    for overrides in (
        {"clerk_secret_key": ""},
        {"clerk_issuer": ""},
        {"clerk_authorized_parties": ()},
    ):
        with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
            clerk_auth.verify_session_token("Bearer abc", clerk_settings(**overrides))
        assert excinfo.value.status == 503
        assert excinfo.value.code == "clerk_not_configured"
        assert not clerk_auth.clerk_configured(clerk_settings(**overrides))


def test_signed_in_session_token_yields_the_issuer_and_subject(fake):
    fake(state=_signed_in({"iss": ISSUER, "sub": "user_2abc", "sid": "sess_1", "sts": "active"}))
    identity = clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    assert identity.issuer == ISSUER
    assert identity.subject == "user_2abc"
    assert identity.session_id == "sess_1"


def test_sdk_request_carries_only_an_authorization_header(fake):
    """A cookie must never be able to reach the token extractor."""
    client = fake(state=_signed_in({"iss": ISSUER, "sub": "user_2abc"}))
    clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    headers = dict(client.requests[0].headers)
    assert list(headers) == ["Authorization"]
    assert headers["Authorization"] == "Bearer fake.jwt.value"


def test_only_session_tokens_are_accepted(fake):
    client = fake(state=_signed_in({"iss": ISSUER, "sub": "user_2abc"}))
    clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    options = client.options[0]
    assert options.accepts_token == [clerk_auth.TokenType.SESSION_TOKEN.value] == ["session_token"]
    assert options.secret_key == "sk_test_unit_not_a_real_key"
    assert options.authorized_parties == list(PARTIES)
    assert options.authorized_parties and "*" not in options.authorized_parties


def test_signed_out_state_is_rejected(fake):
    fake(state=_State(status=clerk_auth.AuthStatus.SIGNED_OUT, payload=None))
    with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
        clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    assert excinfo.value.code == "invalid_clerk_session"


def test_payload_without_a_subject_is_rejected(fake):
    for payload in ({"iss": ISSUER}, {"iss": ISSUER, "sub": ""}, {"iss": ISSUER, "sub": "   "}):
        fake(state=_signed_in(payload))
        with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
            clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
        assert excinfo.value.code in {"invalid_clerk_session"}


def test_token_from_another_instance_is_rejected(fake):
    fake(state=_signed_in({"iss": "https://someone-else.clerk.accounts.dev", "sub": "user_2abc"}))
    with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
        clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    assert excinfo.value.code == "invalid_clerk_issuer"


def test_payload_without_an_issuer_is_rejected(fake):
    fake(state=_signed_in({"sub": "user_2abc"}))
    with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
        clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    assert excinfo.value.code == "invalid_clerk_session"


@pytest.mark.parametrize("state", ["pending", "revoked", "ended", "expired"])
def test_inactive_session_states_are_rejected(fake, state):
    fake(state=_signed_in({"iss": ISSUER, "sub": "user_2abc", "sts": state}))
    with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
        clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    assert excinfo.value.code == "clerk_session_not_active"


def test_sdk_failure_fails_closed(fake):
    fake(error=RuntimeError("jwks unreachable"))
    with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
        clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    assert excinfo.value.status == 401
    assert excinfo.value.code == "clerk_verification_unavailable"
    assert "jwks" not in excinfo.value.message


def test_missing_sdk_fails_closed(monkeypatch):
    monkeypatch.setattr(clerk_auth, "CLERK_SDK_AVAILABLE", False)
    with pytest.raises(clerk_auth.ClerkAuthError) as excinfo:
        clerk_auth.verify_session_token("Bearer fake.jwt.value", clerk_settings())
    assert excinfo.value.status == 503
    assert excinfo.value.code == "clerk_sdk_unavailable"


# ---------------------------------------------------------------------------
# e-mail snapshot (server-to-server only)
# ---------------------------------------------------------------------------
@dataclass
class _Verification:
    status: str


@dataclass
class _Address:
    id: str
    email_address: str
    verification: _Verification


@dataclass
class _User:
    primary_email_address_id: str | None
    email_addresses: list


def test_verified_primary_email_is_lowercased(fake):
    client = fake(
        user=_User(
            primary_email_address_id="idn_1",
            email_addresses=[
                _Address("idn_2", "other@example.test", _Verification("verified")),
                _Address("idn_1", "Applicant@Example.Test", _Verification("verified")),
            ],
        )
    )
    assert clerk_auth.verified_primary_email(clerk_settings(), "user_2abc") == "applicant@example.test"
    assert client.lookups == ["user_2abc"]


def test_unverified_primary_email_is_ignored(fake):
    fake(
        user=_User(
            primary_email_address_id="idn_1",
            email_addresses=[_Address("idn_1", "applicant@example.test", _Verification("unverified"))],
        )
    )
    assert clerk_auth.verified_primary_email(clerk_settings(), "user_2abc") is None


def test_email_lookup_failure_never_raises(fake):
    fake(user_error=RuntimeError("backend api down"))
    assert clerk_auth.verified_primary_email(clerk_settings(), "user_2abc") is None


def test_email_lookup_without_a_secret_is_skipped(fake):
    client = fake(user=_User(primary_email_address_id=None, email_addresses=[]))
    assert clerk_auth.verified_primary_email(clerk_settings(clerk_secret_key=""), "user_2abc") is None
    assert client.lookups == []
