"""Golden (AI Butler) business session — isolated candidate, customer path only.

Why this module exists
----------------------
Clerk authenticates the human; the golden AI Butler still has to know *which
business principal* is talking to it. The golden runtime already answers that
question with an **opaque, database-backed, revocable token**, read on every
request by ``runtime/order_db.py``::

    authenticate_order_token(token)
        SELECT user_id, role FROM goaa_order_tokens WHERE token=%s AND revoked_at IS NULL
    revoke_order_tokens(user_id)
        UPDATE goaa_order_tokens SET revoked_at=now() WHERE user_id=%s

This module reuses that *mechanism* rather than inventing a parallel one:

* the token is the same shape the golden mints (``uuid4().hex``, opaque — the
  value carries no subject, role or expiry);
* the row has the same columns the golden function reads (``user_id``,
  ``token``, ``role``, ``revoked_at``);
* authentication is the same query, and revocation is the same ``UPDATE``;
* consequently the golden authentication function applies to
  ``business_tokens`` verbatim with the table name changed — see
  ``tests/test_golden_business_contract.py``, which takes the SQL out of the
  golden clone instead of restating it.

There is no digest column and no expiry column, on purpose: the golden
authentication function reads neither, and a rule only this service enforced
would make two truths about one token. (An earlier revision of this candidate
stored a SHA-256 digest and enforced a TTL; that was **not** contract
compatible and was replaced. See the delivery notes: this is a retraction, not
an oversight.) Revocation is the single lever that stops a token being
accepted, exactly as in the golden runtime.

What it deliberately refuses to do
----------------------------------
* It never decides ownership from an e-mail address. The only key is
  ``(issuer, subject)``, which is already the unique key of
  ``user_identities`` (migration 0005).
* It never treats the local identity id in ``users`` (the C2 *test* identity
  table) as a golden business id. ``business_tokens.user_id`` references a
  freshly minted ``business_subjects`` row, which plays the role
  ``goaa_order_users.id`` plays in the golden schema.
* It never grants an agent/admin role. ``business_tokens.role`` is restricted
  to ``'customer'`` at the database level; the agent path is out of scope and
  must not be granted implicitly by this bridge.
* It never merges, moves or re-labels existing business data.

Session lifecycle
-----------------
* **login**:   ``ensure_subject`` (link once, by ``(issuer, subject)``) then
  ``issue_token`` — which revokes the principal's previous live tokens first,
  so at most one business credential is alive at a time.
* **refresh**: the browser re-presents the same opaque token; nothing is
  re-derived from Clerk, and the stored row is unchanged.
* **sign-out**: ``revoke_subject`` marks every live token of the principal
  revoked, so a token captured before the sign-out is refused afterwards.
  ``revoke_all`` is the same operation reached through the identity link, for
  when the Clerk session is still available.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from .db import execute, fetch_all, fetch_one
from .security import mask_email

#: The only business role this candidate can mint. Kept as a constant *and* a
#: database CHECK constraint so neither a caller nor a future edit can widen it
#: silently.
BUSINESS_ROLE = "customer"

_EVENT_SUBJECT_LINKED = "business.subject_linked"
_EVENT_TOKEN_ISSUED = "business.token_issued"
_EVENT_TOKEN_REVOKED = "business.token_revoked"
_EVENT_TOKEN_REJECTED = "business.token_rejected"

#: Refusal reasons. Stable strings: they end up in the audit row *and* in the
#: API answer, and they never echo the presented token.
REASON_UNKNOWN = "unknown"
REASON_REVOKED = "revoked"


class BusinessSessionError(Exception):
    """Base class for the business-session bridge."""


class BusinessTokenInvalid(BusinessSessionError):
    """The presented bearer token is not (or is no longer) usable."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"business token is not usable: {reason}")
        self.reason = reason


class BusinessSubjectConflict(BusinessSessionError):
    """The identity row asked to link is already bound to another subject."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_token() -> str:
    """A fresh opaque business token, in the golden's own shape."""

    return str(uuid.uuid4()).replace("-", "")


#: A cheap pre-check only. It can *refuse* a value that cannot be one of ours
#: (wrong length or alphabet) without a database round trip; it never decides
#: that a token is valid — validity is always the row (or its absence).
_TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")


def looks_like_token(token: str | None) -> bool:
    return bool(token) and bool(_TOKEN_RE.match(token.strip()))


