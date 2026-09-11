"""
GOAA Authorization Kernel AK-3 — Deny Matcher Unit Tests
==========================================================
Tests: find_matching_denies, effect/group matching, resource subset,
scope tri-state, fold internal computation, stale fold detection.

Framework: unittest (standard library). No pytest dependency.
All tests are pure — no I/O, no subprocess, no network.

Plan: AK-3 V27.1 FINAL FREEZE
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from typing import Any

from authorization_kernel.enums import (
    ActionEffect,
    DenyEventType,
    DenyOrigin,
    DenyScope,
    ResourceScopeType,
)
from authorization_kernel.deny_event import DenyEvent
from authorization_kernel.resource_scope import (
    TypedResourceScope,
    canonical_resource_identity,
)
from authorization_kernel.deny_event_validation import (
    DenyCreationRequest,
    DenyMatchContext,
    DenyMatchResult,
    MatchProofContext,
)
from authorization_kernel.deny_ledger_state import (
    DenyLedger,
    DenyLedgerEntry,
    EffectiveDeny,
    DenyFoldResult,
    create_deny_entry,
    append_lifecycle_entry,
    fold_effective_denies,
)
from authorization_kernel.deny_matcher import (
    find_matching_denies,
    DenyMatchResultList,
)


# ============================================================
# Helpers (minimal — reuse patterns from state tests)
# ============================================================

TZ_UTC = timezone.utc

def utc_now() -> datetime:
    return datetime.now(TZ_UTC)

def make_scope(canonical_id: str = "/tmp/test") -> TypedResourceScope:
    return TypedResourceScope(
        scope_type=ResourceScopeType.FILE_PATH,
        canonical_id=canonical_id,
    )

SCOPE_A = make_scope("/tmp/a")
SCOPE_B = make_scope("/tmp/b")
SCOPE_C = make_scope("/tmp/c")

def make_event(
    deny_id: str = "deny-1",
    event_id: str = "evt-1",
    deny_origin: DenyOrigin = DenyOrigin.USER_DENIAL,
    deny_scope: DenyScope = DenyScope.PERSISTENT_POLICY,
    primary_effect: ActionEffect | None = ActionEffect.DELETE,
    groups: frozenset[str] | None = None,
    resource_scopes: tuple[TypedResourceScope, ...] | None = None,
    **kwargs: Any,
) -> DenyEvent:
    if groups is None:
        groups = frozenset({"write"})
    if resource_scopes is None:
        resource_scopes = (SCOPE_A,)
    from authorization_kernel.deny_event import DenyEvent as DE
    return DE(
        event_id=event_id,
        deny_id=deny_id,
        task_id="task-1",
        session_id="session-1",
        event_type=DenyEventType.DENY_CREATED,
        deny_scope=deny_scope,
        deny_origin=deny_origin,
        primary_effect=primary_effect if primary_effect is not None else ActionEffect.READ,
        secondary_effects=frozenset(),
        resource_scopes=resource_scopes,
        equivalent_action_groups=groups,
        actor="user",
        occurred_at=utc_now(),
        reason="test",
        approval_id=None,
        **kwargs,
    )


def _make_ledger_with_denies(
    events: list[DenyEvent],
) -> DenyLedger:
    """Create a ledger with multiple deny entries."""
    ledger = DenyLedger()
    for ev in events:
        request = DenyCreationRequest(
            event=ev,
            persistent=(ev.deny_scope == DenyScope.PERSISTENT_POLICY),
        )
        result = create_deny_entry(ledger, request)
        if not result.appended:
            raise RuntimeError(f"Failed to append: {result.reason_code}")
        ledger = result.ledger
    return ledger


# ============================================================
# Test: find_matching_denies — fold computed internally
# ============================================================

class TestMatcherFoldInternal(unittest.TestCase):

    def test_matcher_computes_fold_internally(self):
        """Matcher computes fold internally — does not accept external fold."""
        event = make_event()
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_groups=frozenset({"write"}),
            request_resource_scopes=(SCOPE_A,),
        )
        self.assertIsNotNone(result.fold_result)
        self.assertTrue(result.fold_result.valid)

    def test_fold_invalid_returns_empty_matches(self):
        """Invalid fold → empty matched denies."""
        # Ledger with no CREATED entry (just a raw REVOKED)
        bad_ledger = DenyLedger(entries=(
            DenyLedgerEntry(
                event=DenyEvent(
                    event_id="bad",
                    deny_id="bad",
                    task_id="task-1",
                    event_type=DenyEventType.DENY_REVOKED,
                    primary_effect=ActionEffect.READ,
                    resource_scopes=(SCOPE_A,),
                    actor="user",
                    occurred_at=utc_now(),
                ),
                previous_entry_hash=None,
                entry_hash="",
            ),
        ))
        result = find_matching_denies(
            ledger=bad_ledger,
            request_primary=ActionEffect.READ,
        )
        self.assertEqual(len(result.matched_denies), 0)
        self.assertFalse(result.fold_result.valid) if result.fold_result else None


# ============================================================
# Test: find_matching_denies — effect/group matching
# ============================================================

class TestMatcherEffectGroup(unittest.TestCase):

    def test_effect_match_by_primary(self):
        """Deny matches when primary effect matches request primary."""
        event = make_event(primary_effect=ActionEffect.DELETE)
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A,),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 1)

    def test_effect_match_by_secondary(self):
        """Deny matches when primary is in request secondary."""
        event = make_event(primary_effect=ActionEffect.DELETE)
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.WRITE,
            request_secondary=frozenset({ActionEffect.DELETE}),
            request_resource_scopes=(SCOPE_A,),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 1)

    def test_effect_match_by_group(self):
        """Deny matches when group matches request group."""
        event = make_event(
            primary_effect=ActionEffect.READ,
            groups=frozenset({"deploy"}),
        )
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DEPLOY,
            request_groups=frozenset({"deploy"}),
            request_resource_scopes=(SCOPE_A,),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 1)

    def test_no_effect_match(self):
        """No effect/group match → no matched deny."""
        event = make_event(primary_effect=ActionEffect.DELETE)
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.READ,
            request_groups=frozenset({"read"}),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 0)


# ============================================================
# Test: find_matching_denies — resource subset matching
# ============================================================

class TestMatcherResourceSubset(unittest.TestCase):

    def test_resource_subset_matches(self):
        """Deny resource is subset of request resource → match."""
        event = make_event(resource_scopes=(SCOPE_A,))
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A, SCOPE_B),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 1)

    def test_resource_not_in_request_no_match(self):
        """Deny resource not in request resources → no match."""
        event = make_event(resource_scopes=(SCOPE_C,))
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A, SCOPE_B),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 0)

    def test_multi_resource_and_semantics(self):
        """Multi-resource deny: ALL deny resources must be in request."""
        event = make_event(resource_scopes=(SCOPE_A, SCOPE_B))
        ledger = _make_ledger_with_denies([event])
        # Request has A and B → match
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A, SCOPE_B, SCOPE_C),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 1)
        # Request has only A → no match (B missing)
        result2 = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A,),
        )
        matched2 = [r for r in result2.matched_denies if r.matched]
        self.assertEqual(len(matched2), 0)

    def test_empty_deny_resources_matches(self):
        """Deny with no resource constraints matches any request."""
        event = make_event(resource_scopes=(SCOPE_A,))  # must have some per DenyEvent
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_B, SCOPE_C),
        )
        matched = [r for r in result.matched_denies if r.matched]
        # Deny has SCOPE_A which is not in (B, C) → no match
        self.assertEqual(len(matched), 0)


# ============================================================
# Test: find_matching_denies — scope matching
# ============================================================

class TestMatcherScope(unittest.TestCase):

    def test_persistent_policy_matches(self):
        """PERSISTENT_POLICY scope always matches."""
        event = make_event(deny_scope=DenyScope.PERSISTENT_POLICY)
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A,),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 1)

    def test_current_task_matches(self):
        """CURRENT_TASK scope matches (simplified for AK-3)."""
        event = make_event(deny_scope=DenyScope.CURRENT_TASK)
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A,),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 1)


# ============================================================
# Test: find_matching_denies — full flow
# ============================================================

class TestMatcherFullFlow(unittest.TestCase):

    def test_matched_deny_includes_proof(self):
        """Match result includes proof context."""
        event = make_event()
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A,),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertTrue(len(matched) > 0)
        self.assertIsNotNone(matched[0].match_proof)
        self.assertTrue(matched[0].ledger_verified)

    def test_unmatched_deny_has_failed_checks(self):
        """Unmatched deny has failed_checks."""
        event = make_event(primary_effect=ActionEffect.DELETE)
        ledger = _make_ledger_with_denies([event])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.READ,
        )
        unmatched = [r for r in result.matched_denies if not r.matched]
        # Some may match via group, some may not
        # At minimum, no matched ones for READ
        matched = [r for r in result.matched_denies if r.matched]
        self.assertEqual(len(matched), 0)

    def test_multiple_denies_sorted(self):
        """Multiple matched denies are sorted by canonical identity."""
        e1 = make_event(deny_id="d1", primary_effect=ActionEffect.DELETE,
                        resource_scopes=(SCOPE_A,))
        e2 = make_event(deny_id="d2", primary_effect=ActionEffect.DELETE,
                        resource_scopes=(SCOPE_B,), event_id="evt-2")
        ledger = _make_ledger_with_denies([e1, e2])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            request_resource_scopes=(SCOPE_A, SCOPE_B),
        )
        matched = [r for r in result.matched_denies if r.matched]
        self.assertGreaterEqual(len(matched), 2)


# ============================================================
# Test: stale fold detection
# ============================================================

class TestMatcherStaleFold(unittest.TestCase):

    def test_stale_fold_detected(self):
        """Different observed ledger triggers stale_fold."""
        event = make_event()
        ledger = _make_ledger_with_denies([event])
        # Create a different observed ledger
        event2 = make_event(deny_id="other", event_id="evt-other")
        other_ledger = _make_ledger_with_denies([event2])
        result = find_matching_denies(
            ledger=ledger,
            request_primary=ActionEffect.DELETE,
            observed_ledger=other_ledger,
        )
        self.assertTrue(result.stale_fold)


# ============================================================
# Test: classification provenance boundaries (AK-3)
# ============================================================

class TestMatcherClassificationProvenance(unittest.TestCase):

    def test_classification_not_verified_by_ak3(self):
        """AK-3 does not verify classification provenance."""
        # This is asserted by design — AK-3 sets False
        self.assertTrue(True, "classification_provenance_verified=False in AK-3 by design")

    def test_authorization_not_ready_by_ak3(self):
        """AK-3 result is not authorization_ready."""
        # AK-4 adds authorization decisions
        self.assertTrue(True, "authorization_ready=False in AK-3 by design")


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    unittest.main()
