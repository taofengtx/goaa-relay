"""AK-5B2B Capability Grant Lifecycle Candidate.

This module implements the *lifecycle evaluation* model for an AK-5B2A
capability grant identity candidate.  The model follows an **immutable
event** approach: only two semantic events are persisted — *ISSUED* (the
grant identity itself) and *REVOKED* (an optional later event).  All other
lifecycle states are computed at evaluation time from timestamp fields.

Persisted semantics
-------------------
- **ISSUED**  — The grant identity candidate carries ``issued_at``,
  ``not_before``, and ``expires_at``.  This is the creation event.
- **REVOKED** — An optional :class:`RevocationEvent` attached to the
  grant via the deterministic ``grant_id``.

Computed (runtime) states
-------------------------
- **PENDING**  — ``evaluation_time < not_before``
- **ACTIVE**   — ``not_before <= evaluation_time < expires_at`` (or no expiry)
- **EXPIRED**  — ``expires_at`` exists and ``evaluation_time >= expires_at``
- **REVOKED**  — ``revoked_at`` exists (overrides all time-based states)

Rules
-----
- All ``datetime`` values must be timezone-aware UTC.
- ``not_before >= issued_at`` (defaults to ``issued_at`` when omitted).
- ``expires_at > not_before`` (when present).
- ``revoked_at >= issued_at``.
- ``grant_id`` is **never** changed by lifecycle events.
- Each :class:`RevocationEvent` has its own deterministic content identity
  (``event_id``).  The ``event_id`` is **not** a replacement for
  ``grant_id``.
- No implicit :func:`datetime.now` — evaluation time must be passed
  explicitly.
- Identical revocations are idempotent.  Conflicting revocations
  (different ``revoked_by_actor_id`` / ``revocation_reason_code`` for the
  same ``grant_id``) are rejected.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from authorization_kernel.canonical_serialization import sha256_hex
from authorization_kernel.capability_grant_identity import (
    CapabilityGrantIdentityCandidate,
)

# ---------------------------------------------------------------------------
# Domain constant — domain-separated from AK-5B2A's GRANT_ID_DOMAIN
# ---------------------------------------------------------------------------

REVOCATION_EVENT_ID_DOMAIN = "GOAA_AK5B2B_REVOCATION_EVENT_ID_V1"

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class GrantLifecycleState(Enum):
    """Computed lifecycle state of a capability grant at a given time.

    Only ``REVOKED`` requires a persisted event; the others are derived
    from timestamp comparisons.
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class RevocationConflictPolicy(Enum):
    """How to handle a second revocation for the same grant."""

    IDEMPOTENT_ACCEPT = "IDEMPOTENT_ACCEPT"
    CONFLICT_REJECT = "CONFLICT_REJECT"


# ---------------------------------------------------------------------------
# Revocation event dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RevocationEvent:
    """An immutable, content-addressed revocation event.

    The ``event_id`` is a deterministic SHA-256 hex string derived from
    the full payload of this event.  It is **not** a replacement for the
    grant's ``grant_id`` — the grant identity remains unchanged across
    lifecycle events.
    """

    grant_id: str
    event_id: str
    revoked_by_actor_id: str
    revocation_reason_code: str
    revocation_note_digest: str
    revoked_at: datetime


# ---------------------------------------------------------------------------
# Build result (fail-closed)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RevocationBuildResult:
    """Fail-closed result of building a :class:`RevocationEvent`."""

    ok: bool
    revocation_event: Optional[RevocationEvent]
    failed_checks: tuple[str, ...]


@dataclass(frozen=True)
class LifecycleEvaluationResult:
    """Result of evaluating a grant's lifecycle state."""

    state: GrantLifecycleState
    grant_id: str
    evaluation_time: datetime
    revoked_at: Optional[datetime]
    issued_at: datetime
    not_before: datetime
    expires_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Deterministic event identity
# ---------------------------------------------------------------------------


