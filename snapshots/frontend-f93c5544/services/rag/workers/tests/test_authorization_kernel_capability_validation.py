"""
GOAA Authorization Kernel AK-5A — Capability Grant Candidate Factory Tests
==========================================================================
Framework: unittest (standard library). No pytest, no third-party deps.
All tests are pure — no file I/O, no network, no subprocess, no clock reads.

Covers the AK-5A fail-closed attack model: wrong-type context, wrong-type
gate_result, post_init-bypassing malformed results, forged
authorization_ready, foreign / mismatched gate_result, evidence-digest
mismatch, tampered/replaced context, real-DENY context + forged ALLOW
result, active deny, non-zero matched_deny_count, non-empty failed_checks,
naive decision_time, missing provider / ledger evidence, unbounded expiry,
requested-expiry-before-decision-time, requested-expiry-over-derived-max,
and internal exceptions. Every failure path yields ok=False, candidate=None,
non-empty failed_checks, and no raw-exception leakage. Also exercises the
clean-ALLOW happy path, gate re-evaluation, evidence-digest re-derivation,
and every expiry bound.
"""

from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

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
from authorization_kernel.effect_classifier import (
    RecomputedClassification,
    build_classification_attestation,
)
from authorization_kernel.deny_event import DenyEvent
from authorization_kernel.deny_event_validation import DenyCreationRequest
from authorization_kernel.deny_ledger_state import DenyLedger, create_deny_entry
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
from authorization_kernel.capability_models import (
    CapabilityGrantCandidate,
    verify_candidate_digest,
)
from authorization_kernel.capability_validation import (
    CandidateExpiry,
    CapabilityGrantBuildResult,
    build_capability_grant_candidate,
    derive_candidate_expiry,
)


UTC = timezone.utc
T_PAST = datetime(2026, 6, 15, 11, 0, 0, tzinfo=UTC)
T_NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
T_FUTURE = datetime(2026, 6, 15, 13, 0, 0, tzinfo=UTC)
T_LATE = datetime(2026, 6, 15, 14, 0, 0, tzinfo=UTC)

_D = AuthorizationDecision
_OMIT = object()

# The set of stable, opaque check codes the factory and expiry deriver may
# emit. Used to prove no raw exception text ever leaks into failed_checks.
_KNOWN_CODES = {
    "context_type_invalid",
    "gate_result_type_invalid",
    "requested_expiry_type_invalid",
    "gate_result_not_allow",
    "gate_result_not_ready",
    "gate_result_has_failed_checks",
    "gate_result_deny_matched",
    "gate_result_evidence_digest_empty",
    "gate_result_boundary_flags_invalid",
    "gate_reevaluation_not_clean_allow",
    "evidence_digest_empty",
    "reevaluation_digest_mismatch",
    "evidence_digest_mismatch",
    "expiry_bound_missing",
    "expiry_bound_before_decision_time",
    "decision_time_not_aware",
    "requested_expiry_not_aware",
    "requested_expiry_before_decision_time",
    "requested_expiry_exceeds_derived_max",
    "internal_error_fail_closed",
}


# ============================================================
# Fixture builders (pure, in-memory) — mirror the AK-4 gate tests
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
    resource_scopes=(_scope(),),
    requested_tool: str = "editor",
    policy_version: str = "v1",
) -> ActionRequest:
    return ActionRequest(
        request_id=request_id,
        task_id=task_id,
        authorization_snapshot_id=snapshot_id,
        actor_id=actor_id,
        primary_effect=primary_effect,
        resource_scopes=resource_scopes,
        requested_tool=requested_tool,
        classification_policy_version=policy_version,
    )


def _make_snapshot(
    *,
    task_id: str = "task-1",
    snapshot_id: str = "snap-1",
    policy_version: str = "v1",
    allowed_effects=frozenset({ActionEffect.WRITE}),
    allowed_resource_scopes=(_scope(),),
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
    # Auto-built ledger evidence always carries an aware decision_time; tests
    # that exercise a naive context decision_time still need valid evidence.
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
    )


def _clean_allow():
    """Return (context, clean-ALLOW gate_result)."""
    ctx = _context()
    result = evaluate_pre_action_gate(ctx)
    assert result.authorization_ready, result.failed_checks
    return ctx, result


