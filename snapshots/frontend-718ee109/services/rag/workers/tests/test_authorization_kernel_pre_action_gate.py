"""
GOAA Authorization Kernel AK-4 — Pre-Action Gate Unit Tests
============================================================
Framework: unittest (standard library). No pytest dependency.
All tests are pure — no file I/O, no network, no socket, no subprocess,
no Git, no database, no environment reads, no working-directory deps.

Covers: full happy path, every required-evidence-missing path, naive
decision_time, attestation/classification/policy-version/identity
mismatches, all snapshot-binding failure classes, ledger evidence
tip/count/decision_time/expiry binding, corrupted ledger, active deny,
matcher invalidity, every AuthorizationDecision outcome, empty-decision
fail-closed, digest stability & sensitivity, the unique authorization_ready
condition, and the honest AK-4 boundary (internal consistency never
implies real authority / freshness / TOCTOU resolution).
"""

from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timezone

from authorization_kernel.enums import (
    ActionEffect,
    AuthorizationDecision,
    DenyEventType,
    DenyOrigin,
    DenyScope,
    ResourceScopeType,
)
from authorization_kernel.resource_scope import TypedResourceScope
from authorization_kernel.action_request import ActionRequest
from authorization_kernel.authorization_snapshot import (
    AuthorizationSnapshot,
    compute_snapshot_hash,
)
from authorization_kernel.classification_attestation import compute_attestation_hash
from authorization_kernel.effect_classifier import (
    RecomputedClassification,
    build_classification_attestation,
)
from authorization_kernel.deny_event import DenyEvent
from authorization_kernel.deny_event_validation import DenyCreationRequest
from authorization_kernel.deny_ledger_state import DenyLedger, create_deny_entry
from authorization_kernel.policy_merge import merge_policy_decisions
from authorization_kernel.authorization_evidence import (
    AuthoritativeLedgerEvidence,
    PreActionGateContext,
    PreActionGateResult,
    ProviderEvidence,
    TrustedClassificationEvidence,
)
from authorization_kernel.pre_action_gate import (
    compute_evidence_digest,
    evaluate_pre_action_gate,
)


UTC = timezone.utc
T_EARLY = datetime(2026, 6, 15, 9, 0, 0, tzinfo=UTC)
T_EARLY2 = datetime(2026, 6, 15, 10, 0, 0, tzinfo=UTC)
T_PAST = datetime(2026, 6, 15, 11, 0, 0, tzinfo=UTC)
T_NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
T_FUTURE = datetime(2026, 6, 15, 13, 0, 0, tzinfo=UTC)

_D = AuthorizationDecision
_OMIT = object()


# ============================================================
# Fixture builders (pure, in-memory)
# ============================================================

def _scope(cid: str = "file:/x") -> TypedResourceScope:
    return TypedResourceScope(scope_type=ResourceScopeType.FILE_PATH, canonical_id=cid)


def _make_request(
    *,
    request_id: str = "req-1",
    task_id: str = "task-1",
    snapshot_id: str = "snap-1",
    actor_id: str = "actor-1",
    primary_effect: ActionEffect = ActionEffect.WRITE,
    secondary_effects=frozenset(),
    resource_scopes=(_scope(),),
    equivalent_action_groups=frozenset(),
    policy_version: str = "v1",
) -> ActionRequest:
    return ActionRequest(
        request_id=request_id,
        task_id=task_id,
        authorization_snapshot_id=snapshot_id,
        actor_id=actor_id,
        primary_effect=primary_effect,
        secondary_effects=secondary_effects,
        resource_scopes=resource_scopes,
        equivalent_action_groups=equivalent_action_groups,
        classification_policy_version=policy_version,
    )


def _make_snapshot(
    *,
    task_id: str = "task-1",
    snapshot_id: str = "snap-1",
    policy_version: str = "v1",
    allowed_effects=frozenset({ActionEffect.WRITE}),
    allowed_resource_scopes=(_scope(),),
    allowed_equivalent_groups=frozenset(),
    created_at: datetime = T_PAST,
    expires_at: datetime | None = T_FUTURE,
) -> AuthorizationSnapshot:
    base = AuthorizationSnapshot(
        snapshot_id=snapshot_id,
        task_id=task_id,
        policy_version=policy_version,
        created_at=created_at,
        expires_at=expires_at,
        allowed_effects=allowed_effects,
        allowed_resource_scopes=allowed_resource_scopes,
        allowed_equivalent_groups=allowed_equivalent_groups,
        snapshot_hash="",
    )
    return dataclasses.replace(base, snapshot_hash=compute_snapshot_hash(base))


