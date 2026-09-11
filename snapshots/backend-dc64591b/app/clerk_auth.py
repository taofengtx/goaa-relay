"""Clerk session-token verification (official ``clerk-backend-api`` SDK only).

The service never signs, decrypts or hand-rolls JWT verification. It hands the
token to the official ``clerk-backend-api`` package and only looks at the
resulting ``RequestState``.

Two properties matter and are enforced here, not by the caller:

* **Session tokens only.** ``accepts_token=[TokenType.SESSION_TOKEN.value]``
  plus an SDK request that carries *only* an ``Authorization`` header (never a
  ``Cookie`` header) means a machine token, an OAuth token or a ``__session``
  cookie can never be turned into an identity.
* **Fail closed.** Any SDK/network/JWKS failure, a missing ``iss``/``sub``, an
  issuer that is not the configured Clerk instance, or a non-active session
  state raises instead of returning "no user", so callers cannot accidentally
  treat a broken verifier as an anonymous request.

The BFF in front of this service is *not* trusted: it only relays the browser's
Clerk session token. Every identity fact used below is re-derived from the
token payload and from the Clerk Backend API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

from .config import Settings

logger = logging.getLogger("goaa.c2.loop.clerk")

# The official SDK is a pinned dependency (``clerk-backend-api`` in
# ``requirements.txt``). It is imported defensively so that a host which has
# not been provisioned yet still *starts*, and then fails closed with a clear
# 503 the moment a Clerk token actually has to be verified — rather than
# importing fine and quietly accepting anything.
try:  # pragma: no cover - exercised by the "SDK missing" test path
    from clerk_backend_api import Clerk
    from clerk_backend_api.security.types import (
        AuthenticateRequestOptions,
        AuthStatus,
        TokenType,
    )

    CLERK_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover
    Clerk = None  # type: ignore[assignment]
    AuthenticateRequestOptions = None  # type: ignore[assignment]
    AuthStatus = None  # type: ignore[assignment]
    TokenType = None  # type: ignore[assignment]
    CLERK_SDK_AVAILABLE = False

#: Clerk session states that must never be accepted as a usable session.
_UNUSABLE_SESSION_STATES = frozenset({"pending", "revoked", "ended", "expired"})


class ClerkAuthError(Exception):
    """A Clerk session token that must not be trusted, with an HTTP mapping."""

    def __init__(self, code: str, message: str, *, status: int = 401) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class _SdkRequest:
    """The only request shape the official SDK reads (``Requestish.headers``)."""

    headers: Mapping[str, str]


@dataclass(frozen=True)
class ClerkIdentity:
    """The verified facts we are willing to take from a Clerk session token."""

    issuer: str
    subject: str
    session_id: str | None
    session_status: str | None


def clerk_configured(settings: Settings) -> bool:
    """True when every value needed to verify a Clerk token is present."""

    return bool(
        settings.clerk_secret_key
        and settings.clerk_issuer
        and settings.clerk_authorized_parties
    )


@lru_cache(maxsize=4)
def _client(secret_key: str) -> "Clerk":
    # The secret never leaves the process: it is used as the SDK's bearer
    # credential and is never logged, returned or echoed.
    return Clerk(bearer_auth=secret_key)


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise ClerkAuthError("missing_clerk_session", "a sign-in is required")
    scheme, _, value = authorization.partition(" ")
    token = value.strip()
    if scheme.lower() != "bearer" or not token:
        raise ClerkAuthError(
            "invalid_authorization_scheme", "the Authorization header must use the Bearer scheme"
        )
    return token


def verify_session_token(authorization: str | None, settings: Settings) -> ClerkIdentity:
    """Verify an ``Authorization: Bearer <clerk session token>`` header.

    Raises :class:`ClerkAuthError` for every rejected or unverifiable token.
    """

    if not clerk_configured(settings):
        raise ClerkAuthError(
            "clerk_not_configured",
            "clerk authentication is not configured on this service",
            status=503,
        )

    if not CLERK_SDK_AVAILABLE:
        raise ClerkAuthError(
            "clerk_sdk_unavailable",
            "the official clerk verification SDK is not installed on this service",
            status=503,
        )

    token = _bearer_token(authorization)

    options = AuthenticateRequestOptions(
        secret_key=settings.clerk_secret_key,
        authorized_parties=list(settings.clerk_authorized_parties),
        accepts_token=[TokenType.SESSION_TOKEN.value],
        clock_skew_in_ms=5000,
    )

    try:
        state = _client(settings.clerk_secret_key).authenticate_request(
            _SdkRequest(headers={"Authorization": f"Bearer {token}"}), options
        )
    except ClerkAuthError:
        raise
    except Exception as exc:  # noqa: BLE001 - JWKS/network/SDK failure => fail closed
        logger.warning("clerk session verification failed: %s", type(exc).__name__)
        raise ClerkAuthError(
            "clerk_verification_unavailable",
            "the clerk session token could not be verified",
        ) from exc

    if state is None or state.status != AuthStatus.SIGNED_IN or not state.payload:
        raise ClerkAuthError("invalid_clerk_session", "the clerk session token was rejected")

    payload: dict[str, Any] = dict(state.payload)

    issuer = payload.get("iss")
    subject = payload.get("sub")
    if not isinstance(issuer, str) or not issuer:
        raise ClerkAuthError("invalid_clerk_session", "the clerk session token has no issuer")
    if issuer != settings.clerk_issuer:
        raise ClerkAuthError(
            "invalid_clerk_issuer", "the clerk session token was issued by another instance"
        )
    if not isinstance(subject, str) or not subject.strip():
        raise ClerkAuthError("invalid_clerk_session", "the clerk session token has no subject")

    session_status = payload.get("sts")
    session_status = session_status if isinstance(session_status, str) else None
    if session_status and session_status.lower() in _UNUSABLE_SESSION_STATES:
        raise ClerkAuthError("clerk_session_not_active", "the clerk session is not active")

    session_id = payload.get("sid")
    return ClerkIdentity(
        issuer=issuer,
        subject=subject.strip(),
        session_id=session_id if isinstance(session_id, str) else None,
        session_status=session_status,
    )


def verified_primary_email(settings: Settings, subject: str) -> str | None:
    """Return the Clerk-verified primary e-mail for ``subject``, or ``None``.

    This is a *convenience snapshot only*. Anything the browser sends about the
    e-mail address is ignored; the value only ever comes from the Clerk Backend
    API for the already-verified subject. Any failure keeps the local value
    ``NULL`` rather than trusting a client-supplied address.
    """

    if not settings.clerk_secret_key or not subject or not CLERK_SDK_AVAILABLE:
        return None

    try:
        user = _client(settings.clerk_secret_key).users.get(user_id=subject)
    except Exception as exc:  # noqa: BLE001 - never fatal, never trusted
        logger.warning("clerk user lookup failed: %s", type(exc).__name__)
        return None

    primary_id = getattr(user, "primary_email_address_id", None)
    addresses = getattr(user, "email_addresses", None) or []

    for address in addresses:
        if primary_id is not None and getattr(address, "id", None) != primary_id:
            continue
        if getattr(getattr(address, "verification", None), "status", None) != "verified":
            continue
        email = getattr(address, "email_address", None)
        if isinstance(email, str) and email.strip():
            return email.strip().lower()
    return None
