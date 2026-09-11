"""
GOAA Authorization Kernel AK-3 — Deny Event Validation
========================================================
Pure validation functions for deny creation requests, lifecycle requests,
Origin/Scope matrix checks, strict aware datetime, and structured failure
normalization.

No I/O, no subprocess, no network. All functions are deterministic.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §15, §16
Plan: AK-3 V27.1 FINAL FREEZE
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from authorization_kernel.enums import (
    ActionEffect,
    DenyEventType,
    DenyOrigin,
    DenyScope,
)
from authorization_kernel.deny_event import DenyEvent
from authorization_kernel.resource_scope import (
    TypedResourceScope,
    canonical_resource_identity,
)
from authorization_kernel.canonical_serialization import sha256_hex


# ============================================================
# Constants — V27.1 FINAL FREEZE
# ============================================================

HASH_PLACEHOLDER = "0" * 64

TERMINAL_EVENT_TYPES: frozenset[DenyEventType] = frozenset({
    DenyEventType.DENY_REVOKED,
    DenyEventType.DENY_SUPERSEDED,
    DenyEventType.DENY_EXPIRED,
})

LIFECYCLE_EVENT_TYPES: frozenset[DenyEventType] = frozenset({
    DenyEventType.DENY_REVOKED,
    DenyEventType.DENY_SUPERSEDED,
    DenyEventType.DENY_EXPIRED,
})

LOCKED_FIELDS: frozenset[str] = frozenset({
    "deny_scope",
    "deny_origin",
    "task_id",
    "session_id",
    "request_id",
    "primary_effect",
    "secondary_effects",
    "resource_scopes",
    "equivalent_action_groups",
    "persistent",
    "expires_at",
    # approval_id is NOT locked — varies per lifecycle event
})


# ── DenyOrigin × DenyScope matrix (V27.1 frozen specification) ──
# Derived from design document §16.1, §15.3, §15.4, §16.3.
# Not an explicit table in the original design.
DENY_ORIGIN_SCOPE_MATRIX: dict[DenyOrigin, frozenset[DenyScope]] = {
    DenyOrigin.USER_DENIAL: frozenset({
        DenyScope.CURRENT_ACTION,
        DenyScope.CURRENT_TASK,
        DenyScope.CURRENT_SESSION,
        DenyScope.PERSISTENT_POLICY,
    }),
    DenyOrigin.APPROVER_DENIAL: frozenset({
        DenyScope.CURRENT_ACTION,
        DenyScope.CURRENT_TASK,
        DenyScope.CURRENT_SESSION,
        DenyScope.PERSISTENT_POLICY,
    }),
    DenyOrigin.PERSISTENT_POLICY: frozenset({
        DenyScope.PERSISTENT_POLICY,
    }),
    DenyOrigin.AUTOMATIC_POLICY_BLOCK: frozenset({
        DenyScope.PERSISTENT_POLICY,
    }),
}

# Verify all DenyOrigin members are covered
assert len(DENY_ORIGIN_SCOPE_MATRIX) == len(list(DenyOrigin)), (
    "Origin/Scope matrix must cover all DenyOrigin members"
)


# ============================================================
# Strict aware datetime
# ============================================================

def require_aware_datetime(value: Any, field_name: str) -> None:
    """Three-layer strict aware datetime check.

    Raises ValueError if:
      1. value is not a datetime instance
      2. value.tzinfo is None (naive)
      3. value.utcoffset() is None (fixed-offset edge case)
    """
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name}: not a datetime instance, got {type(value).__name__}")
    if value.tzinfo is None:
        raise ValueError(f"{field_name}: tzinfo is None (naive datetime)")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name}: utcoffset() is None (cannot determine UTC offset)")


# ============================================================
# Origin/Scope matrix check
# ============================================================

def validate_origin_scope_matrix(
    origin: DenyOrigin,
    scope: DenyScope,
) -> str | None:
    """Return None if (origin, scope) is allowed, or a stable reason_code."""
    allowed = DENY_ORIGIN_SCOPE_MATRIX.get(origin)
    if allowed is None:
        return "deny_origin_scope_invalid"
    if scope not in allowed:
        return "deny_origin_scope_invalid"
    return None


# ============================================================
# Identity presence check
# ============================================================

def identity_is_present(value: Any) -> bool:
    """Check if a value is a non-empty, non-whitespace string."""
    return isinstance(value, str) and bool(value.strip())


# ============================================================
# Creation Request
# ============================================================

@dataclass(frozen=True)
class DenyCreationRequest:
    """Request to create a deny entry in the Ledger.

    Contains the DenyEvent data plus two Ledger-level fields:
      - persistent: whether this deny survives session/task boundaries
      - request_id: the action request that triggered this deny (if any)
    """

    event: DenyEvent
    persistent: bool = False
    request_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.persistent) is not bool:
            raise TypeError("persistent must be a bool")
        if self.request_id is not None and not isinstance(self.request_id, str):
            raise TypeError("request_id must be str or None")
        if self.request_id is not None and not self.request_id.strip():
            raise ValueError("request_id must not be empty")


@dataclass(frozen=True)
class DenyCreationValidation:
    """Structured result of validate_deny_creation()."""
    valid: bool
    failed_checks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.valid and self.failed_checks:
            raise ValueError("valid=True requires empty failed_checks")
        if not self.valid and not self.failed_checks:
            raise ValueError("valid=False requires non-empty failed_checks")


def validate_deny_creation(request: DenyCreationRequest) -> DenyCreationValidation:
    """Three-phase structured creation validation (total function)."""

    # ════════════════════════════════════════════════════════════
    # Phase 1: Container type validation
    # ════════════════════════════════════════════════════════════
    if type(request) is not DenyCreationRequest:
        return DenyCreationValidation(valid=False, failed_checks=("deny_invalid_request_type",))

    event = request.event
    if type(event) is not DenyEvent:
        return DenyCreationValidation(valid=False, failed_checks=("deny_invalid_event_type",))
    if type(request.persistent) is not bool:
        return DenyCreationValidation(valid=False, failed_checks=("deny_persistent_not_bool",))

    # ════════════════════════════════════════════════════════════
    # Phase 2: Member-level schema validation
    # ════════════════════════════════════════════════════════════

    # event_type must be DENY_CREATED
    if type(event.event_type) is not DenyEventType:
        return DenyCreationValidation(valid=False, failed_checks=("deny_event_type_type_invalid",))
    if event.event_type != DenyEventType.DENY_CREATED:
        return DenyCreationValidation(valid=False, failed_checks=("deny_event_type_not_created",))

    # Strings: non-empty
    for field_name, value in (
        ("deny_id", event.deny_id),
        ("event_id", event.event_id),
        ("actor", event.actor),
    ):
        if not isinstance(value, str) or not value.strip():
            return DenyCreationValidation(
                valid=False, failed_checks=(f"deny_{field_name}_empty",),
            )

    # request_id: None or non-empty string
    if request.request_id is not None:
        if not isinstance(request.request_id, str):
            return DenyCreationValidation(valid=False, failed_checks=("deny_request_id_type",))
        if not request.request_id.strip():
            return DenyCreationValidation(valid=False, failed_checks=("deny_request_id_empty",))

    # primary_effect: ActionEffect or None
    if event.primary_effect is not None and type(event.primary_effect) is not ActionEffect:
        return DenyCreationValidation(valid=False, failed_checks=("deny_primary_effect_type",))

    # secondary_effects: frozenset with ActionEffect members
    if type(event.secondary_effects) is not frozenset:
        return DenyCreationValidation(valid=False, failed_checks=("deny_secondary_effects_not_frozenset",))
    for eff in event.secondary_effects:
        if type(eff) is not ActionEffect:
            return DenyCreationValidation(valid=False, failed_checks=("deny_secondary_effect_member_type",))

    # equivalent_action_groups: frozenset with non-empty string members
    if type(event.equivalent_action_groups) is not frozenset:
        return DenyCreationValidation(valid=False, failed_checks=("deny_groups_not_frozenset",))
    for group in event.equivalent_action_groups:
        if not isinstance(group, str) or not group.strip():
            return DenyCreationValidation(valid=False, failed_checks=("deny_group_member_invalid",))

    # resource_scopes: non-empty tuple of TypedResourceScope
    if type(event.resource_scopes) is not tuple:
        return DenyCreationValidation(valid=False, failed_checks=("deny_scopes_not_tuple",))
    if not event.resource_scopes:
        return DenyCreationValidation(valid=False, failed_checks=("deny_resource_scopes_empty",))
    seen_identities: set[str] = set()
    for scope in event.resource_scopes:
        if type(scope) is not TypedResourceScope:
            return DenyCreationValidation(valid=False, failed_checks=("deny_scope_member_type",))
        try:
            ident = canonical_resource_identity(scope)
        except Exception:
            return DenyCreationValidation(valid=False, failed_checks=("deny_scope_canonical_failed",))
        if ident in seen_identities:
            return DenyCreationValidation(valid=False, failed_checks=("deny_scope_identity_duplicate",))
        seen_identities.add(ident)

    # deny_scope / deny_origin type checks
    if type(event.deny_scope) is not DenyScope:
        return DenyCreationValidation(valid=False, failed_checks=("deny_scope_type_invalid",))
    if type(event.deny_origin) is not DenyOrigin:
        return DenyCreationValidation(valid=False, failed_checks=("deny_origin_type_invalid",))

    # occurred_at: must be timezone-aware (three-layer check)
    if event.occurred_at is not None:
        try:
            require_aware_datetime(event.occurred_at, "creation.occurred_at")
        except ValueError:
            return DenyCreationValidation(valid=False, failed_checks=("deny_occurred_at_naive",))

    # expires_at: None or timezone-aware
    if event.expires_at is not None:
        try:
            require_aware_datetime(event.expires_at, "creation.expires_at")
        except ValueError:
            return DenyCreationValidation(valid=False, failed_checks=("deny_expires_at_naive",))
        if event.occurred_at is not None and event.expires_at < event.occurred_at:
            return DenyCreationValidation(valid=False, failed_checks=("deny_expires_before_occurred",))

    # ════════════════════════════════════════════════════════════
    # Phase 3: Business rule validation
    # ════════════════════════════════════════════════════════════

    # Action condition: must have primary_effect or equivalent_action_groups
    if event.primary_effect is None and not event.equivalent_action_groups:
        return DenyCreationValidation(valid=False, failed_checks=("deny_action_condition_missing",))

    # CURRENT_ACTION scope requires request_id
    if event.deny_scope == DenyScope.CURRENT_ACTION:
        if request.request_id is None:
            return DenyCreationValidation(valid=False, failed_checks=("deny_request_id_missing",))
    else:
        if request.request_id is not None:
            return DenyCreationValidation(valid=False, failed_checks=("deny_unexpected_request_id",))

    # persistent/scope consistency
    if event.deny_scope == DenyScope.PERSISTENT_POLICY:
        if not request.persistent:
            return DenyCreationValidation(valid=False, failed_checks=("deny_persistent_scope_required",))
    else:
        if request.persistent:
            return DenyCreationValidation(valid=False, failed_checks=("deny_persistent_not_allowed",))

    # Origin/Scope matrix
    matrix_check = validate_origin_scope_matrix(event.deny_origin, event.deny_scope)
    if matrix_check is not None:
        return DenyCreationValidation(valid=False, failed_checks=(matrix_check,))

    # AUTOMATIC_POLICY_BLOCK five conditions
    if event.deny_origin == DenyOrigin.AUTOMATIC_POLICY_BLOCK:
        conditions_ok = (
            type(request.persistent) is bool and request.persistent is True
            and event.deny_scope is DenyScope.PERSISTENT_POLICY
            and event.expires_at is not None
            and bool(event.equivalent_action_groups)
            and bool(event.resource_scopes)
        )
        if not conditions_ok:
            return DenyCreationValidation(
                valid=False,
                failed_checks=("automatic_policy_conditions_incomplete",),
            )

    return DenyCreationValidation(valid=True)


# ============================================================
# Lifecycle Request
# ============================================================

@dataclass(frozen=True)
class DenyLifecycleRequest:
    """Request to append a lifecycle event (REVOKED/SUPERSEDED/EXPIRED)."""

    deny_id: str
    event_id: str
    event_type: DenyEventType
    actor: str
    occurred_at: datetime
    reason: str = ""
    approval_id: str | None = None

    def __post_init__(self) -> None:
        if not self.deny_id.strip():
            raise ValueError("deny_id must not be empty")
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")
        if type(self.event_type) is not DenyEventType:
            raise TypeError("event_type must be a DenyEventType")
        if self.event_type not in LIFECYCLE_EVENT_TYPES:
            raise ValueError(f"event_type must be one of {LIFECYCLE_EVENT_TYPES}")
        if not self.actor.strip():
            raise ValueError("actor must not be empty")
        if not isinstance(self.occurred_at, datetime):
            raise TypeError("occurred_at must be a datetime")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if self.approval_id is not None and not isinstance(self.approval_id, str):
            raise TypeError("approval_id must be str or None")
        if self.approval_id is not None and not self.approval_id.strip():
            raise ValueError("approval_id must not be empty string")


@dataclass(frozen=True)
class DenyLifecycleValidation:
    """Structured result of validate_deny_lifecycle_request()."""
    valid: bool
    failed_checks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.valid and self.failed_checks:
            raise ValueError("valid=True requires empty failed_checks")
        if not self.valid and not self.failed_checks:
            raise ValueError("valid=False requires non-empty failed_checks")


def validate_deny_lifecycle_request(
    created_entry: DenyLedgerEntry | None,
    previous_deny_entry: DenyLedgerEntry | None,
    ledger_entries: tuple[DenyLedgerEntry, ...],
    request: DenyLifecycleRequest,
) -> DenyLifecycleValidation:
    """Structured lifecycle request validation (total function).

    Validates:
      - request type
      - event_type in {REVOKED, SUPERSEDED, EXPIRED}
      - deny_id / event_id / actor / reason non-empty
      - approval_id None or non-empty string
      - occurred_at timezone-aware (three-layer)
      - deny_id exists with CREATED entry
      - event_id globally unique
      - current state is CREATED (terminal states reject)
      - time does not reverse (occurred_at >= last lifecycle event)
      - EXPIRED requires expires_at and occurred_at >= expires_at
    """
    # Type check
    if type(request) is not DenyLifecycleRequest:
        return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_invalid_request_type",))

    # event_type check
    if type(request.event_type) is not DenyEventType:
        return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_event_type_type",))
    if request.event_type not in LIFECYCLE_EVENT_TYPES:
        return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_event_type_invalid",))

    # String non-empty checks
    for field_name, value in (
        ("deny_id", request.deny_id),
        ("event_id", request.event_id),
        ("actor", request.actor),
        ("reason", request.reason),
    ):
        if not isinstance(value, str) or not value.strip():
            return DenyLifecycleValidation(
                valid=False, failed_checks=(f"lifecycle_{field_name}_empty",),
            )

    # approval_id: None or non-empty string
    if request.approval_id is not None:
        if not isinstance(request.approval_id, str) or not request.approval_id.strip():
            return DenyLifecycleValidation(
                valid=False, failed_checks=("lifecycle_approval_id_empty",),
            )

    # occurred_at timezone-aware (three-layer)
    try:
        require_aware_datetime(request.occurred_at, "lifecycle.occurred_at")
    except ValueError:
        return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_occurred_at_naive",))

    # deny_id must exist
    if created_entry is None:
        return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_deny_not_found",))

    # event_id globally unique
    for entry in ledger_entries:
        if entry.event.event_id == request.event_id:
            return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_event_id_duplicate",))

    # current state must be CREATED
    if previous_deny_entry is not None:
        current_event_type = previous_deny_entry.event.event_type
        if current_event_type in TERMINAL_EVENT_TYPES:
            return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_terminal_state",))

    # Time monotonicity: occurred_at >= last lifecycle event for same deny
    if previous_deny_entry is not None and previous_deny_entry.event.occurred_at is not None:
        if request.occurred_at < previous_deny_entry.event.occurred_at:
            return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_time_reversal",))

    # DENY_EXPIRED: expires_at must be non-None, occurred_at >= expires_at
    if request.event_type == DenyEventType.DENY_EXPIRED:
        created_expires_at = created_entry.event.expires_at
        if created_expires_at is None:
            return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_expiry_not_defined",))
        if request.occurred_at < created_expires_at:
            return DenyLifecycleValidation(valid=False, failed_checks=("lifecycle_expired_before_expiry",))

    return DenyLifecycleValidation(valid=True)


# ============================================================
# Failure normalization (for matcher)
# ============================================================

@dataclass(frozen=True)
class NormalizedMatchFailure:
    """A structured failure description in a match/proof context."""
    reason: str
    proof_fields: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("reason must not be empty")
        # Strict boolean check on proof fields
        for f in self.proof_fields:
            if not isinstance(f, str):
                raise TypeError(f"proof field must be str, got {type(f).__name__}")


@dataclass(frozen=True)
class MatchProofContext:
    """Context for ledger integrity proof during matching.

    ledger_verified: whether the ledger passed integrity verification
    observed_ledger_tip: the observed entry_hash of the last ledger entry
    observed_entry_count: the total number of entries observed
    observation_timestamp: when this context was captured
    """
    ledger_verified: bool
    observed_ledger_tip: str | None
    observed_entry_count: int
    observation_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if type(self.ledger_verified) is not bool:
            raise TypeError("ledger_verified must be bool")
        if self.observed_entry_count < 0:
            raise ValueError("observed_entry_count must be non-negative")


@dataclass(frozen=True)
class DenyMatchContext:
    """Context for a single deny match evaluation."""
    ledger_verified: bool = False
    ledger_tip_hash: str | None = None
    ledger_entry_count: int = 0
    evaluated_at: datetime | None = None


@dataclass(frozen=True)
class DenyMatchResult:
    """Result of matching a deny against an action request.

    matched: True if this deny applies to the action request
    active_deny: the effective deny that matched (if matched=True)
    failed_checks: list of reasons for failure (if matched=False)
    ledger_verified: whether the ledger integrity was confirmed
    match_proof: integrity proof context (if available)
    """
    matched: bool
    active_deny: Any | None = None  # EffectiveDeny type
    failed_checks: tuple[str | NormalizedMatchFailure, ...] = ()
    ledger_verified: bool = False
    match_proof: MatchProofContext | None = None

    def __post_init__(self) -> None:
        if type(self.matched) is not bool:
            raise TypeError("matched must be bool")
        # matched=True requires active_deny
        if self.matched and self.active_deny is None:
            raise ValueError("matched=True requires active_deny")
        # matched=False requires failed_checks
        if not self.matched and not self.failed_checks:
            raise ValueError("matched=False requires failed_checks")


# ============================================================
# Integrity result types
# ============================================================

class LedgerIntegrityCode:
    """Stable ledger integrity error codes."""
    OK = "integrity_ok"
    EMPTY_LEDGER = "empty_ledger"
    GLOBAL_CHAIN_BROKEN = "global_chain_broken"
    EVENT_CHAIN_BROKEN = "event_chain_broken"
    DUPLICATE_EVENT_ID = "duplicate_event_id"
    FIRST_EVENT_NOT_CREATED = "first_event_not_created"
    DUPLICATE_CREATED = "duplicate_created"
    TERMINAL_STATE_VIOLATION = "terminal_state_violation"
    LOCKED_FIELD_DRIFT = "locked_field_drift"
    TIME_REVERSAL = "time_reversal"
    EXPIRED_BEFORE_EXPIRY = "expired_before_expiry"
    SCOPE_CONSISTENCY = "scope_consistency"
    ORIGIN_SCOPE_MATRIX = "origin_scope_matrix"
    AUTO_POLICY_CONDITIONS = "auto_policy_conditions"
    EMPTY_RESOURCE_SCOPES = "empty_resource_scopes"
    DUPLICATE_RESOURCE_IDENTITY = "duplicate_resource_identity"
    ACTION_CONDITION_MISSING = "action_condition_missing"
    HASH_VALIDATION_FAILED = "hash_validation_failed"
    CANONICALIZATION_ERROR = "canonicalization_error"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class LedgerIntegrityResult:
    """Structured ledger integrity verification result."""
    valid: bool
    code: str = ""
    failed_checks: tuple[str, ...] = ()
    entry_count: int = 0
    ledger_tip_hash: str | None = None
    error_details: str | None = None

    def __post_init__(self) -> None:
        if self.valid and self.code != LedgerIntegrityCode.OK:
            raise ValueError("valid=True requires code=OK")


# ============================================================
# Canonical effective deny identity
# ============================================================

def canonical_effective_deny_identity(
    effect: ActionEffect | None,
    resource_scopes: tuple[TypedResourceScope, ...],
) -> str:
    """Form a stable identity for deduplicating effective denies.

    Uses canonical resource identities from AK-1.
    """
    parts: list[str] = []
    if effect is not None:
        parts.append(f"effect:{effect.value}")
    for scope in resource_scopes:
        try:
            ident = canonical_resource_identity(scope)
        except Exception:
            ident = f"unknown:{scope.canonical_id}"
        parts.append(f"resource:{ident}")
    return "|".join(parts)


def normalize_failure_proof(
    reason: str,
    proof_fields: frozenset[str] | None = None,
) -> NormalizedMatchFailure:
    """Single-point construction of NormalizedMatchFailure."""
    return NormalizedMatchFailure(
        reason=reason,
        proof_fields=proof_fields or frozenset(),
    )


def build_invalid_match_result(
    reason: str,
    proof_fields: frozenset[str] | None = None,
    ledger_verified: bool = False,
    match_proof: MatchProofContext | None = None,
) -> DenyMatchResult:
    """Single-point construction of a non-matching DenyMatchResult."""
    failure = normalize_failure_proof(reason, proof_fields)
    return DenyMatchResult(
        matched=False,
        failed_checks=(failure,),
        ledger_verified=ledger_verified,
        match_proof=match_proof,
    )


# ============================================================
# Scope match status (for matcher)
# ============================================================

class ScopeMatchStatus:
    """Tri-state scope matching outcome."""
    SAME = "same"
    NARROWER = "narrower"
    DIFFERENT = "different"


# ============================================================
# Forward reference for DenyLedgerEntry (defined in deny_ledger_state.py)
# ============================================================

# Import at runtime to avoid circular import
import typing as _t

if _t.TYPE_CHECKING:
    from authorization_kernel.deny_ledger_state import DenyLedgerEntry