def _matching_deny_ledger() -> DenyLedger:
    event = DenyEvent(
        event_id="ev-1",
        deny_id="deny-1",
        task_id="task-1",
        event_type=DenyEventType.DENY_CREATED,
        deny_scope=DenyScope.CURRENT_TASK,
        deny_origin=DenyOrigin.USER_DENIAL,
        primary_effect=ActionEffect.WRITE,
        resource_scopes=(_scope("file:/x"),),
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


def _forged_allow(evidence_digest: str) -> PreActionGateResult:
    """A *claimed* clean-ALLOW result with an arbitrary evidence digest."""
    return PreActionGateResult(
        decision=_D.ALLOW,
        authorization_ready=True,
        failed_checks=(),
        evidence_digest=evidence_digest,
        matched_deny_count=0,
    )


def _malformed_result(**attrs) -> PreActionGateResult:
    """A PreActionGateResult built via object.__new__, bypassing __post_init__.

    Lets tests fabricate states the normal invariants forbid (e.g. ready=True
    with non-empty failed_checks) to prove the factory still fails closed.
    """
    obj = object.__new__(PreActionGateResult)
    defaults = dict(
        decision=_D.ALLOW,
        authorization_ready=True,
        failed_checks=(),
        evidence_digest="x" * 64,
        matched_deny_count=0,
        provider_authority_proven=False,
        global_ledger_authority_proven=False,
        global_ledger_freshness_proven=False,
        toctou_resolved=False,
        real_execution_permission=False,
    )
    defaults.update(attrs)
    for k, v in defaults.items():
        object.__setattr__(obj, k, v)
    return obj


class _ExplodingDatetime(datetime):
    """An aware datetime whose ordering comparisons raise — to drive the
    factory's internal-exception fail-closed path."""

    def __lt__(self, other):
        raise RuntimeError("boom")

    def __gt__(self, other):
        raise RuntimeError("boom")

    def __le__(self, other):
        raise RuntimeError("boom")

    def __ge__(self, other):
        raise RuntimeError("boom")


def _assert_failed(self, res: CapabilityGrantBuildResult, *expected_codes: str):
    self.assertFalse(res.ok)
    self.assertIsNone(res.candidate)
    self.assertTrue(res.failed_checks)
    self.assertIsNone(res.expiry_bound_source)
    # No raw exception text or unknown codes leaked.
    for code in res.failed_checks:
        self.assertIn(code, _KNOWN_CODES, f"leaked/unknown code: {code!r}")
        self.assertNotIn("boom", code)
        self.assertNotIn("Traceback", code)
    for code in expected_codes:
        self.assertIn(code, res.failed_checks)


# ============================================================
# Happy path
# ============================================================

class HappyPathTests(unittest.TestCase):
    def test_clean_allow_builds_candidate(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(ctx, result)
        self.assertTrue(res.ok)
        self.assertIsInstance(res.candidate, CapabilityGrantCandidate)
        self.assertEqual(res.failed_checks, ())

    def test_candidate_digest_is_valid(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(ctx, result)
        self.assertTrue(verify_candidate_digest(res.candidate))

    def test_candidate_fields_derived_from_context(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(ctx, result)
        c = res.candidate
        self.assertEqual(c.request_id, ctx.request.request_id)
        self.assertEqual(c.task_id, ctx.request.task_id)
        self.assertEqual(c.actor_id, ctx.request.actor_id)
        self.assertEqual(c.primary_effect, ctx.request.primary_effect)
        self.assertEqual(c.snapshot_id, ctx.snapshot.snapshot_id)
        self.assertEqual(c.policy_version, ctx.snapshot.policy_version)
        self.assertEqual(
            c.classification_attestation_hash,
            ctx.attestation.classification_attestation_hash,
        )

    def test_evidence_digest_recomputed_and_bound(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(ctx, result)
        self.assertEqual(res.candidate.evidence_digest, compute_evidence_digest(ctx))
        self.assertEqual(res.candidate.evidence_digest, result.evidence_digest)

    def test_issued_at_not_before_equal_decision_time(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(ctx, result)
        self.assertEqual(res.candidate.issued_at, ctx.decision_time)
        self.assertEqual(res.candidate.not_before, ctx.decision_time)
        self.assertEqual(res.candidate.issued_at, res.candidate.not_before)

    def test_requested_tool_recorded(self):
        request = _make_request(requested_tool="custom-shell")
        ctx = _context(request=request)
        result = evaluate_pre_action_gate(ctx)
        res = build_capability_grant_candidate(ctx, result)
        self.assertEqual(res.candidate.requested_tool, "custom-shell")

    def test_expires_at_always_bounded_and_not_none(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(ctx, result)
        self.assertIsNotNone(res.candidate.expires_at)
        self.assertIsInstance(res.candidate.expires_at, datetime)
        self.assertLessEqual(res.candidate.expires_at, T_FUTURE)

    def test_expiry_bound_source_reported_on_result(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(ctx, result)
        self.assertIn(
            res.expiry_bound_source,
            {"snapshot", "classification_evidence", "provider_evidence", "ledger_evidence"},
        )

    def test_candidate_has_no_grant_id_or_runtime_fields(self):
        ctx, result = _clean_allow()
        c = build_capability_grant_candidate(ctx, result).candidate
        for forbidden in (
            "grant_id",
            "status",
            "real_execution_permission",
            "runtime_enforced",
            "consumed_at",
            "revoked_at",
            "expiry_bound_source",
        ):
            self.assertFalse(hasattr(c, forbidden))


# ============================================================
# Type-check fail-closed
# ============================================================

class TypeCheckTests(unittest.TestCase):
    def test_wrong_type_context(self):
        _, result = _clean_allow()
        res = build_capability_grant_candidate("not-a-context", result)
        _assert_failed(self, res, "context_type_invalid")

    def test_none_context(self):
        _, result = _clean_allow()
        res = build_capability_grant_candidate(None, result)
        _assert_failed(self, res, "context_type_invalid")

    def test_wrong_type_gate_result(self):
        ctx, _ = _clean_allow()
        res = build_capability_grant_candidate(ctx, "not-a-result")
        _assert_failed(self, res, "gate_result_type_invalid")

    def test_none_gate_result(self):
        ctx, _ = _clean_allow()
        res = build_capability_grant_candidate(ctx, None)
        _assert_failed(self, res, "gate_result_type_invalid")

    def test_requested_expiry_wrong_type(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(ctx, result, requested_expires_at="soon")
        _assert_failed(self, res, "requested_expiry_type_invalid")


# ============================================================
# Non-clean-ALLOW claimed result
# ============================================================

class ClaimedResultTests(unittest.TestCase):
    def test_decision_not_allow(self):
        ctx, _ = _clean_allow()
        denied = PreActionGateResult(decision=_D.DENY, authorization_ready=False)
        res = build_capability_grant_candidate(ctx, denied)
        _assert_failed(self, res, "gate_result_not_allow")

    def test_allow_but_not_ready(self):
        ctx, _ = _clean_allow()
        not_ready = PreActionGateResult(decision=_D.ALLOW, authorization_ready=False)
        res = build_capability_grant_candidate(ctx, not_ready)
        _assert_failed(self, res, "gate_result_not_ready")

    def test_malformed_result_with_failed_checks(self):
        ctx, real = _clean_allow()
        bad = _malformed_result(
            evidence_digest=real.evidence_digest, failed_checks=("snapshot:expired",)
        )
        res = build_capability_grant_candidate(ctx, bad)
        _assert_failed(self, res, "gate_result_has_failed_checks")

    def test_malformed_result_with_deny_count(self):
        ctx, real = _clean_allow()
        bad = _malformed_result(evidence_digest=real.evidence_digest, matched_deny_count=2)
        res = build_capability_grant_candidate(ctx, bad)
        _assert_failed(self, res, "gate_result_deny_matched")

    def test_malformed_result_with_empty_digest(self):
        ctx, _ = _clean_allow()
        bad = _malformed_result(evidence_digest="")
        res = build_capability_grant_candidate(ctx, bad)
        _assert_failed(self, res, "gate_result_evidence_digest_empty")


# ============================================================
# AK-4 boundary-flag forgery (the five proofs must stay False)
# ============================================================

class BoundaryFlagTests(unittest.TestCase):
    """A malformed gate_result that asserts ANY of the five AK-4 boundary
    proofs must be rejected. These results are built via object.__new__ to
    bypass AK-4's __post_init__ (which would itself forbid the True flag), so
    the factory cannot lean on that invariant and must re-check independently.
    Each result is otherwise a perfectly bound clean ALLOW (real evidence
    digest), proving the boundary check — not some other gate — is what fails.
    """

    def _attack(self, **flag):
        ctx, real = _clean_allow()
        bad = _malformed_result(evidence_digest=real.evidence_digest, **flag)
        res = build_capability_grant_candidate(ctx, bad)
        _assert_failed(self, res, "gate_result_boundary_flags_invalid")

    def test_provider_authority_proven_true_rejected(self):
        self._attack(provider_authority_proven=True)

    def test_global_ledger_authority_proven_true_rejected(self):
        self._attack(global_ledger_authority_proven=True)

    def test_global_ledger_freshness_proven_true_rejected(self):
        self._attack(global_ledger_freshness_proven=True)

    def test_toctou_resolved_true_rejected(self):
        self._attack(toctou_resolved=True)

    def test_real_execution_permission_true_rejected(self):
        self._attack(real_execution_permission=True)

    def test_truthy_nonbool_boundary_flag_rejected(self):
        # Strict identity (is False) means a truthy non-bool also fails closed.
        self._attack(real_execution_permission=1)


# ============================================================
# Forged / foreign / mismatched results
# ============================================================

class ForgedResultTests(unittest.TestCase):
    def test_forged_allow_with_wrong_digest(self):
        ctx, _ = _clean_allow()
        forged = _forged_allow("a" * 64)
        res = build_capability_grant_candidate(ctx, forged)
        _assert_failed(self, res, "evidence_digest_mismatch")

    def test_foreign_clean_allow_from_other_context(self):
        # A genuine clean-ALLOW result, but for a *different* request.
        other_ctx = _context(request=_make_request(request_id="req-OTHER"))
        other_result = evaluate_pre_action_gate(other_ctx)
        self.assertTrue(other_result.authorization_ready)
        ctx, _ = _clean_allow()
        res = build_capability_grant_candidate(ctx, other_result)
        _assert_failed(self, res, "evidence_digest_mismatch")

    def test_tampered_context_against_real_result(self):
        # Result computed for ctx_a; context swapped to a tampered ctx_b.
        ctx_a = _context()
        result_a = evaluate_pre_action_gate(ctx_a)
        ctx_b = _context(request=_make_request(actor_id="actor-EVIL"))
        res = build_capability_grant_candidate(ctx_b, result_a)
        _assert_failed(self, res, "evidence_digest_mismatch")

    def test_real_deny_context_with_forged_allow(self):
        ledger = _matching_deny_ledger()
        ctx = _context(ledger=ledger)
        real = evaluate_pre_action_gate(ctx)
        self.assertEqual(real.decision, _D.DENY)
        forged = _forged_allow("b" * 64)
        res = build_capability_grant_candidate(ctx, forged)
        _assert_failed(self, res, "gate_reevaluation_not_clean_allow")


# ============================================================
# Context that does not re-evaluate to a clean ALLOW
# ============================================================

class ReevaluationTests(unittest.TestCase):
    def test_active_deny_context(self):
        # A real DENY result (matched_deny_count > 0) presented as the claim:
        # the factory rejects it on the decision check before re-evaluating.
        ledger = _matching_deny_ledger()
        ctx = _context(ledger=ledger)
        real = evaluate_pre_action_gate(ctx)
        self.assertGreater(real.matched_deny_count, 0)
        res = build_capability_grant_candidate(ctx, real)
        _assert_failed(self, res, "gate_result_not_allow")

    def test_naive_decision_time_context(self):
        naive = datetime(2026, 6, 15, 12, 0, 0)
        # ledger_evidence still carries an aware decision_time; the naive
        # context decision_time is what drives the gate to fail closed.
        ctx = _context(
            decision_time=naive, ledger_evidence=_make_ledger_ev(DenyLedger())
        )
        # A real result for this context is non-ready; forge a clean ALLOW.
        forged = _forged_allow("c" * 64)
        res = build_capability_grant_candidate(ctx, forged)
        _assert_failed(self, res, "gate_reevaluation_not_clean_allow")

    def test_missing_provider_evidence_context(self):
        request = _make_request()
        recomputed = _make_recomputed(request)
        attestation = build_classification_attestation(request, recomputed, "v1")
        cls_ev = _make_cls_ev(request, attestation, recomputed, provider=None)
        ctx = _context(
            request=request,
            attestation=attestation,
            recomputed=recomputed,
            classification_evidence=cls_ev,
        )
        forged = _forged_allow("d" * 64)
        res = build_capability_grant_candidate(ctx, forged)
        _assert_failed(self, res, "gate_reevaluation_not_clean_allow")

    def test_missing_ledger_evidence_context(self):
        ctx = _context(ledger_evidence=None)
        forged = _forged_allow("e" * 64)
        res = build_capability_grant_candidate(ctx, forged)
        _assert_failed(self, res, "gate_reevaluation_not_clean_allow")

    def test_malformed_context_object_fails_closed(self):
        # object.__new__ bypasses __post_init__; isinstance still passes, but
        # the gate re-evaluation fails closed rather than crashing.
        malformed = object.__new__(PreActionGateContext)
        forged = _forged_allow("f" * 64)
        res = build_capability_grant_candidate(malformed, forged)
        self.assertFalse(res.ok)
        self.assertIsNone(res.candidate)
        for code in res.failed_checks:
            self.assertIn(code, _KNOWN_CODES)


# ============================================================
# Requested-expiry handling via the factory
# ============================================================

class RequestedExpiryTests(unittest.TestCase):
    def test_requested_within_range_is_honoured(self):
        ctx, result = _clean_allow()
        requested = T_NOW + timedelta(minutes=30)
        res = build_capability_grant_candidate(ctx, result, requested_expires_at=requested)
        self.assertTrue(res.ok)
        self.assertEqual(res.candidate.expires_at, requested)
        self.assertEqual(res.expiry_bound_source, "requested_expires_at")

    def test_requested_before_decision_time_rejected(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(
            ctx, result, requested_expires_at=T_NOW - timedelta(minutes=1)
        )
        _assert_failed(self, res, "requested_expiry_before_decision_time")

    def test_requested_exceeding_derived_max_rejected(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(
            ctx, result, requested_expires_at=T_LATE
        )
        _assert_failed(self, res, "requested_expiry_exceeds_derived_max")

    def test_requested_naive_rejected(self):
        ctx, result = _clean_allow()
        res = build_capability_grant_candidate(
            ctx, result, requested_expires_at=datetime(2026, 6, 15, 12, 30, 0)
        )
        _assert_failed(self, res, "requested_expiry_not_aware")

    def test_internal_exception_fails_closed(self):
        ctx, result = _clean_allow()
        boom = _ExplodingDatetime(2026, 6, 15, 12, 30, 0, tzinfo=UTC)
        res = build_capability_grant_candidate(ctx, result, requested_expires_at=boom)
        _assert_failed(self, res, "internal_error_fail_closed")


# ============================================================
# derive_candidate_expiry (pure, direct)
# ============================================================

class DeriveExpiryTests(unittest.TestCase):
    def test_issued_and_not_before_equal_decision_time(self):
        exp = derive_candidate_expiry(_context())
        self.assertTrue(exp.ok)
        self.assertEqual(exp.issued_at, T_NOW)
        self.assertEqual(exp.not_before, T_NOW)

    def test_picks_minimum_bound(self):
        # Ledger evidence expires earliest -> it is the binding source.
        ledger = DenyLedger()
        led_ev = _make_ledger_ev(
            ledger, decision_time=T_NOW, expires_at=T_NOW + timedelta(minutes=5)
        )
        ctx = _context(ledger=ledger, ledger_evidence=led_ev)
        exp = derive_candidate_expiry(ctx)
        self.assertTrue(exp.ok)
        self.assertEqual(exp.expires_at, T_NOW + timedelta(minutes=5))
        self.assertEqual(exp.source, "ledger_evidence")

    def test_snapshot_expiry_none_uses_other_bounds(self):
        ctx = _context(snapshot=_make_snapshot(expires_at=None))
        exp = derive_candidate_expiry(ctx)
        self.assertTrue(exp.ok)
        self.assertNotEqual(exp.source, "snapshot")
        self.assertIsNotNone(exp.expires_at)

    def test_no_bounds_yields_missing(self):
        # snapshot.expires_at None and no evidence -> no upper bound at all.
        ctx = _context(
            snapshot=_make_snapshot(expires_at=None),
            classification_evidence=None,
            ledger_evidence=None,
        )
        exp = derive_candidate_expiry(ctx)
        self.assertFalse(exp.ok)
        self.assertIsNone(exp.expires_at)
        self.assertIn("expiry_bound_missing", exp.failed_checks)

    def test_naive_decision_time_yields_not_aware(self):
        ctx = _context(decision_time=datetime(2026, 6, 15, 12, 0, 0))
        exp = derive_candidate_expiry(ctx)
        self.assertFalse(exp.ok)
        self.assertIn("decision_time_not_aware", exp.failed_checks)

    def test_all_bounds_before_decision_time(self):
        # decision_time far after every bound -> no valid window.
        snap = _make_snapshot(created_at=T_PAST, expires_at=T_FUTURE)
        ctx = _context(snapshot=snap, decision_time=T_LATE)
        exp = derive_candidate_expiry(ctx)
        self.assertFalse(exp.ok)
        self.assertIn("expiry_bound_before_decision_time", exp.failed_checks)

    def test_requested_equal_decision_time_ok(self):
        exp = derive_candidate_expiry(_context(), requested_expires_at=T_NOW)
        self.assertTrue(exp.ok)
        self.assertEqual(exp.expires_at, T_NOW)

    def test_requested_equal_derived_max_ok(self):
        exp = derive_candidate_expiry(_context(), requested_expires_at=T_FUTURE)
        self.assertTrue(exp.ok)
        self.assertEqual(exp.expires_at, T_FUTURE)
        self.assertEqual(exp.source, "requested_expires_at")

    def test_requested_over_max_rejected(self):
        exp = derive_candidate_expiry(_context(), requested_expires_at=T_LATE)
        self.assertFalse(exp.ok)
        self.assertIn("requested_expiry_exceeds_derived_max", exp.failed_checks)

    def test_requested_before_decision_rejected(self):
        exp = derive_candidate_expiry(
            _context(), requested_expires_at=T_NOW - timedelta(seconds=1)
        )
        self.assertFalse(exp.ok)
        self.assertIn("requested_expiry_before_decision_time", exp.failed_checks)

    def test_wrong_type_context_fails(self):
        exp = derive_candidate_expiry("nope")
        self.assertFalse(exp.ok)
        self.assertIn("context_type_invalid", exp.failed_checks)


# ============================================================
# CapabilityGrantBuildResult invariants
# ============================================================

class BuildResultInvariantTests(unittest.TestCase):
    def test_ok_true_requires_candidate(self):
        with self.assertRaises(ValueError):
            CapabilityGrantBuildResult(ok=True, candidate=None, failed_checks=())

    def test_ok_true_requires_empty_failed_checks(self):
        ctx, result = _clean_allow()
        c = build_capability_grant_candidate(ctx, result).candidate
        with self.assertRaises(ValueError):
            CapabilityGrantBuildResult(ok=True, candidate=c, failed_checks=("x",))

    def test_ok_false_requires_no_candidate(self):
        ctx, result = _clean_allow()
        c = build_capability_grant_candidate(ctx, result).candidate
        with self.assertRaises(ValueError):
            CapabilityGrantBuildResult(ok=False, candidate=c, failed_checks=("x",))

    def test_ok_false_requires_failed_checks(self):
        with self.assertRaises(ValueError):
            CapabilityGrantBuildResult(ok=False, candidate=None, failed_checks=())

    def test_is_frozen(self):
        res = CapabilityGrantBuildResult(ok=False, failed_checks=("x",))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            res.ok = True  # type: ignore[misc]

    def test_candidate_expiry_is_frozen(self):
        exp = CandidateExpiry(ok=False, failed_checks=("x",))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            exp.ok = True  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