def _event(
    conn: Any,
    event_type: str,
    *,
    user_id: str | None,
    issuer: str,
    subject: str,
    email: str | None,
    detail: dict[str, Any],
) -> None:
    """Append to the shared, append-only ``identity_events`` stream."""

    with conn.cursor() as cur:
        cur.execute(
            "insert into identity_events "
            "(event_type, subject_user_id, provider, issuer, subject, email_masked, detail) "
            "values (%s, %s, 'clerk', %s, %s, %s, %s::jsonb)",
            (
                event_type,
                user_id,
                issuer,
                subject,
                mask_email(email) if email else None,
                json.dumps(detail),
            ),
        )


def subject_for_user(conn: Any, user_id: str) -> dict[str, Any] | None:
    """The business subject linked to this identity row, if any."""

    return fetch_one(
        conn,
        "select subject_id, kind, linked_via from business_subject_links l "
        "join business_subjects s on s.id = l.subject_id where l.user_id = %s",
        (user_id,),
    )


def ensure_subject(
    conn: Any,
    *,
    user_id: str,
    issuer: str,
    subject: str,
    email: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return the business subject for a *verified* identity, creating it once.

    Creates nothing else: no order, no matter, no profile, and no role. Linking
    is serialised so a double-submit cannot mint two business principals.
    """

    if not user_id:
        raise BusinessSessionError("a verified local user id is required")
    if not issuer or not subject:
        raise BusinessSessionError("issuer and subject are required")

    existing = subject_for_user(conn, user_id)
    if existing is not None:
        return {"user_id": str(existing["subject_id"]), "created": False}

    with conn.transaction():
        # Serialise concurrent first logins of this identity.
        fetch_one(
            conn,
            "select pg_advisory_xact_lock(hashtextextended(%s::text, 0::bigint))",
            (f"golden-subject|{user_id}",),
        )
        existing = subject_for_user(conn, user_id)
        if existing is not None:
            return {"user_id": str(existing["subject_id"]), "created": False}

        created_at = now or _utcnow()
        row = fetch_one(
            conn,
            "insert into business_subjects (id, kind, created_at, updated_at) "
            "values (%s, 'customer', %s, %s) returning id",
            (str(uuid.uuid4()), created_at, created_at),
        )
        subject_id = str(row["id"])
        fetch_one(
            conn,
            "insert into business_subject_links (user_id, subject_id, linked_via, issuer, subject, created_at) "
            "values (%s, %s, 'clerk_issuer_subject', %s, %s, %s) returning user_id",
            (user_id, subject_id, issuer, subject, created_at),
        )
        _event(
            conn,
            _EVENT_SUBJECT_LINKED,
            user_id=user_id,
            issuer=issuer,
            subject=subject,
            email=email,
            detail={"kind": "customer"},
        )
    return {"user_id": subject_id, "created": True}


def issue_token(
    conn: Any,
    *,
    user_id: str,
    issuer: str,
    subject: str,
    email: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Mint a fresh opaque business token for this identity's principal.

    The insert is the golden's own shape. The previous live token(s) of the
    principal are revoked first — expressible in the golden vocabulary, and the
    reason the "one live credential" property holds. Returns the token **once**:
    the value is never logged and never written anywhere but the row.
    """

    linked = subject_for_user(conn, user_id)
    if linked is None:
        raise BusinessSessionError("the identity has no business subject yet")
    subject_id = str(linked["subject_id"])

    issued = now or _utcnow()
    token = new_token()

    with conn.transaction():
        execute(
            conn,
            "update business_tokens set revoked_at = %s "
            "where user_id = %s and revoked_at is null",
            (issued, subject_id),
        )
        fetch_one(
            conn,
            "insert into business_tokens (user_id, token, role, created_at, issued_at) "
            "values (%s, %s, %s, %s, %s) returning id",
            (subject_id, token, BUSINESS_ROLE, issued, issued),
        )
        _event(
            conn,
            _EVENT_TOKEN_ISSUED,
            user_id=user_id,
            issuer=issuer,
            subject=subject,
            email=email,
            detail={"role": BUSINESS_ROLE},
        )

    return {
        "token": token,
        "user_id": subject_id,
        "role": BUSINESS_ROLE,
        "issued_at": issued.isoformat(),
    }


def authenticate_token(conn: Any, token: str, *, now: datetime | None = None) -> dict[str, Any]:
    """Resolve an opaque business token to its principal, or refuse.

    This is the golden lookup: the row is found by the token value itself and
    the caller must not be revoked. ``role`` and ``user_id`` come from the row —
    never from the caller, the browser or the token.
    """

    if not looks_like_token(token):
        raise BusinessTokenInvalid(REASON_UNKNOWN)

    row = fetch_one(
        conn,
        "select id, user_id, role, revoked_at, created_at, last_used_at "
        "from business_tokens where token = %s and revoked_at is null",
        (token.strip(),),
    )
    if row is None:
        # Distinguish "was revoked" from "was never ours" for the audit trail;
        # the answer to the caller is the same refusal either way.
        if _row_was_revoked(conn, token.strip()):
            raise BusinessTokenInvalid(REASON_REVOKED)
        raise BusinessTokenInvalid(REASON_UNKNOWN)

    moment = now or _utcnow()
    execute(conn, "update business_tokens set last_used_at = %s where id = %s", (moment, row["id"]))
    return {
        "user_id": str(row["user_id"]),
        "role": row["role"],
        "issued_at": _iso(row.get("created_at")),
        "last_used_at": moment.isoformat(),
    }


def _row_was_revoked(conn: Any, token: str) -> bool:
    row = fetch_one(
        conn,
        "select revoked_at from business_tokens where token = %s",
        (token,),
    )
    return bool(row and row["revoked_at"] is not None)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def revoke_subject(
    conn: Any,
    *,
    subject_id: str,
    reason: str,
    user_id: str | None = None,
    issuer: str | None = None,
    subject: str | None = None,
    email: str | None = None,
    now: datetime | None = None,
) -> int:
    """Revoke every live token of one business principal.

    This is the golden's ``revoke_order_tokens`` with the identity bookkeeping
    kept for the audit trail: identified by the principal id alone, so the
    caller only needs *a* proof of that principal — either the identity link
    (sign-out while the Clerk session is still valid) or the live business token
    itself (sign-out that already happened).
    """

    with conn.transaction():
        revoked = execute(
            conn,
            "update business_tokens set revoked_at = %s "
            "where user_id = %s and revoked_at is null",
            (now or _utcnow(), subject_id),
        )
        if revoked:
            _event(
                conn,
                _EVENT_TOKEN_REVOKED,
                user_id=user_id,
                issuer=issuer or "unknown",
                subject=subject or "unknown",
                email=email,
                detail={"revoked": int(revoked), "reason": reason},
            )
    return int(revoked)


def revoke_all(
    conn: Any,
    *,
    user_id: str,
    issuer: str,
    subject: str,
    email: str | None = None,
    now: datetime | None = None,
) -> int:
    """Revoke every live token of this identity's business principal."""

    linked = subject_for_user(conn, user_id)
    if linked is None:
        return 0
    return revoke_subject(
        conn,
        subject_id=str(linked["subject_id"]),
        reason="sign_out",
        user_id=user_id,
        issuer=issuer,
        subject=subject,
        email=email,
        now=now,
    )


def live_token_count(conn: Any, subject_id: str) -> int:
    row = fetch_one(
        conn,
        "select count(*) as live from business_tokens "
        "where user_id = %s and revoked_at is null",
        (subject_id,),
    )
    return int(row["live"]) if row else 0


def record_rejection(
    conn: Any,
    *,
    token: str,
    issuer: str | None = None,
    subject: str | None = None,
    reason: str,
) -> None:
    """Audit a refused token in its **own** transaction.

    The caller's transaction is about to roll back, so this record is written
    separately — otherwise the very refusals worth auditing would vanish. The
    token itself is never stored, not even its digest.
    """

    _event(
        conn,
        _EVENT_TOKEN_REJECTED,
        user_id=None,
        issuer=issuer or "unknown",
        subject=subject or "unknown",
        email=None,
        detail={"reason": reason, "presented_len": len(token or "")},
    )


def list_live_tokens(conn: Any, subject_id: str) -> list[dict[str, Any]]:
    """Diagnostic helper: the live credentials of a principal.

    Returns metadata only — the token value is never selected back out.
    """

    return fetch_all(
        conn,
        "select id, issued_at, last_used_at from business_tokens "
        "where user_id = %s and revoked_at is null order by issued_at",
        (subject_id,),
    )