def _make_recomputed(request: ActionRequest) -> RecomputedClassification:
    return RecomputedClassification(
        primary_effect=request.primary_effect,
        secondary_effects=request.secondary_effects,
        equivalent_action_groups=request.equivalent_action_groups,
    )


def _make_cls_ev(
    request: ActionRequest,
    attestation,
    recomputed: RecomputedClassification,
    *,
    issued_at: datetime = T_PAST,
    expires_at: datetime = T_FUTURE,
    provider=_OMIT,
) -> TrustedClassificationEvidence:
    if provider is _OMIT:
        provider = ProviderEvidence(
            provider_id="prov-1", issued_at=T_PAST, expires_at=T_FUTURE
        )
    return TrustedClassificationEvidence(
        subject_request_id=request.request_id,
        subject_task_id=request.task_id,
        classification_policy_version=attestation.classification_policy_version,
        attestation_hash=attestation.classification_attestation_hash,
        recomputed=recomputed,
        issued_at=issued_at,
        expires_at=expires_at,
        provider=provider,
    )


def _make_ledger_ev(
    ledger: DenyLedger,
    *,
    decision_time: datetime = T_NOW,
    issued_at: datetime = T_PAST,
    expires_at: datetime = T_FUTURE,
) -> AuthoritativeLedgerEvidence:
    tip = ledger.entries[-1].entry_hash if ledger.entries else None
    return AuthoritativeLedgerEvidence(
        ledger_tip_hash=tip,
        ledger_entry_count=len(ledger.entries),
        decision_time=decision_time,
        issued_at=issued_at,
        expires_at=expires_at,
    )


def _context(
    *,
    request=_OMIT,
    snapshot=_OMIT,
    attestation=_OMIT,
    recomputed=_OMIT,
    classification_evidence=_OMIT,
    ledger=_OMIT,
    ledger_evidence=_OMIT,
    decision_time=_OMIT,
    requires_human_approval: bool = False,
    human_approval_valid: bool = False,
) -> PreActionGateContext:
    request = _make_request() if request is _OMIT else request
    snapshot = _make_snapshot() if snapshot is _OMIT else snapshot
    if recomputed is _OMIT:
        recomputed = _make_recomputed(request)
    if attestation is _OMIT:
        attestation = build_classification_attestation(
            request, recomputed, request.classification_policy_version
        )
    if classification_evidence is _OMIT:
        classification_evidence = _make_cls_ev(request, attestation, recomputed)
    ledger = DenyLedger() if ledger is _OMIT else ledger
    if ledger_evidence is _OMIT:
        ledger_evidence = _make_ledger_ev(ledger)
    decision_time = T_NOW if decision_time is _OMIT else decision_time
    return PreActionGateContext(
        request=request,
        snapshot=snapshot,
        attestation=attestation,
        ledger=ledger,
        decision_time=decision_time,
        classification_evidence=classification_evidence,
        ledger_evidence=ledger_evidence,
        requires_human_approval=requires_human_approval,
        human_approval_valid=human_approval_valid,
    )


def _matching_deny_ledger(
    *,
    primary: ActionEffect = ActionEffect.WRITE,
    scope_cid: str = "file:/x",
    task_id: str = "task-1",
) -> DenyLedger:
    event = DenyEvent(
        event_id="ev-1",
        deny_id="deny-1",
        task_id=task_id,
        event_type=DenyEventType.DENY_CREATED,
        deny_scope=DenyScope.CURRENT_TASK,
        deny_origin=DenyOrigin.USER_DENIAL,
        primary_effect=primary,
        resource_scopes=(_scope(scope_cid),),
        actor="approver-1",
        occurred_at=T_PAST,
        expires_at=T_FUTURE,
        reason="blocked",
    )
    result = create_deny_entry(
        DenyLedger(), DenyCreationRequest(event=event, persistent=False, request_id=None)
    )
    assert result.appended, result.reason_code
    return result.ledger


def _corrupted_ledger() -> DenyLedger:
    good = _matching_deny_ledger()
    bad = dataclasses.replace(good.entries[0], entry_hash="0" * 64)
    return DenyLedger(entries=(bad,))