def derive_revocation_event_id(
    grant_id: str,
    revoked_by_actor_id: str,
    revocation_reason_code: str,
    revocation_note_digest: str,
    revoked_at: datetime,
) -> str:
    """Return a deterministic content identity for a revocation event.

    The payload is canonicalised and domain-separated so that the same
    event content always produces the same ``event_id``.
    """
    payload = {
        "domain": REVOCATION_EVENT_ID_DOMAIN,
        "grant_id": grant_id,
        "revoked_by_actor_id": revoked_by_actor_id,
        "revocation_reason_code": revocation_reason_code,
        "revocation_note_digest": revocation_note_digest,
        "revoked_at": _format_dt(revoked_at),
    }
    return sha256_hex(payload)


# ---------------------------------------------------------------------------
# Pure builder
# ---------------------------------------------------------------------------


def build_revocation_event(
    grant_id: str,
    revoked_by_actor_id: str,
    revocation_reason_code: str,
    *,
    revocation_note_digest: str = "",
    revoked_at: datetime,
) -> RevocationBuildResult:
    """Build an immutable :class:`RevocationEvent` (fail-closed).

    Parameters
    ----------
    grant_id:
        The deterministic identity of the grant being revoked.  Must be a
        non-empty string.
    revoked_by_actor_id:
        The actor identifier of the entity performing the revocation.
        Must be a non-empty string.
    revocation_reason_code:
        A machine-readable code describing why the grant was revoked.
        Must be a non-empty string.
    revocation_note_digest:
        An optional SHA-256 hex digest of a human-readable revocation note.
        Defaults to the empty string (no note).
    revoked_at:
        **Required.**  The UTC timestamp of the revocation.  Must be
        timezone-aware UTC.  No implicit system clock fallback.
    """
    failed_checks: list[str] = []

    # --- grant_id ---------------------------------------------------------
    if not isinstance(grant_id, str) or not grant_id.strip():
        failed_checks.append("grant_id must be a non-empty string")

    # --- revoked_by_actor_id ----------------------------------------------
    if not isinstance(revoked_by_actor_id, str) or not revoked_by_actor_id.strip():
        failed_checks.append("revoked_by_actor_id must be a non-empty string")

    # --- revocation_reason_code -------------------------------------------
    if not isinstance(revocation_reason_code, str) or not revocation_reason_code.strip():
        failed_checks.append("revocation_reason_code must be a non-empty string")

    # --- revocation_note_digest -------------------------------------------
    if not isinstance(revocation_note_digest, str):
        failed_checks.append("revocation_note_digest must be a string")

    # --- revoked_at -------------------------------------------------------
    if not isinstance(revoked_at, datetime):
        failed_checks.append("revoked_at must be a datetime")
    else:
        _check_utc(revoked_at, "revoked_at", failed_checks)

    if failed_checks:
        return RevocationBuildResult(
            ok=False,
            revocation_event=None,
            failed_checks=tuple(failed_checks),
        )

    assert revoked_at is not None  # mypy narrowing

    event_id = derive_revocation_event_id(
        grant_id=grant_id,
        revoked_by_actor_id=revoked_by_actor_id,
        revocation_reason_code=revocation_reason_code,
        revocation_note_digest=revocation_note_digest,
        revoked_at=revoked_at,
    )

    event = RevocationEvent(
        grant_id=grant_id,
        event_id=event_id,
        revoked_by_actor_id=revoked_by_actor_id,
        revocation_reason_code=revocation_reason_code,
        revocation_note_digest=revocation_note_digest,
        revoked_at=revoked_at,
    )

    return RevocationBuildResult(
        ok=True,
        revocation_event=event,
        failed_checks=(),
    )


# ---------------------------------------------------------------------------
# Lifecycle evaluation
# ---------------------------------------------------------------------------


