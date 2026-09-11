"""Password hashing, session tokens and short-lived download tokens.

Guarantees
----------
* Passwords are stored as bcrypt hashes only. Plaintext passwords are never
  persisted, logged, or returned.
* Session cookies carry a signed payload; the database only ever stores the
  SHA-256 of the full token, so a database leak cannot be replayed as a login.
* Download links are short-lived HMAC tokens bound to a single document **and**
  to the owning user id, so a leaked URL is useless to anybody else and expires.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

import bcrypt

BCRYPT_ROUNDS = 12
MIN_PASSWORD_LENGTH = 12


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def password_problem(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"password must be at least {MIN_PASSWORD_LENGTH} characters"
    return None


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def token_fingerprint(token: str) -> str:
    """What we persist: never the token itself."""
    return sha256_hex(token)


def _sign(secret: bytes, payload: str) -> str:
    return _b64(hmac.new(secret, payload.encode("ascii"), hashlib.sha256).digest())


def new_session_token(secret: bytes, user_id: str, ttl_seconds: int) -> tuple[str, str, int]:
    """Return ``(token, token_fingerprint, expires_at_epoch)``."""
    now = int(time.time())
    payload = _b64(
        json.dumps(
            {"sid": secrets.token_urlsafe(24), "sub": user_id, "exp": now + ttl_seconds, "iat": now},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    token = f"{payload}.{_sign(secret, payload)}"
    return token, token_fingerprint(token), now + ttl_seconds


def parse_session_token(secret: bytes, token: str) -> dict[str, Any] | None:
    if not token or token.count(".") != 1:
        return None
    payload, signature = token.split(".", 1)
    if not hmac.compare_digest(_sign(secret, payload), signature):
        return None
    try:
        data = json.loads(_unb64(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if int(data.get("exp", 0)) <= int(time.time()):
        return None
    if not isinstance(data.get("sub"), str) or not isinstance(data.get("sid"), str):
        return None
    return data


def new_download_token(secret: bytes, document_id: str, owner_user_id: str, ttl_seconds: int) -> str:
    payload = _b64(
        json.dumps(
            {"doc": document_id, "own": owner_user_id, "exp": int(time.time()) + ttl_seconds},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    return f"{payload}.{_sign(secret, payload)}"


def parse_download_token(secret: bytes, token: str) -> dict[str, Any] | None:
    if not token or token.count(".") != 1:
        return None
    payload, signature = token.split(".", 1)
    if not hmac.compare_digest(_sign(secret, payload), signature):
        return None
    try:
        data = json.loads(_unb64(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if int(data.get("exp", 0)) <= int(time.time()):
        return None
    if not isinstance(data.get("doc"), str) or not isinstance(data.get("own"), str):
        return None
    return data


def mask_email(value: str | None) -> str:
    """Mask an e-mail for cross-account (admin) views. Own account is unmasked."""
    if not value or "@" not in value:
        return "***"
    local, _, domain = value.partition("@")
    if len(local) <= 1:
        head = "*"
    elif len(local) == 2:
        head = local[0] + "*"
    else:
        head = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{head}@{domain}"


def mask_license_number(value: str | None) -> str:
    """Never expose a full licence number outside its own account."""
    if not value:
        return "***"
    tail = value[-4:] if len(value) > 4 else ""
    return f"****{tail}"


def mask_address(value: str | None) -> str:
    if not value:
        return "***"
    text = value.strip()
    if len(text) <= 4:
        return "***"
    return f"{text[:2]}***{text[-2:]}"