# ============================================================
# Happy path + result-shape
# ============================================================

class HappyPathTests(unittest.TestCase):
    def test_happy_path_allows_and_is_ready(self):
        result = evaluate_pre_action_gate(_context())
        self.assertEqual(result.decision, _D.ALLOW)
        self.assertTrue(result.authorization_ready)
        self.assertEqual(result.failed_checks, ())
        self.assertEqual(result.matched_deny_count, 0)

    def test_happy_path_digest_nonempty_and_64_hex(self):
        result = evaluate_pre_action_gate(_context())
        self.assertNotEqual(result.evidence_digest, "")
        self.assertEqual(len(result.evidence_digest), 64)
        int(result.evidence_digest, 16)  # raises if not hex

    def test_result_boundary_flags_always_false(self):
        result = evaluate_pre_action_gate(_context())
        self.assertFalse(result.provider_authority_proven)
        self.assertFalse(result.global_ledger_authority_proven)
        self.assertFalse(result.global_ledger_freshness_proven)
        self.assertFalse(result.toctou_resolved)
        self.assertFalse(result.real_execution_permission)

    def test_allow_does_not_emit_real_execution_permission(self):
        result = evaluate_pre_action_gate(_context())
        self.assertEqual(result.decision, _D.ALLOW)
        self.assertTrue(result.authorization_ready)
        # Even a clean ALLOW is NOT a production execution permission.
        self.assertFalse(result.real_execution_permission)
        self.assertFalse(result.toctou_resolved)

    def test_internal_consistency_does_not_prove_authority_or_freshness(self):
        # A fully self-consistent ALLOW still proves no real-world authority
        # or global ledger freshness.
        result = evaluate_pre_action_gate(_context())
        self.assertTrue(result.authorization_ready)
        self.assertFalse(result.provider_authority_proven)
        self.assertFalse(result.global_ledger_authority_proven)
        self.assertFalse(result.global_ledger_freshness_proven)


# ============================================================
# Missing required evidence -> OUT_OF_SCOPE
# ============================================================

class MissingEvidenceTests(unittest.TestCase):
    def test_classification_evidence_missing(self):
        result = evaluate_pre_action_gate(_context(classification_evidence=None))
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)
        self.assertFalse(result.authorization_ready)
        self.assertIn("classification_evidence_missing", result.failed_checks)

    def test_ledger_evidence_missing(self):
        result = evaluate_pre_action_gate(_context(ledger_evidence=None))
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)
        self.assertFalse(result.authorization_ready)
        self.assertIn("ledger_evidence_missing", result.failed_checks)

    def test_provider_evidence_missing(self):
        request = _make_request()
        recomputed = _make_recomputed(request)
        attestation = build_classification_attestation(request, recomputed, "v1")
        cls_ev = _make_cls_ev(request, attestation, recomputed, provider=None)
        result = evaluate_pre_action_gate(
            _context(request=request, attestation=attestation, recomputed=recomputed,
                     classification_evidence=cls_ev)
        )
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)
        self.assertFalse(result.authorization_ready)
        self.assertIn("provider_evidence_missing", result.failed_checks)

    def test_all_evidence_missing_fails_closed(self):
        result = evaluate_pre_action_gate(
            _context(classification_evidence=None, ledger_evidence=None)
        )
        self.assertFalse(result.authorization_ready)
        self.assertNotEqual(result.decision, _D.ALLOW)


# ============================================================
# decision_time / structural
# ============================================================

class DecisionTimeTests(unittest.TestCase):
    def test_naive_decision_time_fails_closed(self):
        naive = datetime(2026, 6, 15, 12, 0, 0)  # no tzinfo
        result = evaluate_pre_action_gate(_context(decision_time=naive))
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertFalse(result.authorization_ready)
        self.assertEqual(result.evidence_digest, "")
        self.assertIn("decision_time_not_aware", result.failed_checks)

    def test_non_context_input_fails_closed(self):
        result = evaluate_pre_action_gate("not-a-context")  # type: ignore[arg-type]
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertFalse(result.authorization_ready)
        self.assertIn("context_type_invalid", result.failed_checks)

    def test_internal_error_fails_closed_without_leak(self):
        # A type-valid-but-broken ledger forces an exception inside the gate.
        broken_ledger = DenyLedger(entries=("not-an-entry",))  # type: ignore[arg-type]
        ledger_ev = AuthoritativeLedgerEvidence(
            ledger_tip_hash="x", ledger_entry_count=1,
            decision_time=T_NOW, issued_at=T_PAST, expires_at=T_FUTURE,
        )
        result = evaluate_pre_action_gate(
            _context(ledger=broken_ledger, ledger_evidence=ledger_ev)
        )
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)
        self.assertFalse(result.authorization_ready)
        self.assertEqual(result.failed_checks, ("internal_error_fail_closed",))


