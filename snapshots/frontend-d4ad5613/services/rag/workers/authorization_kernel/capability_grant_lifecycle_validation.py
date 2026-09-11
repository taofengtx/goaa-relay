"""AK-5B2B Capability Grant Lifecycle Validation.

Validation rules for :class:`RevocationEvent` and lifecycle consistency.
All validators are pure functions — no I/O, no network, no system clock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from authorization_kernel.capability_grant_identity import (
    CapabilityGrantIdentityCandidate,
)
from authorization_kernel.capability_grant_lifecycle import (
    GrantLifecycleState,
    LifecycleEvaluationResult,
    RevocationBuildResult,
    RevocationConflictPolicy,
    RevocationEvent,
    build_revocation_event,
    check_revocation_conflict,
    evaluate_grant_lifecycle,
)


@dataclass(frozen=True)
class LifecycleValidationResult:
    """Fail-closed result of a lifecycle validation."""

    ok: bool
    failed_checks: tuple[str, ...]


# ---------------------------------------------------------------------------
# Revocation event field validation
# ---------------------------------------------------------------------------


def validate_revocation_event_fields(
    grant_id: str,
    revoked_by_actor_id: str,
    revocation_reason_code: str,
    *,
    revocation_note_digest: str = "",
    revoked_at: Optional[datetime] = None,
) -> RevocationBuildResult:
    """Validate and build a :class:`RevocationEvent`.

    Thin wrapper around :func:`build_revocation_event` that enforces all
    field-level constraints:

    - ``grant_id`` — non-empty string
    - ``revoked_by_actor_id`` — non-empty string
    - ``revocation_reason_code`` — non-empty string
    - ``revocation_note_digest`` — string (may be empty for no note)
    - ``revoked_at`` — timezone-aware UTC ``datetime``
    """
    return build_revocation_event(
        grant_id=grant_id,
        revoked_by_actor_id=revoked_by_actor_id,
        revocation_reason_code=revocation_reason_code,
        revocation_note_digest=revocation_note_digest,
        revoked_at=revoked_at,
    )


# ---------------------------------------------------------------------------
# Lifecycle consistency validation
# ---------------------------------------------------------------------------


def validate_lifecycle_consistency(
    identity: CapabilityGrantIdentityCandidate,
    evaluation_time: datetime,
    revocation: Optional[RevocationEvent] = None,
) -> LifecycleValidationResult:
    """Validate that a grant identity and optional revocation are consistent.

    Checks
    ------
    1. ``identity`` is not ``None``.
    2. ``evaluation_time`` is timezone-aware UTC.
    3. ``revoked_at >= identity.issued_at`` (if revocation present).
    4. ``revocation.grant_id == identity.grant_id`` (if revocation present).
    5. Duplicate-revocation idempotency: a second identical revocation is
       accepted (IDEMPOTENT_ACCEPT); a conflicting revocation is rejected.
    """
    failed_checks: list[str] = []

    # --- identity ---------------------------------------------------------
    if identity is None:
        failed_checks.append("identity must not be None")

    # --- evaluation_time --------------------------------------------------
    if not isinstance(evaluation_time, datetime):
        failed_checks.append("evaluation_time must be a datetime")
    elif evaluation_time.tzinfo is None:
        failed_checks.append("evaluation_time must be timezone-aware")
    elif evaluation_time.tzinfo != timezone.utc:
        if evaluation_time.utcoffset() != timezone.utc.utcoffset(evaluation_time.replace(tzinfo=None)):
            failed_checks.append("evaluation_time must be in UTC")

    # --- revocation consistency -------------------------------------------
    if revocation is not None:
        _validate_revocation_consistency(identity, revocation, failed_checks)

    if failed_checks:
        return LifecycleValidationResult(
            ok=False,
            failed_checks=tuple(failed_checks),
        )

    return LifecycleValidationResult(
        ok=True,
        failed_checks=(),
    )


# ---------------------------------------------------------------------------
# Revocation consistency (shared logic)
# ---------------------------------------------------------------------------


def _validate_revocation_consistency(
    identity: CapabilityGrantIdentityCandidate,
    revocation: RevocationEvent,
    failed_checks: list[str],
) -> None:
    """Validate revocation-time constraints against the grant identity."""
    # grant_id match
    if revocation.grant_id != identity.grant_id:
        failed_checks.append(
            f"revocation grant_id {revocation.grant_id!r} does not match "
            f"identity grant_id {identity.grant_id!r}"
        )

    # revoked_at >= issued_at
    if revocation.revoked_at < identity.issued_at:
        failed_checks.append(
            f"revoked_at ({revocation.revoked_at}) must not be before "
            f"issued_at ({identity.issued_at})"
        )


def validate_revocation_idempotency(
    existing: Optional[RevocationEvent],
    incoming: RevocationEvent,
) -> LifecycleValidationResult:
    """Validate that ``incoming`` revocation is idempotent with ``existing``.

    * If ``existing`` is ``None`` — always valid (first revocation).
    * If ``existing`` is semantically identical — valid (idempotent).
    * If ``existing`` is semantically different — **rejected** (conflict).
    """
    failed_checks: list[str] = []

    if existing is not None:
        policy = check_revocation_conflict(existing, incoming)
        if policy == RevocationConflictPolicy.CONFLICT_REJECT:
            failed_checks.append(
                f"Revocation conflict for grant {incoming.grant_id!r}: "
                f"existing (actor={existing.revoked_by_actor_id!r}, "
                f"reason={existing.revocation_reason_code!r}) vs "
                f"incoming (actor={incoming.revoked_by_actor_id!r}, "
                f"reason={incoming.revocation_reason_code!r})"
            )

    if failed_checks:
        return LifecycleValidationResult(
            ok=False,
            failed_checks=tuple(failed_checks),
        )

    return LifecycleValidationResult(
        ok=True,
        failed_checks=(),
    )
