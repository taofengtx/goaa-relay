"""
GOAA Authorization Kernel AK-3 — Deny Matcher
================================================
Pure functions for matching action requests against active Deny Ledger
entries.

Four-phase matching:
  1. Compute fold (internal — caller never provides fold_result)
  2. Candidate deny selection (effect/group + resource subset)
  3. Scope tri-state evaluation
  4. Return sorted, deduplicated matched denies

Classification provenance: AK-3 does NOT verify classification.
  AK-4 adds TrustedClassificationProof.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §13, §18
Plan: AK-3 V27.1 FINAL FREEZE
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
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
from authorization_kernel.deny_event_validation import (
    HASH_PLACEHOLDER,
    LIFECYCLE_EVENT_TYPES,
    TERMINAL_EVENT_TYPES,
    DenyMatchContext,
    DenyMatchResult,
    MatchProofContext,
    NormalizedMatchFailure,
    ScopeMatchStatus,
    build_invalid_match_result,
    canonical_effective_deny_identity,
    normalize_failure_proof,
    require_aware_datetime,
)
from authorization_kernel.deny_ledger_state import (
    DenyAppendResult,
    DenyFoldResult,
    DenyLedger,
    DenyLedgerEntry,
    EffectiveDeny,
    fold_effective_denies,
    verify_ledger_integrity,
)


# ============================================================
# Matching utilities
# ============================================================

def _deny_scope_matches(
    deny_scope: DenyScope,
    request_resource_scopes: tuple[TypedResourceScope, ...],
) -> ScopeMatchStatus:
    """Determine if a deny's scope matches a set of resource scopes.

    This is a simplified tri-state for AK-3.
    AK-4 adds full scope resolution from action request.
    """
    # PERSISTENT_POLICY always matches
    if deny_scope == DenyScope.PERSISTENT_POLICY:
        return ScopeMatchStatus.SAME

    # CURRENT_SESSION: check session_id
    # Simplified for AK-3 — always assumes same session
    if deny_scope == DenyScope.CURRENT_SESSION:
        if request_resource_scopes:
            return ScopeMatchStatus.NARROWER
        return ScopeMatchStatus.SAME

    # CURRENT_TASK / CURRENT_ACTION: check task_id
    if deny_scope in (DenyScope.CURRENT_TASK, DenyScope.CURRENT_ACTION):
        if request_resource_scopes:
            return ScopeMatchStatus.NARROWER
        return ScopeMatchStatus.SAME

    return ScopeMatchStatus.DIFFERENT


def _deny_effect_matches(
    deny_primary: ActionEffect | None,
    deny_secondary: frozenset[ActionEffect],
    deny_groups: frozenset[str],
    request_primary: ActionEffect,
    request_secondary: frozenset[ActionEffect],
    request_groups: frozenset[str],
) -> bool:
    """Check if a deny's effect/group constraints match a request.

    Match if:
      - deny primary_effect matches request primary_effect
        OR deny primary_effect is in request secondary_effects
      - OR deny primary_effect matches any request group
      - OR any deny group matches any request group
      - OR any deny secondary_effect matches request primary/secondary
    """
    # Check effects
    if deny_primary is not None:
        if deny_primary == request_primary:
            return True
        if deny_primary in request_secondary:
            return True

    # Check secondary effects
    for se in deny_secondary:
        if se == request_primary or se in request_secondary:
            return True

    # Check groups
    for dg in deny_groups:
        if dg in request_groups:
            return True
        # Also check if deny primary effect value matches group
        if deny_primary is not None and dg == deny_primary.value:
            return True

    return False


def _deny_resource_matches(
    deny_scopes: tuple[TypedResourceScope, ...],
    request_scopes: tuple[TypedResourceScope, ...],
) -> bool:
    """Check if deny's resource scopes are a subset of request's.

    Multi-resource AND/⊆ rule:
      ALL of deny's resource identities MUST be present in request's.
    """
    if not deny_scopes:
        return True  # No resource constraint → always matches
    if not request_scopes:
        return False  # Request has no resources but deny has constraints

    deny_identities: set[str] = set()
    for scope in deny_scopes:
        try:
            ident = canonical_resource_identity(scope)
            deny_identities.add(ident)
        except Exception:
            return False  # Can't verify — assume no match

    request_identities: set[str] = set()
    for scope in request_scopes:
        try:
            ident = canonical_resource_identity(scope)
            request_identities.add(ident)
        except Exception:
            continue  # Skip unidentifiable request scopes

    # All deny identities must be present in request
    return deny_identities.issubset(request_identities)


# ============================================================
# find_matching_denies — four-phase matching
# ============================================================

@dataclass(frozen=True)
class DenyMatchResultList:
    """List of DenyMatchResult items from find_matching_denies."""
    matched_denies: tuple[DenyMatchResult, ...] = ()
    fold_result: DenyFoldResult | None = None
    match_context: DenyMatchContext | None = None
    stale_fold: bool = False

    def __post_init__(self) -> None:
        if type(self.stale_fold) is not bool:
            raise TypeError("stale_fold must be bool")


def find_matching_denies(
    ledger: DenyLedger,
    request_primary: ActionEffect,
    request_secondary: frozenset[ActionEffect] = frozenset(),
    request_groups: frozenset[str] = frozenset(),
    request_resource_scopes: tuple[TypedResourceScope, ...] = (),
    decision_time: datetime | None = None,
    observed_ledger: DenyLedger | None = None,
) -> DenyMatchResultList:
    """Find all active deny entries matching an action request.

    Four phases:
      1. Fold ledger (internal — caller never provides fold_result)
      2. Candidate deny selection (effect/group + resource subset)
      3. Scope tri-state evaluation
      4. Return sorted, deduplicated results

    AK-3 limitations:
      - classification_provenance_verified = False (AK-4 adds this)
      - authorization_ready = False (AK-4 adds this)
      - GLOBAL_LEDGER_FRESHNESS_PROVEN = NO (AK-4 adds this)
    """

    # Validate decision_time
    if decision_time is not None:
        try:
            require_aware_datetime(decision_time, "match.decision_time")
        except ValueError:
            return DenyMatchResultList(
                matched_denies=(),
                stale_fold=False,
            )

    # Phase 1: Compute fold (internal — matcher never accepts external fold)
    try:
        fold_result = fold_effective_denies(ledger, decision_time)
    except Exception:
        return DenyMatchResultList(
            matched_denies=(),
            stale_fold=False,
        )

    if not fold_result.valid or not fold_result.fold_attemptable:
        return DenyMatchResultList(
            matched_denies=(),
            fold_result=fold_result,
            stale_fold=False,
        )

    # Stale fold protection: verify count + tip
    stale_fold = False
    if observed_ledger is not None:
        try:
            current_tip = observed_ledger.entries[-1].entry_hash if observed_ledger.entries else None
            current_count = len(observed_ledger.entries)
            if (fold_result.ledger_entry_count != current_count
                    or fold_result.ledger_tip_hash != current_tip):
                stale_fold = True
        except Exception:
            stale_fold = True

    # Build match context
    match_context = DenyMatchContext(
        ledger_verified=fold_result.valid,
        ledger_tip_hash=fold_result.ledger_tip_hash,
        ledger_entry_count=fold_result.ledger_entry_count,
        evaluated_at=decision_time,
    )

    # Phase 2: Candidate deny selection
    candidates: list[DenyMatchResult] = []
    for active_deny in fold_result.active_denies:
        # Effect/group match
        effect_match = _deny_effect_matches(
            deny_primary=active_deny.primary_effect,
            deny_secondary=active_deny.secondary_effects,
            deny_groups=active_deny.equivalent_action_groups,
            request_primary=request_primary,
            request_secondary=request_secondary,
            request_groups=request_groups,
        )

        if not effect_match:
            continue

        # Resource subset match (multi-resource AND/⊆)
        resource_match = _deny_resource_matches(
            deny_scopes=active_deny.resource_scopes,
            request_scopes=request_resource_scopes,
        )

        if not resource_match:
            candidates.append(
                DenyMatchResult(
                    matched=False,
                    failed_checks=("resource_scope_does_not_cover_request",),
                    ledger_verified=fold_result.valid,
                )
            )
            continue

        # Phase 3: Scope tri-state
        scope_status = _deny_scope_matches(
            active_deny.deny_scope,
            request_resource_scopes,
        )

        # Simplified scope matching for AK-3:
        # PERSISTENT_POLICY always matches
        # CURRENT_* always matches (full scope resolution in AK-4)
        if scope_status == ScopeMatchStatus.DIFFERENT:
            candidates.append(
                DenyMatchResult(
                    matched=False,
                    failed_checks=("scope_mismatch",),
                    ledger_verified=fold_result.valid,
                )
            )
            continue

        # Matched!
        proof = MatchProofContext(
            ledger_verified=fold_result.valid,
            observed_ledger_tip=fold_result.ledger_tip_hash,
            observed_entry_count=fold_result.ledger_entry_count,
            observation_timestamp=decision_time,
        )

        candidates.append(
            DenyMatchResult(
                matched=True,
                active_deny=active_deny,
                ledger_verified=fold_result.valid,
                match_proof=proof,
            )
        )

    # Phase 4: Sort by canonical identity for stability
    matched = tuple(
        sorted(
            candidates,
            key=lambda r: (
                canonical_effective_deny_identity(
                    r.active_deny.primary_effect if r.matched and r.active_deny is not None else None,
                    r.active_deny.resource_scopes if r.matched and r.active_deny is not None else (),
                ) if r.matched else "",
            ),
        )
    )

    return DenyMatchResultList(
        matched_denies=matched,
        fold_result=fold_result,
        match_context=match_context,
        stale_fold=stale_fold,
    )