# ============================================================
# Classification / attestation conflicts -> POLICY_CONFLICT
# ============================================================

class ClassificationConflictTests(unittest.TestCase):
    def test_attestation_hash_invalid(self):
        ctx = _context()
        bad_att = dataclasses.replace(
            ctx.attestation, classification_attestation_hash="0" * 64
        )
        bad_ce = dataclasses.replace(ctx.classification_evidence, attestation_hash="0" * 64)
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, attestation=bad_att, classification_evidence=bad_ce)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("attestation_hash_invalid", result.failed_checks)
        self.assertFalse(result.authorization_ready)

    def test_classification_mismatch(self):
        request = _make_request()
        # Build an attestation where declared != recomputed but hash is valid.
        base = dataclasses.replace(
            build_classification_attestation(request, _make_recomputed(request), "v1"),
            recomputed_primary_effect=ActionEffect.DELETE,
            classification_attestation_hash="",
        )
        att = dataclasses.replace(
            base, classification_attestation_hash=compute_attestation_hash(base)
        )
        recomputed = RecomputedClassification(primary_effect=ActionEffect.DELETE)
        ce = _make_cls_ev(request, att, recomputed)
        result = evaluate_pre_action_gate(
            _context(request=request, attestation=att, recomputed=recomputed,
                     classification_evidence=ce)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("classification_mismatch", result.failed_checks)

    def test_request_attestation_policy_version_mismatch(self):
        request = _make_request(policy_version="v1")
        recomputed = _make_recomputed(request)
        att = build_classification_attestation(request, recomputed, "v2")
        ce = _make_cls_ev(request, att, recomputed)  # ce version = att version = v2
        result = evaluate_pre_action_gate(
            _context(request=request, attestation=att, recomputed=recomputed,
                     classification_evidence=ce)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("request_attestation_policy_version_mismatch", result.failed_checks)

    def test_classification_evidence_policy_version_mismatch(self):
        ctx = _context()
        bad_ce = dataclasses.replace(
            ctx.classification_evidence, classification_policy_version="v-other"
        )
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, classification_evidence=bad_ce)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn(
            "classification_evidence_policy_version_mismatch", result.failed_checks
        )

    def test_classification_evidence_request_mismatch(self):
        ctx = _context()
        bad_ce = dataclasses.replace(
            ctx.classification_evidence, subject_request_id="req-other"
        )
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, classification_evidence=bad_ce)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("classification_evidence_request_mismatch", result.failed_checks)

    def test_classification_evidence_task_mismatch(self):
        ctx = _context()
        bad_ce = dataclasses.replace(
            ctx.classification_evidence, subject_task_id="task-other"
        )
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, classification_evidence=bad_ce)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("classification_evidence_task_mismatch", result.failed_checks)

    def test_classification_evidence_hash_mismatch(self):
        ctx = _context()
        bad_ce = dataclasses.replace(
            ctx.classification_evidence, attestation_hash="a" * 64
        )
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, classification_evidence=bad_ce)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("classification_evidence_hash_mismatch", result.failed_checks)

    def test_classification_evidence_recomputed_mismatch(self):
        ctx = _context()
        bad_ce = dataclasses.replace(
            ctx.classification_evidence,
            recomputed=RecomputedClassification(primary_effect=ActionEffect.DELETE),
        )
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, classification_evidence=bad_ce)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn(
            "classification_evidence_recomputed_mismatch", result.failed_checks
        )


# ============================================================
# Classification / provider validity windows -> OUT_OF_SCOPE
# ============================================================

