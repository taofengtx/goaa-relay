"""
GOAA Authorization Kernel AK-3 — Deny Ledger State
====================================================
Pure functions and data models for Deny Ledger state management:
  - DenyLedger and DenyLedgerEntry data models
  - create_deny_entry (immutable append, two-phase hash)
  - append_lifecycle_entry (two-phase hash, dual hash chains)
  - fold_effective_denies (expiry via expires_at only)
  - verify_ledger_integrity (total function, structured errors)

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
from authorization_kernel.canonical_serialization import (
    format_utc_rfc3339,
    sha256_hex,
)
from authorization_kernel.deny_event_validation import (
    HASH_PLACEHOLDER,
    LOCKED_FIELDS,
    TERMINAL_EVENT_TYPES,
    LIFECYCLE_EVENT_TYPES,
    DenyCreationRequest,
    DenyCreationValidation,
    DenyLifecycleRequest,
    DenyLifecycleValidation,
    DenyMatchContext,
    LedgerIntegrityCode,
    LedgerIntegrityResult,
    MatchProofContext,
    ScopeMatchStatus,
    validate_deny_creation,
    validate_deny_lifecycle_request,
    validate_origin_scope_matrix,
    require_aware_datetime,
    identity_is_present,
)


# ============================================================
# DenyLedgerEntry
# ============================================================

@dataclass(frozen=True)
class DenyLedgerEntry:
    """A single entry in the append-only Deny Ledger.

    event: the DenyEvent at this position
    previous_entry_hash: SHA-256 of the preceding entry in the global chain
    entry_hash: SHA-256 covering event.event_hash + previous_entry_hash
                + request_id + persistent
    request_id: the action request that triggered this entry (inherited)
    persistent: whether this entry survives session/task boundaries
    """

    event: DenyEvent
    previous_entry_hash: str | None = None
    entry_hash: str = ""
    request_id: str | None = None
    persistent: bool = False

    def __post_init__(self) -> None:
        if type(self.event) is not DenyEvent:
            raise TypeError("event must be a DenyEvent")
        if type(self.persistent) is not bool:
            raise TypeError("persistent must be a bool")
        if self.request_id is not None and not isinstance(self.request_id, str):
            raise TypeError("request_id must be str or None")


# ============================================================
# DenyLedger
# ============================================================

@dataclass(frozen=True)
class DenyLedger:
    """Append-only Deny Ledger as an immutable tuple of entries.

    entries: ordered tuple of DenyLedgerEntry, oldest first
    """

    entries: tuple[DenyLedgerEntry, ...] = ()

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise TypeError("entries must be a tuple")


# ============================================================
# DenyAppendResult
# ============================================================

@dataclass(frozen=True)
class DenyAppendResult:
    """Result of an append operation (create_deny_entry or append_lifecycle_entry)."""
    appended: bool
    ledger: DenyLedger
    entry: DenyLedgerEntry | None = None
    reason_code: str = ""

    def __post_init__(self) -> None:
        if type(self.appended) is not bool:
            raise TypeError("appended must be a bool")
        if self.appended and self.entry is None:
            raise ValueError("appended=True requires entry")
        if self.appended and not self.reason_code:
            raise ValueError("appended=True requires reason_code")
        if not self.appended and not self.reason_code:
            # Allow empty reason_code for unset — caller fills
            pass


# ============================================================
# EffectiveDeny
# ============================================================

@dataclass(frozen=True)
class EffectiveDeny:
    """An active, effective deny derived from a CREATED DenyLedgerEntry.

    All lifecycle fields inherited from the CREATED event.
    source_entry: the DenyLedgerEntry this deny originated from.
    """
    source_entry: DenyLedgerEntry
    deny_id: str
    task_id: str
    session_id: str | None = None
    deny_scope: DenyScope = DenyScope.CURRENT_ACTION
    deny_origin: DenyOrigin = DenyOrigin.AUTOMATIC_POLICY_BLOCK
    primary_effect: ActionEffect | None = None
    secondary_effects: frozenset[ActionEffect] = field(default_factory=frozenset)
    resource_scopes: tuple[TypedResourceScope, ...] = ()
    equivalent_action_groups: frozenset[str] = field(default_factory=frozenset)
    expires_at: datetime | None = None
    approval_id: str | None = None

    def __post_init__(self) -> None:
        if not self.deny_id:
            raise ValueError("deny_id must not be empty")
        if type(self.deny_scope) is not DenyScope:
            raise TypeError("deny_scope must be DenyScope")
        if type(self.deny_origin) is not DenyOrigin:
            raise TypeError("deny_origin must be DenyOrigin")


# ============================================================
# DenyFoldResult
# ============================================================

@dataclass(frozen=True)
class DenyFoldResult:
    """Result of folding a Deny Ledger into active effective denies.

    valid: whether the ledger integrity was confirmed
    evaluated_at: when the fold was performed
    ledger_tip_hash: entry_hash of the last entry in the ledger
    ledger_entry_count: total entries in the ledger
    active_denies: tuple of active EffectiveDeny instances
    failed_checks: reasons for partial or total failure
    fold_attemptable: whether the fold could be attempted (true even if
                      some entries fail, false only for catastrophic failure)
    """
    valid: bool
    evaluated_at: datetime | None = None
    ledger_tip_hash: str | None = None
    ledger_entry_count: int = 0
    active_denies: tuple[EffectiveDeny, ...] = ()
    failed_checks: tuple[str, ...] = ()
    fold_attemptable: bool = False

    def __post_init__(self) -> None:
        if type(self.valid) is not bool:
            raise TypeError("valid must be bool")
        if type(self.fold_attemptable) is not bool:
            raise TypeError("fold_attemptable must be bool")
        if not self.valid and self.active_denies:
            raise ValueError("invalid fold must have empty active_denies")


# ============================================================
# Payload builders
# ============================================================

def deny_ledger_entry_payload(
    entry: DenyLedgerEntry,
) -> dict[str, Any]:
    """Canonical payload for DenyLedgerEntry hash computation.

    Covers:
      event_hash (which transitively covers all Event fields including event_id)
      previous_entry_hash
      request_id
      persistent
    """
    return {
        "event_hash": entry.event.event_hash,
        "previous_entry_hash": entry.previous_entry_hash,
        "request_id": entry.request_id,
        "persistent": entry.persistent,
    }


def _resource_scope_to_dict(scope: TypedResourceScope) -> dict[str, Any]:
    """Convert TypedResourceScope to a canonical-serializable dict."""
    return {
        "scope_type": scope.scope_type.value,
        "canonical_id": scope.canonical_id,
        "attributes": dict(scope.attributes),
    }


def deny_event_payload(event: DenyEvent) -> dict[str, Any]:
    """Build canonical payload dict for a DenyEvent hash computation.

    Covers all security-relevant fields (design doc §15.2, §12).
    Excludes event_hash (hash covers all fields except itself).

    TypedResourceScope objects are converted to dicts via
    _resource_scope_to_dict to enable canonical JSON serialization.
    """
    return {
        "event_id": event.event_id,
        "deny_id": event.deny_id,
        "task_id": event.task_id,
        "session_id": event.session_id,
        "event_type": event.event_type.value,
        "deny_scope": event.deny_scope.value,
        "deny_origin": event.deny_origin.value,
        "primary_effect": event.primary_effect.value if event.primary_effect is not None else None,
        "secondary_effects": event.secondary_effects,
        "resource_scopes": tuple(_resource_scope_to_dict(s) for s in event.resource_scopes),
        "equivalent_action_groups": event.equivalent_action_groups,
        "actor": event.actor,
        "occurred_at": event.occurred_at,
        "expires_at": event.expires_at,
        "reason": event.reason,
        "approval_id": event.approval_id,
        "previous_event_hash": event.previous_event_hash,
    }


def compute_deny_event_hash(event: DenyEvent) -> str:
    """Compute SHA-256 hash of a DenyEvent.

    Uses deny_event_payload() and AK-1 sha256_hex.
    """
    payload = deny_event_payload(event)
    return sha256_hex(payload)


def compute_deny_ledger_entry_hash(entry: DenyLedgerEntry) -> str:
    """Compute SHA-256 hash of a DenyLedgerEntry.

    Entry hash transitively covers event_id through event.event_hash.
    """
    payload = deny_ledger_entry_payload(entry)
    return sha256_hex(payload)


# ============================================================
# Two-phase hash building for DenyEvent
# ============================================================

def _build_deny_event(
    *,
    event_id: str,
    deny_id: str,
    task_id: str,
    session_id: str | None,
    event_type: DenyEventType,
    deny_scope: DenyScope,
    deny_origin: DenyOrigin,
    primary_effect: ActionEffect | None,
    secondary_effects: frozenset[ActionEffect],
    resource_scopes: tuple[TypedResourceScope, ...],
    equivalent_action_groups: frozenset[str],
    actor: str,
    occurred_at: datetime,
    expires_at: datetime | None,
    reason: str,
    approval_id: str | None,
    previous_event_hash: str | None,
) -> DenyEvent:
    """Two-phase hash building for DenyEvent: placehold -> compute -> replace."""
    # Phase 1: provisional Event with HASH_PLACEHOLDER
    provisional = DenyEvent(
        event_id=event_id,
        deny_id=deny_id,
        task_id=task_id,
        session_id=session_id,
        event_type=event_type,
        deny_scope=deny_scope,
        deny_origin=deny_origin,
        primary_effect=primary_effect if primary_effect is not None else DenyEvent.__dataclass_fields__["primary_effect"].default,
        secondary_effects=secondary_effects,
        resource_scopes=resource_scopes,
        equivalent_action_groups=equivalent_action_groups,
        actor=actor,
        occurred_at=occurred_at,
        expires_at=expires_at,
        reason=reason,
        approval_id=approval_id,
        previous_event_hash=previous_event_hash,
        event_hash=HASH_PLACEHOLDER,
    )
    # Phase 2: compute hash
    final_hash = compute_deny_event_hash(provisional)
    # Phase 3: replace
    return dataclasses.replace(provisional, event_hash=final_hash)


# ============================================================
# create_deny_entry — immutable append
# ============================================================

def _get_observed_tip(ledger: DenyLedger) -> str | None:
    """Get the entry_hash of the last entry, or None for empty ledger."""
    if not ledger.entries:
        return None
    return ledger.entries[-1].entry_hash


def create_deny_entry(
    ledger: DenyLedger,
    request: DenyCreationRequest,
) -> DenyAppendResult:
    """Create and append a DENY_CREATED entry (total function).

    Five gates:
      1. Verify input ledger integrity
      2. Structured creation validation
      3. Reject duplicate deny_id / second DENY_CREATED
      4. Build entry with two-phase hash (event then entry)
      5. Verify candidate ledger integrity
    """

    def _fail(code: str) -> DenyAppendResult:
        return DenyAppendResult(
            appended=False,
            ledger=ledger,
            entry=None,
            reason_code=code,
        )

    # Gate 1: Input ledger integrity
    try:
        integrity = verify_ledger_integrity(ledger, verify_hash=False)
        if not integrity.valid:
            return _fail("ledger_integrity_invalid_pre")
    except Exception:
        return _fail("ledger_integrity_check_failed_pre")

    # Gate 2: Structured creation validation
    try:
        validation = validate_deny_creation(request)
        if not validation.valid:
            return _fail(validation.failed_checks[0])
    except Exception:
        return _fail("creation_validation_failed")

    # Gate 3: Reject duplicate deny_id / second DENY_CREATED
    try:
        for entry in ledger.entries:
            if entry.event.event_type == DenyEventType.DENY_CREATED:
                if entry.event.deny_id == request.event.deny_id:
                    return _fail("duplicate_deny_created")
    except Exception:
        return _fail("duplicate_check_failed")

    event = request.event

    # Gate 4: Build entry with two-phase hash
    try:
        # Derive hashes
        previous_event_hash: str | None = None  # First event, no predecessor
        global_previous_entry_hash = _get_observed_tip(ledger)

        # Phase 1-3: Build finalized Event
        final_event = _build_deny_event(
            event_id=event.event_id,
            deny_id=event.deny_id,
            task_id=event.task_id,
            session_id=event.session_id,
            event_type=event.event_type,
            deny_scope=event.deny_scope,
            deny_origin=event.deny_origin,
            primary_effect=event.primary_effect,
            secondary_effects=event.secondary_effects,
            resource_scopes=event.resource_scopes,
            equivalent_action_groups=event.equivalent_action_groups,
            actor=event.actor,
            occurred_at=event.occurred_at,
            expires_at=event.expires_at,
            reason=event.reason,
            approval_id=event.approval_id,
            previous_event_hash=previous_event_hash,
        )

        # Phase 4: Provisional Entry
        provisional_entry = DenyLedgerEntry(
            event=final_event,
            previous_entry_hash=global_previous_entry_hash,
            entry_hash=HASH_PLACEHOLDER,
            request_id=request.request_id,
            persistent=request.persistent,
        )

        # Phase 5: Compute entry hash
        entry_hash = compute_deny_ledger_entry_hash(provisional_entry)

        # Phase 6: Final Entry
        final_entry = dataclasses.replace(provisional_entry, entry_hash=entry_hash)
    except Exception:
        return _fail("entry_build_failed")

    # Construct candidate ledger
    try:
        candidate_ledger = DenyLedger(entries=(*ledger.entries, final_entry))
    except Exception:
        return _fail("candidate_ledger_build_failed")

    # Gate 5: Verify candidate ledger integrity
    try:
        candidate_integrity = verify_ledger_integrity(candidate_ledger)
        if not candidate_integrity.valid:
            return _fail("candidate_ledger_integrity_invalid")
    except Exception:
        return _fail("candidate_integrity_check_failed")

    return DenyAppendResult(
        appended=True,
        ledger=candidate_ledger,
        entry=final_entry,
        reason_code="success",
    )


# ============================================================
# append_lifecycle_entry
# ============================================================

def _find_created_entry(
    ledger: DenyLedger,
    deny_id: str,
) -> DenyLedgerEntry | None:
    """Find the first DENY_CREATED entry for a given deny_id."""
    for entry in ledger.entries:
        if entry.event.deny_id == deny_id and entry.event.event_type == DenyEventType.DENY_CREATED:
            return entry
    return None


def _find_previous_deny_entry(
    ledger: DenyLedger,
    deny_id: str,
) -> DenyLedgerEntry | None:
    """Find the last entry for a given deny_id."""
    found: DenyLedgerEntry | None = None
    for entry in ledger.entries:
        if entry.event.deny_id == deny_id:
            found = entry
    return found


def _build_lifecycle_event(
    request: DenyLifecycleRequest,
    created_entry: DenyLedgerEntry,
    previous_deny_entry: DenyLedgerEntry,
    global_previous_entry_hash: str | None,
) -> DenyLedgerEntry:
    """Two-phase hash building for lifecycle entry.

    Six steps:
      1. Provisional Event with HASH_PLACEHOLDER
      2. compute_deny_event_hash()
      3. Replace -> final Event
      4. Provisional Entry with HASH_PLACEHOLDER
      5. compute_deny_ledger_entry_hash()
      6. Replace -> final Entry
    """
    created_event = created_entry.event

    # Step 1: Provisional Event
    provisional_event = DenyEvent(
        event_id=request.event_id,
        deny_id=created_event.deny_id,
        task_id=created_event.task_id,
        session_id=created_event.session_id,
        event_type=request.event_type,
        deny_scope=created_event.deny_scope,
        deny_origin=created_event.deny_origin,
        primary_effect=created_event.primary_effect,
        secondary_effects=created_event.secondary_effects,
        resource_scopes=created_event.resource_scopes,
        equivalent_action_groups=created_event.equivalent_action_groups,
        actor=request.actor,
        occurred_at=request.occurred_at,
        expires_at=created_event.expires_at,
        reason=request.reason,
        approval_id=request.approval_id,
        previous_event_hash=previous_deny_entry.event.event_hash,
        event_hash=HASH_PLACEHOLDER,
    )

    # Step 2: Compute event hash
    event_hash = compute_deny_event_hash(provisional_event)

    # Step 3: Final Event
    final_event = dataclasses.replace(provisional_event, event_hash=event_hash)

    # Step 4: Provisional Entry
    provisional_entry = DenyLedgerEntry(
        event=final_event,
        previous_entry_hash=global_previous_entry_hash,
        entry_hash=HASH_PLACEHOLDER,
        request_id=created_entry.request_id,
        persistent=created_entry.persistent,
    )

    # Step 5: Compute entry hash
    entry_hash = compute_deny_ledger_entry_hash(provisional_entry)

    # Step 6: Final Entry
    return dataclasses.replace(provisional_entry, entry_hash=entry_hash)


def append_lifecycle_entry(
    ledger: DenyLedger,
    request: DenyLifecycleRequest,
) -> DenyAppendResult:
    """Append a lifecycle entry (REVOKED/SUPERSEDED/EXPIRED) — total function.

    Dual hash chains:
      - event.previous_event_hash: from last entry for same deny_id
      - entry.previous_entry_hash: from global ledger tail

    Locked fields derived from CREATED entry.
    """

    def _fail(code: str) -> DenyAppendResult:
        return DenyAppendResult(
            appended=False,
            ledger=ledger,
            entry=None,
            reason_code=code,
        )

    # Gate 1: Input ledger integrity
    try:
        integrity = verify_ledger_integrity(ledger, verify_hash=False)
        if not integrity.valid:
            return _fail("ledger_integrity_invalid_pre")
    except Exception:
        return _fail("ledger_integrity_check_failed_pre")

    # Find created_entry and previous_deny_entry
    try:
        created_entry = _find_created_entry(ledger, request.deny_id)
        previous_deny_entry = _find_previous_deny_entry(ledger, request.deny_id)
    except Exception:
        return _fail("ledger_lookup_failed")

    # Gate 2: Lifecycle request validation
    try:
        validation = validate_deny_lifecycle_request(
            created_entry,
            previous_deny_entry,
            ledger.entries,
            request,
        )
        if not validation.valid:
            return _fail(validation.failed_checks[0])
    except Exception:
        return _fail("lifecycle_validation_failed")

    # Gate 3: Build lifecycle entry with two-phase hash
    try:
        global_previous_entry_hash = _get_observed_tip(ledger)

        lifecycle_entry = _build_lifecycle_event(
            request=request,
            created_entry=created_entry,
            previous_deny_entry=previous_deny_entry,
            global_previous_entry_hash=global_previous_entry_hash,
        )
    except Exception:
        return _fail("lifecycle_entry_build_failed")

    # Construct candidate ledger
    try:
        candidate_ledger = DenyLedger(entries=(*ledger.entries, lifecycle_entry))
    except Exception:
        return _fail("candidate_ledger_build_failed")

    # Gate 4: Verify candidate ledger integrity
    try:
        candidate_integrity = verify_ledger_integrity(candidate_ledger)
        if not candidate_integrity.valid:
            return _fail("candidate_ledger_integrity_invalid")
    except Exception:
        return _fail("candidate_integrity_check_failed")

    return DenyAppendResult(
        appended=True,
        ledger=candidate_ledger,
        entry=lifecycle_entry,
        reason_code="success",
    )


# ============================================================
# verify_ledger_integrity — total function
# ============================================================

def _is_valid_sha256_hex(value: str) -> bool:
    """Check if a string is a valid 64-char lowercase SHA-256 hex."""
    if not isinstance(value, str):
        return False
    if len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def verify_ledger_integrity(
    ledger: DenyLedger,
    verify_hash: bool = True,
) -> LedgerIntegrityResult:
    """Structural total-function ledger integrity verification.

    Validates:
      1. Global entry chain (previous_entry_hash consistency)
      2. Per-deny event chains (previous_event_hash consistency)
      3. Event ID global uniqueness
      4. First event for each deny must be DENY_CREATED
      5. No duplicate DENY_CREATED for same deny_id
      6. Terminal state machine (no events after terminal)
      7. Locked field consistency across lifecycle
      8. Time monotonicity
      9. EXPIRED requires expires_at and occurred_at >= expires_at
      10. persistent/scope consistency
      11. Origin/Scope matrix
      12. AUTOMATIC_POLICY_BLOCK five conditions
      13. Resource scope non-empty and identity unique (for CREATED)
      14. Action condition non-empty
      15. Hash validation (when verify_hash=True)
    """
    try:
        if type(ledger) is not DenyLedger:
            return LedgerIntegrityResult(
                valid=False,
                code=LedgerIntegrityCode.INTERNAL_ERROR,
                failed_checks=("invalid_ledger_type",),
            )

        entries = ledger.entries
        if not entries:
            return LedgerIntegrityResult(
                valid=True,
                code=LedgerIntegrityCode.OK,
                failed_checks=(),
                entry_count=0,
                ledger_tip_hash=None,
            )

        entry_count = len(entries)
        ledger_tip_hash = entries[-1].entry_hash if entries else None
        failed: list[str] = []

        # Track deny state per deny_id
        deny_states: dict[str, DenyEventType | None] = {}  # deny_id -> current state
        deny_created_entries: dict[str, DenyLedgerEntry] = {}  # deny_id -> CREATED entry
        seen_event_ids: set[str] = set()

        # 1. Global entry chain
        for i, entry in enumerate(entries):
            if i == 0:
                if entry.previous_entry_hash is not None:
                    failed.append("first_entry_has_previous_hash")
            else:
                expected = entries[i - 1].entry_hash
                if entry.previous_entry_hash != expected:
                    failed.append(f"global_chain_broken_at_{i}")
                    break

        # 2-15. Per-entry checks
        for i, entry in enumerate(entries):
            ev = entry.event
            deny_id = ev.deny_id

            # 3. Event ID uniqueness
            if ev.event_id in seen_event_ids:
                failed.append(f"duplicate_event_id_{ev.event_id}")
            seen_event_ids.add(ev.event_id)

            # Track deny state
            if deny_id not in deny_states:
                deny_states[deny_id] = None

            current_state = deny_states[deny_id]

            # 4. First event must be CREATED
            if current_state is None:
                if ev.event_type != DenyEventType.DENY_CREATED:
                    failed.append(f"first_event_not_created_{deny_id}")
                deny_states[deny_id] = DenyEventType.DENY_CREATED
                deny_created_entries[deny_id] = entry
            else:
                # 5. No duplicate CREATED
                if ev.event_type == DenyEventType.DENY_CREATED:
                    failed.append(f"duplicate_created_{deny_id}")

                # 6. Terminal state check
                if current_state in TERMINAL_EVENT_TYPES:
                    failed.append(f"terminal_state_violation_{deny_id}")

                # Update state
                if ev.event_type in TERMINAL_EVENT_TYPES:
                    deny_states[deny_id] = ev.event_type

            # Skip CREATED entry checks for lifecycle entries beyond basic
            if current_state is not None:
                created_entry = deny_created_entries.get(deny_id)
                if created_entry is not None:
                    # 7. Locked field consistency
                    created_ev = created_entry.event
                    locked_mismatches: list[str] = []
                    for locked_field in LOCKED_FIELDS:
                        created_val = getattr(created_ev, locked_field, None)
                        current_val = getattr(ev, locked_field, None)
                        if created_val != current_val:
                            locked_mismatches.append(locked_field)
                    if locked_mismatches:
                        failed.append(f"locked_field_drift_{deny_id}:{','.join(locked_mismatches)}")

                    # 8. Time monotonicity
                    if created_ev.occurred_at is not None and ev.occurred_at is not None:
                        if ev.occurred_at < created_ev.occurred_at:
                            failed.append(f"time_reversal_{deny_id}")

                    # 9. EXPIRED requires expires_at and occurred_at >= expires_at
                    if ev.event_type == DenyEventType.DENY_EXPIRED:
                        if created_ev.expires_at is None:
                            failed.append(f"expired_no_expiry_{deny_id}")
                        elif ev.occurred_at is not None and ev.occurred_at < created_ev.expires_at:
                            failed.append(f"expired_before_expiry_{deny_id}")

        # 10. persistent/scope consistency for CREATED entries
        for deny_id, created_entry in deny_created_entries.items():
            created_ev = created_entry.event
            persistent = created_entry.persistent
            scope = created_ev.deny_scope

            if scope == DenyScope.PERSISTENT_POLICY and not persistent:
                failed.append(f"scope_persistent_not_persistent_{deny_id}")
            if scope != DenyScope.PERSISTENT_POLICY and persistent:
                failed.append(f"non_persistent_scope_with_persistent_{deny_id}")

            # 11. Origin/Scope matrix
            matrix_check = validate_origin_scope_matrix(created_ev.deny_origin, scope)
            if matrix_check is not None:
                failed.append(f"origin_scope_matrix_{deny_id}")

            # 12. AUTOMATIC_POLICY_BLOCK five conditions
            if created_ev.deny_origin == DenyOrigin.AUTOMATIC_POLICY_BLOCK:
                conditions_ok = (
                    type(persistent) is bool and persistent is True
                    and created_ev.deny_scope is DenyScope.PERSISTENT_POLICY
                    and created_ev.expires_at is not None
                    and bool(created_ev.equivalent_action_groups)
                    and bool(created_ev.resource_scopes)
                )
                if not conditions_ok:
                    failed.append(f"auto_policy_conditions_{deny_id}")

            # 13. Resource scopes non-empty and identity unique
            if not created_ev.resource_scopes:
                failed.append(f"empty_resource_scopes_{deny_id}")
            else:
                seen_ids: set[str] = set()
                for scope in created_ev.resource_scopes:
                    try:
                        ident = canonical_resource_identity(scope)
                    except Exception:
                        failed.append(f"canonical_identity_error_{deny_id}")
                        continue
                    if ident in seen_ids:
                        failed.append(f"duplicate_resource_identity_{deny_id}")
                    seen_ids.add(ident)

            # 14. Action condition
            if created_ev.primary_effect is None and not created_ev.equivalent_action_groups:
                failed.append(f"action_condition_missing_{deny_id}")

        # 15. Per-deny event chain verification
        deny_event_previous: dict[str, str | None] = {}
        for entry in entries:
            deny_id = entry.event.deny_id
            expected_prev = deny_event_previous.get(deny_id)
            if expected_prev is not None:
                if entry.event.previous_event_hash != expected_prev:
                    failed.append(f"event_chain_broken_{deny_id}")
                    break
            if entry.event.event_hash:
                deny_event_previous[deny_id] = entry.event.event_hash

        # Hash validation (when requested)
        if verify_hash:
            try:
                for i, entry in enumerate(entries):
                    # Verify event hash
                    if entry.event.event_hash:
                        recomputed_event = compute_deny_event_hash(entry.event)
                        if recomputed_event != entry.event.event_hash:
                            # Recompute using provisional
                            provisional = dataclasses.replace(entry.event, event_hash=HASH_PLACEHOLDER)
                            expected_hash = compute_deny_event_hash(provisional)
                            if expected_hash != entry.event.event_hash:
                                failed.append(f"event_hash_mismatch_at_{i}")
                    # Verify entry hash
                    if entry.entry_hash:
                        recomputed_entry = compute_deny_ledger_entry_hash(entry)
                        if recomputed_entry != entry.entry_hash:
                            provisional = dataclasses.replace(entry, entry_hash=HASH_PLACEHOLDER)
                            expected_hash = compute_deny_ledger_entry_hash(provisional)
                            if expected_hash != entry.entry_hash:
                                failed.append(f"entry_hash_mismatch_at_{i}")
            except Exception:
                failed.append("hash_validation_error")

        if failed:
            return LedgerIntegrityResult(
                valid=False,
                code=LedgerIntegrityCode.GLOBAL_CHAIN_BROKEN,
                failed_checks=tuple(failed),
                entry_count=entry_count,
                ledger_tip_hash=ledger_tip_hash,
            )

        return LedgerIntegrityResult(
            valid=True,
            code=LedgerIntegrityCode.OK,
            entry_count=entry_count,
            ledger_tip_hash=ledger_tip_hash,
        )

    except Exception as exc:
        return LedgerIntegrityResult(
            valid=False,
            code=LedgerIntegrityCode.INTERNAL_ERROR,
            failed_checks=("internal_error",),
            error_details=str(exc)[:200],
        )


# ============================================================
# fold_effective_denies
# ============================================================

def fold_effective_denies(
    ledger: DenyLedger,
    decision_time: datetime | None = None,
) -> DenyFoldResult:
    """Fold ledger entries into active effective denies.

    Only uses expires_at to determine activity.
    Does NOT append DENY_EXPIRED — fold is read-only.
    """
    if decision_time is not None:
        try:
            require_aware_datetime(decision_time, "fold.decision_time")
        except ValueError:
            return DenyFoldResult(
                valid=False,
                evaluated_at=None,
                ledger_tip_hash=None,
                ledger_entry_count=0,
                active_denies=(),
                failed_checks=("fold_decision_time_naive",),
                fold_attemptable=False,
            )

    # Verify ledger integrity
    integrity = verify_ledger_integrity(ledger)
    if not integrity.valid:
        return DenyFoldResult(
            valid=False,
            evaluated_at=decision_time,
            ledger_tip_hash=integrity.ledger_tip_hash,
            ledger_entry_count=integrity.entry_count,
            active_denies=(),
            failed_checks=integrity.failed_checks,
            fold_attemptable=False,
        )

    try:
        active_denies: list[EffectiveDeny] = []
        deny_id_state: dict[str, DenyEventType] = {}

        for entry in ledger.entries:
            ev = entry.event
            deny_id = ev.deny_id

            # Track lifecycle state
            current_state = deny_id_state.get(deny_id)
            if ev.event_type == DenyEventType.DENY_CREATED:
                if current_state is None:
                    # Only consider CREATED entries as candidates for active denies
                    if decision_time is not None:
                        # expires_at: only authority for activity
                        if ev.expires_at is not None and decision_time > ev.expires_at:
                            # Inactive — don't add, but track state
                            deny_id_state[deny_id] = DenyEventType.DENY_CREATED
                            continue

                    active = EffectiveDeny(
                        source_entry=entry,
                        deny_id=ev.deny_id,
                        task_id=ev.task_id,
                        session_id=ev.session_id,
                        deny_scope=ev.deny_scope,
                        deny_origin=ev.deny_origin,
                        primary_effect=ev.primary_effect if ev.primary_effect != DenyEvent.__dataclass_fields__["primary_effect"].default else None,
                        secondary_effects=ev.secondary_effects,
                        resource_scopes=ev.resource_scopes,
                        equivalent_action_groups=ev.equivalent_action_groups,
                        expires_at=ev.expires_at,
                        approval_id=ev.approval_id,
                    )
                    active_denies.append(active)
                deny_id_state[deny_id] = DenyEventType.DENY_CREATED

            elif ev.event_type in TERMINAL_EVENT_TYPES:
                deny_id_state[deny_id] = ev.event_type
                # Remove from active denies
                active_denies = [d for d in active_denies if d.deny_id != deny_id]

        return DenyFoldResult(
            valid=True,
            evaluated_at=decision_time,
            ledger_tip_hash=integrity.ledger_tip_hash,
            ledger_entry_count=integrity.entry_count,
            active_denies=tuple(active_denies),
            fold_attemptable=True,
        )

    except Exception as exc:
        return DenyFoldResult(
            valid=False,
            evaluated_at=decision_time,
            ledger_tip_hash=integrity.ledger_tip_hash if integrity.valid else None,
            ledger_entry_count=integrity.entry_count,
            active_denies=(),
            failed_checks=("fold_internal_error",),
            fold_attemptable=False,
        )