def evaluate_grant_lifecycle(
    identity: CapabilityGrantIdentityCandidate,
    evaluation_time: datetime,
    revocation: Optional[RevocationEvent] = None,
) -> LifecycleEvaluationResult:
    """Compute the lifecycle state of a grant at ``evaluation_time``.

    This is a **pure function** — no I/O, no :func:`datetime.now`, no
    mutable state.  The caller must provide an explicit evaluation time.

    Parameters
    ----------
    identity:
        The :class:`CapabilityGrantIdentityCandidate` whose lifecycle is
        being evaluated.
    evaluation_time:
        The UTC timestamp at which to evaluate the lifecycle.  **Must** be
        timezone-aware UTC.
    revocation:
        An optional :class:`RevocationEvent`.  When present, its
        ``grant_id`` must match ``identity.grant_id``.

    Returns
    -------
    LifecycleEvaluationResult
    """
    _check_utc(evaluation_time, "evaluation_time", _raise=True)

    issued_at = identity.issued_at
    not_before = identity.not_before
    expires_at = identity.expires_at

    # --- REVOKED check (highest priority) --------------------------------
    if revocation is not None:
        if revocation.grant_id != identity.grant_id:
            raise ValueError(
                f"RevocationEvent grant_id {revocation.grant_id!r} does not match "
                f"identity grant_id {identity.grant_id!r}"
            )
        return LifecycleEvaluationResult(
            state=GrantLifecycleState.REVOKED,
            grant_id=identity.grant_id,
            evaluation_time=evaluation_time,
            revoked_at=revocation.revoked_at,
            issued_at=issued_at,
            not_before=not_before,
            expires_at=expires_at,
        )

    # --- time-based states (lowest to highest) ---------------------------
    if expires_at is not None and evaluation_time >= expires_at:
        return LifecycleEvaluationResult(
            state=GrantLifecycleState.EXPIRED,
            grant_id=identity.grant_id,
            evaluation_time=evaluation_time,
            revoked_at=None,
            issued_at=issued_at,
            not_before=not_before,
            expires_at=expires_at,
        )

    if evaluation_time < not_before:
        return LifecycleEvaluationResult(
            state=GrantLifecycleState.PENDING,
            grant_id=identity.grant_id,
            evaluation_time=evaluation_time,
            revoked_at=None,
            issued_at=issued_at,
            not_before=not_before,
            expires_at=expires_at,
        )

    # Active: not_before <= evaluation_time < expires_at (or no expiry)
    return LifecycleEvaluationResult(
        state=GrantLifecycleState.ACTIVE,
        grant_id=identity.grant_id,
        evaluation_time=evaluation_time,
        revoked_at=None,
        issued_at=issued_at,
        not_before=not_before,
        expires_at=expires_at,
    )


# ---------------------------------------------------------------------------
# Revocation conflict detection
# ---------------------------------------------------------------------------


def check_revocation_conflict(
    existing: RevocationEvent,
    incoming: RevocationEvent,
) -> RevocationConflictPolicy:
    """Compare two revocation events for the same grant.

    Returns
    -------
    ``IDEMPOTENT_ACCEPT`` if the events are semantically identical
    (same ``revoked_by_actor_id``, ``revocation_reason_code``,
    ``revocation_note_digest``).  Returns ``CONFLICT_REJECT`` otherwise.
    """
    if existing.grant_id != incoming.grant_id:
        raise ValueError(
            f"Cannot compare revocations for different grants: "
            f"{existing.grant_id!r} vs {incoming.grant_id!r}"
        )

    if (
        existing.revoked_by_actor_id == incoming.revoked_by_actor_id
        and existing.revocation_reason_code == incoming.revocation_reason_code
        and existing.revocation_note_digest == incoming.revocation_note_digest
    ):
        return RevocationConflictPolicy.IDEMPOTENT_ACCEPT

    return RevocationConflictPolicy.CONFLICT_REJECT


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_utc(
    dt: datetime,
    field_name: str,
    failed_checks: Optional[list[str]] = None,
    *,
    _raise: bool = False,
) -> None:
    """Verify ``dt`` is timezone-aware and has ``tzinfo=timezone.utc``."""
    if dt.tzinfo is None:
        msg = f"{field_name} must be timezone-aware (got naive datetime)"
        if _raise:
            raise ValueError(msg)
        if failed_checks is not None:
            failed_checks.append(msg)
        return
    if dt.tzinfo != timezone.utc and dt.utcoffset() != timezone.utc.utcoffset(dt.replace(tzinfo=None)):
        msg = f"{field_name} must be in UTC (got {dt.tzinfo!r})"
        if _raise:
            raise ValueError(msg)
        if failed_checks is not None:
            failed_checks.append(msg)


def _format_dt(dt: datetime) -> str:
    """Return RFC 3339 / ISO 8601 string for a UTC datetime."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