class EvidenceWindowTests(unittest.TestCase):
    def test_classification_evidence_expired(self):
        ctx = _context()
        expired_ce = dataclasses.replace(
            ctx.classification_evidence, issued_at=T_EARLY, expires_at=T_EARLY2
        )
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, classification_evidence=expired_ce)
        )
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)
        self.assertIn(
            "classification_evidence_outside_validity_window", result.failed_checks
        )

    def test_classification_evidence_window_boundary_is_valid(self):
        # decision_time exactly equals expires_at -> still valid (inclusive).
        request = _make_request()
        recomputed = _make_recomputed(request)
        att = build_classification_attestation(request, recomputed, "v1")
        ce = _make_cls_ev(request, att, recomputed, issued_at=T_PAST, expires_at=T_NOW)
        result = evaluate_pre_action_gate(
            _context(request=request, attestation=att, recomputed=recomputed,
                     classification_evidence=ce, decision_time=T_NOW)
        )
        self.assertEqual(result.decision, _D.ALLOW)
        self.assertTrue(result.authorization_ready)

    def test_provider_evidence_expired(self):
        ctx = _context()
        expired_provider = ProviderEvidence(
            provider_id="prov-1", issued_at=T_EARLY, expires_at=T_EARLY2
        )
        bad_ce = dataclasses.replace(ctx.classification_evidence, provider=expired_provider)
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, classification_evidence=bad_ce)
        )
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)
        self.assertIn(
            "provider_evidence_outside_validity_window", result.failed_checks
        )


# ============================================================
# Snapshot binding failures
# ============================================================

class SnapshotBindingTests(unittest.TestCase):
    def test_task_id_mismatch_policy_conflict(self):
        snap = _make_snapshot(task_id="task-other")
        result = evaluate_pre_action_gate(_context(snapshot=snap))
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("snapshot:task_id mismatch", result.failed_checks)

    def test_snapshot_id_mismatch_policy_conflict(self):
        snap = _make_snapshot(snapshot_id="snap-other")
        result = evaluate_pre_action_gate(_context(snapshot=snap))
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("snapshot:snapshot_id mismatch", result.failed_checks)

    def test_policy_version_mismatch_policy_conflict(self):
        snap = _make_snapshot(policy_version="v2")
        result = evaluate_pre_action_gate(_context(snapshot=snap))
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("snapshot:policy_version mismatch", result.failed_checks)

    def test_snapshot_hash_invalid_policy_conflict(self):
        ctx = _context()
        tampered = dataclasses.replace(ctx.snapshot, snapshot_hash="0" * 64)
        result = evaluate_pre_action_gate(dataclasses.replace(ctx, snapshot=tampered))
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("snapshot:snapshot_hash invalid", result.failed_checks)

    def test_snapshot_expired_deny(self):
        snap = _make_snapshot(created_at=T_EARLY, expires_at=T_EARLY2)
        result = evaluate_pre_action_gate(_context(snapshot=snap))
        self.assertEqual(result.decision, _D.DENY)
        self.assertIn("snapshot:snapshot expired", result.failed_checks)

    def test_effects_exceed_allowed_deny(self):
        request = _make_request(primary_effect=ActionEffect.DELETE)
        snap = _make_snapshot(allowed_effects=frozenset({ActionEffect.WRITE}))
        result = evaluate_pre_action_gate(_context(request=request, snapshot=snap))
        self.assertEqual(result.decision, _D.DENY)
        self.assertIn("snapshot:effects exceed allowed_effects", result.failed_checks)

    def test_resource_scopes_exceed_allowed_deny(self):
        request = _make_request(resource_scopes=(_scope("file:/y"),))
        snap = _make_snapshot(allowed_resource_scopes=(_scope("file:/x"),))
        result = evaluate_pre_action_gate(_context(request=request, snapshot=snap))
        self.assertEqual(result.decision, _D.DENY)
        self.assertIn(
            "snapshot:resource_scopes exceed allowed_resource_scopes",
            result.failed_checks,
        )

    def test_groups_exceed_allowed_deny(self):
        request = _make_request(equivalent_action_groups=frozenset({"g1"}))
        recomputed = RecomputedClassification(
            primary_effect=request.primary_effect,
            equivalent_action_groups=frozenset({"g1"}),
        )
        snap = _make_snapshot(allowed_equivalent_groups=frozenset())
        result = evaluate_pre_action_gate(
            _context(request=request, recomputed=recomputed, snapshot=snap)
        )
        self.assertEqual(result.decision, _D.DENY)
        self.assertIn(
            "snapshot:groups exceed allowed_equivalent_groups", result.failed_checks
        )


# ============================================================
# Ledger evidence binding
# ============================================================

class LedgerEvidenceBindingTests(unittest.TestCase):
    def test_tip_mismatch_policy_conflict(self):
        # Non-empty ledger; evidence claims the wrong tip hash.
        ledger = _matching_deny_ledger(primary=ActionEffect.DEPLOY)
        good_le = _make_ledger_ev(ledger)
        wrong_le = dataclasses.replace(good_le, ledger_tip_hash="a" * 64)
        result = evaluate_pre_action_gate(
            _context(ledger=ledger, ledger_evidence=wrong_le)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("ledger_evidence_tip_mismatch", result.failed_checks)

    def test_ledger_evidence_construction_rejects_empty_count_with_tip(self):
        # Model-level invariant: empty ledger must have tip None.
        with self.assertRaises(ValueError):
            AuthoritativeLedgerEvidence(
                ledger_tip_hash="f" * 64, ledger_entry_count=0,
                decision_time=T_NOW, issued_at=T_PAST, expires_at=T_FUTURE,
            )

    def test_count_mismatch_policy_conflict(self):
        ledger = _matching_deny_ledger(primary=ActionEffect.DEPLOY)
        good_le = _make_ledger_ev(ledger)
        wrong_le = dataclasses.replace(good_le, ledger_entry_count=99)
        result = evaluate_pre_action_gate(
            _context(ledger=ledger, ledger_evidence=wrong_le)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("ledger_evidence_count_mismatch", result.failed_checks)

    def test_decision_time_mismatch_policy_conflict(self):
        ctx = _context()
        wrong_le = dataclasses.replace(ctx.ledger_evidence, decision_time=T_FUTURE)
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, ledger_evidence=wrong_le)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)
        self.assertIn("ledger_evidence_decision_time_mismatch", result.failed_checks)

    def test_ledger_evidence_expired_out_of_scope(self):
        ctx = _context()
        expired_le = dataclasses.replace(
            ctx.ledger_evidence, issued_at=T_EARLY, expires_at=T_EARLY2
        )
        result = evaluate_pre_action_gate(
            dataclasses.replace(ctx, ledger_evidence=expired_le)
        )
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)
        self.assertIn(
            "ledger_evidence_outside_validity_window", result.failed_checks
        )


# ============================================================
# Ledger integrity / matcher / denies
# ============================================================

class LedgerAndMatcherTests(unittest.TestCase):
    def test_corrupted_ledger_integrity_invalid(self):
        ledger = _corrupted_ledger()
        le = AuthoritativeLedgerEvidence(
            ledger_tip_hash="0" * 64, ledger_entry_count=1,
            decision_time=T_NOW, issued_at=T_PAST, expires_at=T_FUTURE,
        )
        result = evaluate_pre_action_gate(_context(ledger=ledger, ledger_evidence=le))
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)
        self.assertFalse(result.authorization_ready)
        self.assertIn("ledger_integrity_invalid", result.failed_checks)

    def test_corrupted_ledger_marks_matcher_invalid(self):
        ledger = _corrupted_ledger()
        le = AuthoritativeLedgerEvidence(
            ledger_tip_hash="0" * 64, ledger_entry_count=1,
            decision_time=T_NOW, issued_at=T_PAST, expires_at=T_FUTURE,
        )
        result = evaluate_pre_action_gate(_context(ledger=ledger, ledger_evidence=le))
        self.assertIn("matcher_invalid", result.failed_checks)

    def test_active_deny_matched_denies(self):
        ledger = _matching_deny_ledger(primary=ActionEffect.WRITE)
        le = _make_ledger_ev(ledger)
        result = evaluate_pre_action_gate(_context(ledger=ledger, ledger_evidence=le))
        self.assertEqual(result.decision, _D.DENY)
        self.assertFalse(result.authorization_ready)
        self.assertGreaterEqual(result.matched_deny_count, 1)
        self.assertIn("active_deny_matched", result.failed_checks)

    def test_non_matching_deny_still_allows(self):
        # A deny for an unrelated effect must not block this request.
        ledger = _matching_deny_ledger(primary=ActionEffect.DEPLOY)
        le = _make_ledger_ev(ledger)
        result = evaluate_pre_action_gate(_context(ledger=ledger, ledger_evidence=le))
        self.assertEqual(result.decision, _D.ALLOW)
        self.assertTrue(result.authorization_ready)
        self.assertEqual(result.matched_deny_count, 0)


# ============================================================
# Precedence + approval routing + every outcome
# ============================================================

class DecisionOutcomeTests(unittest.TestCase):
    def test_policy_conflict_precedes_deny(self):
        # Active deny (DENY) AND a policy-version conflict (POLICY_CONFLICT).
        ledger = _matching_deny_ledger(primary=ActionEffect.WRITE)
        le = _make_ledger_ev(ledger)
        snap = _make_snapshot(policy_version="v2")  # bind policy_version conflict
        result = evaluate_pre_action_gate(
            _context(snapshot=snap, ledger=ledger, ledger_evidence=le)
        )
        self.assertEqual(result.decision, _D.POLICY_CONFLICT)

    def test_requires_approval_when_required_and_absent(self):
        result = evaluate_pre_action_gate(
            _context(requires_human_approval=True, human_approval_valid=False)
        )
        self.assertEqual(result.decision, _D.REQUIRES_APPROVAL)
        self.assertFalse(result.authorization_ready)
        self.assertIn("human_approval_required", result.failed_checks)

    def test_requires_approval_satisfied_allows(self):
        result = evaluate_pre_action_gate(
            _context(requires_human_approval=True, human_approval_valid=True)
        )
        self.assertEqual(result.decision, _D.ALLOW)
        self.assertTrue(result.authorization_ready)

    def test_deny_precedes_requires_approval(self):
        ledger = _matching_deny_ledger(primary=ActionEffect.WRITE)
        le = _make_ledger_ev(ledger)
        result = evaluate_pre_action_gate(
            _context(ledger=ledger, ledger_evidence=le,
                     requires_human_approval=True, human_approval_valid=False)
        )
        self.assertEqual(result.decision, _D.DENY)

    def test_out_of_scope_precedes_requires_approval(self):
        result = evaluate_pre_action_gate(
            _context(classification_evidence=None,
                     requires_human_approval=True, human_approval_valid=False)
        )
        self.assertEqual(result.decision, _D.OUT_OF_SCOPE)

    def test_all_five_outcomes_reachable(self):
        cases = {
            _D.ALLOW: _context(),
            _D.REQUIRES_APPROVAL: _context(
                requires_human_approval=True, human_approval_valid=False
            ),
            _D.OUT_OF_SCOPE: _context(classification_evidence=None),
            _D.DENY: _context(
                ledger=_matching_deny_ledger(primary=ActionEffect.WRITE),
                ledger_evidence=_make_ledger_ev(
                    _matching_deny_ledger(primary=ActionEffect.WRITE)
                ),
            ),
            _D.POLICY_CONFLICT: _context(snapshot=_make_snapshot(task_id="x")),
        }
        for expected, ctx in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(evaluate_pre_action_gate(ctx).decision, expected)


# ============================================================
# Reused merge semantics
# ============================================================

class MergeReuseTests(unittest.TestCase):
    def test_empty_decision_tuple_is_out_of_scope(self):
        # Spec: empty decision set must fail closed (never ALLOW).
        self.assertEqual(merge_policy_decisions(()), _D.OUT_OF_SCOPE)

    def test_merge_precedence_table(self):
        self.assertEqual(
            merge_policy_decisions((_D.ALLOW, _D.DENY, _D.POLICY_CONFLICT)),
            _D.POLICY_CONFLICT,
        )
        self.assertEqual(merge_policy_decisions((_D.ALLOW, _D.DENY)), _D.DENY)
        self.assertEqual(
            merge_policy_decisions((_D.ALLOW, _D.OUT_OF_SCOPE)), _D.OUT_OF_SCOPE
        )
        self.assertEqual(
            merge_policy_decisions((_D.ALLOW, _D.REQUIRES_APPROVAL)),
            _D.REQUIRES_APPROVAL,
        )
        self.assertEqual(merge_policy_decisions((_D.ALLOW,)), _D.ALLOW)


# ============================================================
# Evidence digest
# ============================================================

class EvidenceDigestTests(unittest.TestCase):
    def test_digest_deterministic(self):
        ctx = _context()
        self.assertEqual(
            compute_evidence_digest(ctx), compute_evidence_digest(ctx)
        )

    def test_digest_stable_across_set_like_ordering(self):
        scopes_ab = (_scope("file:/a"), _scope("file:/b"))
        scopes_ba = (_scope("file:/b"), _scope("file:/a"))
        allowed = (_scope("file:/a"), _scope("file:/b"))
        req_ab = _make_request(resource_scopes=scopes_ab)
        req_ba = _make_request(resource_scopes=scopes_ba)
        snap = _make_snapshot(allowed_resource_scopes=allowed)
        ctx_ab = _context(request=req_ab, snapshot=snap)
        ctx_ba = _context(request=req_ba, snapshot=snap)
        self.assertEqual(
            compute_evidence_digest(ctx_ab), compute_evidence_digest(ctx_ba)
        )

    def test_digest_changes_on_security_field_change(self):
        ctx_a = _context(request=_make_request(actor_id="actor-1"))
        ctx_b = _context(request=_make_request(actor_id="actor-2"))
        self.assertNotEqual(
            compute_evidence_digest(ctx_a), compute_evidence_digest(ctx_b)
        )

    def test_digest_changes_on_decision_time_change(self):
        ctx_a = _context()
        # Rebuild ledger evidence to keep decision_time binding consistent.
        ctx_b = _context(
            decision_time=T_FUTURE,
            ledger_evidence=_make_ledger_ev(DenyLedger(), decision_time=T_FUTURE),
        )
        self.assertNotEqual(
            compute_evidence_digest(ctx_a), compute_evidence_digest(ctx_b)
        )

    def test_result_digest_matches_helper_for_allow(self):
        ctx = _context()
        result = evaluate_pre_action_gate(ctx)
        self.assertEqual(result.evidence_digest, compute_evidence_digest(ctx))


# ============================================================
# authorization_ready unique condition
# ============================================================

class AuthorizationReadyTests(unittest.TestCase):
    def test_ready_only_true_for_clean_allow(self):
        not_ready_contexts = {
            "missing_classification": _context(classification_evidence=None),
            "missing_ledger": _context(ledger_evidence=None),
            "naive_time": _context(decision_time=datetime(2026, 6, 15, 12)),
            "binding_conflict": _context(snapshot=_make_snapshot(task_id="x")),
            "active_deny": _context(
                ledger=_matching_deny_ledger(primary=ActionEffect.WRITE),
                ledger_evidence=_make_ledger_ev(
                    _matching_deny_ledger(primary=ActionEffect.WRITE)
                ),
            ),
            "requires_approval": _context(
                requires_human_approval=True, human_approval_valid=False
            ),
        }
        for name, ctx in not_ready_contexts.items():
            with self.subTest(case=name):
                self.assertFalse(evaluate_pre_action_gate(ctx).authorization_ready)
        # Positive control.
        self.assertTrue(evaluate_pre_action_gate(_context()).authorization_ready)

    def test_result_invariant_blocks_inconsistent_ready(self):
        # The result model itself refuses a ready flag without a clean ALLOW.
        with self.assertRaises(ValueError):
            PreActionGateResult(
                decision=_D.DENY, authorization_ready=True, evidence_digest="x"
            )
        with self.assertRaises(ValueError):
            PreActionGateResult(
                decision=_D.ALLOW, authorization_ready=True, evidence_digest=""
            )

    def test_result_rejects_true_boundary_flags(self):
        with self.assertRaises(ValueError):
            PreActionGateResult(decision=_D.ALLOW, real_execution_permission=True)


# ============================================================
# Honest boundary semantics
# ============================================================

class BoundarySemanticsTests(unittest.TestCase):
    def test_toctou_never_claimed_resolved(self):
        for ctx in (
            _context(),
            _context(classification_evidence=None),
            _context(ledger=_matching_deny_ledger(primary=ActionEffect.WRITE),
                     ledger_evidence=_make_ledger_ev(
                         _matching_deny_ledger(primary=ActionEffect.WRITE))),
        ):
            with self.subTest():
                self.assertFalse(evaluate_pre_action_gate(ctx).toctou_resolved)

    def test_valid_hash_does_not_auto_grant_authority(self):
        # The attestation hash is internally valid in the happy path, yet the
        # gate never upgrades that into provider/global authority.
        result = evaluate_pre_action_gate(_context())
        self.assertTrue(result.authorization_ready)
        self.assertFalse(result.provider_authority_proven)
        self.assertFalse(result.global_ledger_authority_proven)
        self.assertFalse(result.global_ledger_freshness_proven)


if __name__ == "__main__":
    unittest.main()
