"""
GOAA Authorization Kernel AK-5B — Capability Grant Envelope Factory Tests
=========================================================================
Framework: unittest (standard library). No pytest, no third-party deps.
All tests are pure — no file I/O, no network, no subprocess, no clock reads.

Covers the AK-5B fail-closed attack model: wrong-type / None parameters,
empty issuer metadata, non-clean / not-ready / forged-flag claimed results,
post_init-bypassing malformed results, foreign / mismatched gate_result,
evidence-digest mismatch, real-DENY context + forged ALLOW, naive
decision_time, missing ledger evidence, candidate rebuild failure (requested
expiry over derived max), tampered candidate (digest invalid AND
field-mismatch), and internal exceptions. Every failure path yields ok=False,
envelope_candidate=None, non-empty failed_checks (all in KNOWN_FAIL_CODES),
and no raw-exception leakage.

BLOCKER 8E additions:
  - AK-5A rebuild receives the CALLER'S ORIGINAL gate_result (not recomputed).
  - A passed-but-fake recomputation fails closed.
  - The recomputed boundary-flag failure has its OWN distinct code
    ("recomputed_gate_boundary_flags_invalid").
  - The success field is named `envelope_candidate` (no `envelope` alias).
  - The full-rebuild mismatch code is "candidate_rebuild_mismatch".
  - The AK-5A rebuild failure collapses to exactly ("candidate_rebuild_failed",).
  - Every emitted code is a member of KNOWN_FAIL_CODES.

BLOCKER 2 (revision R2) additions:
  - CapabilityGrantEnvelopeBuildResult.__post_init__ rejects unknown codes,
    non-str codes, and empty-string codes; ok=False forces expiry_bound_source
    to None and a non-str expiry_bound_source is rejected.
  - _fail() collapses an unknown/empty code to ("internal_error_fail_closed",)
    without leaking the bad code and without recursion.
  - Every literal code passed to _fail() in the factory source is a member of
    KNOWN_FAIL_CODES.

BLOCKER 3 (revision R2) additions:
  - Whitespace-only issuer metadata maps to issuer_claim_id_invalid /
    issuer_claim_version_invalid, NOT internal_error_fail_closed.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
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
from authorization_kernel.effect_classifier import (
    RecomputedClassification,
    build_classification_attestation,
)
from authorization_kernel.deny_event import DenyEvent
from authorization_kernel.deny_event_validation import DenyCreationRequest
from authorization_kernel.deny_ledger_state import DenyLedger, create_deny_entry
from authorization_kernel.authorization_evidence import (
    PreActionGateContext,
    PreActionGateResult,
    ProviderEvidence,
    TrustedClassificationEvidence,
    AuthoritativeLedgerEvidence,
)
from authorization_kernel.pre_action_gate import (
    compute_evidence_digest,
    evaluate_pre_action_gate,
)
from authorization_kernel.capability_models import (
    CapabilityGrantCandidate,
    compute_candidate_digest,
    verify_candidate_digest,
)
from authorization_kernel.capability_validation import (
    build_capability_grant_candidate,
)
from authorization_kernel.capability_grant_envelope import (
    CapabilityGrantEnvelopeCandidate,
    verify_envelope_candidate_digest,
)
import authorization_kernel.capability_grant_envelope_validation as val_module
from authorization_kernel.capability_grant_envelope_validation import (
    KNOWN_FAIL_CODES,
    CapabilityGrantEnvelopeBuildResult,
    build_capability_grant_envelope_candidate,
)


UTC = timezone.utc
T_PAST = datetime(2026, 6, 15, 11, 0, 0, tzinfo=UTC)
T_NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
T_FUTURE = datetime(2026, 6, 15, 13, 0, 0, tzinfo=UTC)
T_LATE = datetime(2026, 6, 15, 14, 0, 0, tzinfo=UTC)

_D = AuthorizationDecision
_OMIT = object()

# All emitted codes must be members of the factory's closed vocabulary.
_KNOWN_CODES = KNOWN_FAIL_CODES


# ============================================================
# Fixture builders (pure, in-memory) — mirror the AK-4/AK-5A tests
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
        provider = ProviderEvidence(provider_id="prov-1", issued_at=T_PAST, expires_at=T_FUTURE)
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
    ctx = _context()
    result = evaluate_pre_action_gate(ctx)
    assert result.authorization_ready, result.failed_checks
    return ctx, result


def _clean_candidate(ctx, result) -> CapabilityGrantCandidate:
    build = build_capability_grant_candidate(ctx, result)
    assert build.ok, build.failed_checks
    return build.candidate


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
    return PreActionGateResult(
        decision=_D.ALLOW,
        authorization_ready=True,
        failed_checks=(),
        evidence_digest=evidence_digest,
        matched_deny_count=0,
    )


def _malformed_result(**attrs) -> PreActionGateResult:
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


def _assert_failed(self, res: CapabilityGrantEnvelopeBuildResult, *expected_codes: str):
    self.assertFalse(res.ok)
    self.assertIsNone(res.envelope_candidate)
    self.assertTrue(res.failed_checks)
    self.assertIsNone(res.expiry_bound_source)
    for code in res.failed_checks:
        self.assertIn(code, _KNOWN_CODES, f"leaked/unknown code: {code!r}")
        self.assertNotIn("Traceback", code)
    for code in expected_codes:
        self.assertIn(code, res.failed_checks)


# ============================================================
# Happy path
# ============================================================

class HappyPathTests(unittest.TestCase):
    def _build_ok(self):
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        res = build_capability_grant_envelope_candidate(
            ctx, result, candidate, "issuer-1", "iv1"
        )
        return ctx, result, candidate, res

    def test_clean_allow_builds_envelope(self):
        _, _, _, res = self._build_ok()
        self.assertTrue(res.ok, res.failed_checks)
        self.assertIsInstance(res.envelope_candidate, CapabilityGrantEnvelopeCandidate)
        self.assertEqual(res.failed_checks, ())

    def test_result_uses_envelope_candidate_field_no_alias(self):
        # BLOCKER 6: the success field is `envelope_candidate`; no `envelope`.
        _, _, _, res = self._build_ok()
        self.assertTrue(hasattr(res, "envelope_candidate"))
        self.assertFalse(hasattr(res, "envelope"))

    def test_envelope_digest_is_valid(self):
        _, _, _, res = self._build_ok()
        self.assertTrue(verify_envelope_candidate_digest(res.envelope_candidate))
        self.assertNotEqual(res.envelope_candidate.envelope_candidate_digest, "")

    def test_envelope_binds_candidate_digest(self):
        _, _, candidate, res = self._build_ok()
        self.assertEqual(res.envelope_candidate.candidate_digest, candidate.candidate_digest)

    def test_envelope_binds_evidence_digest(self):
        ctx, _, _, res = self._build_ok()
        self.assertEqual(res.envelope_candidate.evidence_digest, compute_evidence_digest(ctx))

    def test_envelope_fields_derived_from_candidate(self):
        ctx, _, candidate, res = self._build_ok()
        e = res.envelope_candidate
        self.assertEqual(e.request_id, candidate.request_id)
        self.assertEqual(e.task_id, candidate.task_id)
        self.assertEqual(e.actor_id, candidate.actor_id)
        self.assertEqual(e.primary_effect, candidate.primary_effect)
        self.assertEqual(e.snapshot_id, candidate.snapshot_id)
        self.assertEqual(e.policy_version, candidate.policy_version)
        self.assertEqual(e.expires_at, candidate.expires_at)

    def test_issuer_metadata_recorded(self):
        _, _, _, res = self._build_ok()
        self.assertEqual(res.envelope_candidate.issuer_claim_id, "issuer-1")
        self.assertEqual(res.envelope_candidate.issuer_claim_version, "iv1")

    def test_authority_proof_type_is_none(self):
        _, _, _, res = self._build_ok()
        self.assertEqual(res.envelope_candidate.authority_proof_type, "NONE")

    def test_issued_not_before_equal_decision_time(self):
        ctx, _, _, res = self._build_ok()
        self.assertEqual(res.envelope_candidate.issued_at, ctx.decision_time)
        self.assertEqual(res.envelope_candidate.not_before, ctx.decision_time)

    def test_expiry_bound_source_reported(self):
        _, _, _, res = self._build_ok()
        self.assertIn(
            res.expiry_bound_source,
            {"snapshot", "classification_evidence", "provider_evidence",
             "ledger_evidence", "requested_expires_at"},
        )

    def test_expiry_bound_source_is_nonempty_str(self):
        # BLOCKER 2: ok=True carries a real, non-empty AK-5A source string.
        _, _, _, res = self._build_ok()
        self.assertIsInstance(res.expiry_bound_source, str)
        self.assertTrue(res.expiry_bound_source.strip())

    def test_envelope_has_no_lifecycle_fields(self):
        _, _, _, res = self._build_ok()
        for forbidden in ("grant_id", "status", "consumed_at", "revoked_at", "expiry_bound_source"):
            self.assertFalse(hasattr(res.envelope_candidate, forbidden))


# ============================================================
# BLOCKER 5/8E — AK-5A rebuild receives the ORIGINAL gate_result
# ============================================================

class RebuildInputTests(unittest.TestCase):
    def test_ak5a_receives_original_gate_result(self):
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        captured = {}
        real = val_module.build_capability_grant_candidate

        def spy(*, context, gate_result, requested_expires_at):
            captured["gate_result"] = gate_result
            return real(
                context=context,
                gate_result=gate_result,
                requested_expires_at=requested_expires_at,
            )

        val_module.build_capability_grant_candidate = spy
        try:
            res = build_capability_grant_envelope_candidate(
                ctx, result, candidate, "issuer-1", "iv1"
            )
        finally:
            val_module.build_capability_grant_candidate = real
        self.assertTrue(res.ok, res.failed_checks)
        # The EXACT original result object must flow into the AK-5A factory.
        self.assertIs(captured["gate_result"], result)

    def test_passed_but_fake_recomputation_fails_closed(self):
        # Passed result is genuinely clean, but the recomputation is forced to
        # a non-clean ALLOW -> fail closed before the AK-5A rebuild.
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        real = val_module.evaluate_pre_action_gate

        def fake(context):
            r = real(context)
            return _malformed_result(
                evidence_digest=r.evidence_digest, matched_deny_count=7
            )

        val_module.evaluate_pre_action_gate = fake
        try:
            res = build_capability_grant_envelope_candidate(
                ctx, result, candidate, "issuer-1", "iv1"
            )
        finally:
            val_module.evaluate_pre_action_gate = real
        _assert_failed(self, res, "gate_reevaluation_not_clean_allow")

    def test_recomputed_boundary_flag_has_distinct_code(self):
        # Recomputed result is a clean ALLOW but forges a boundary proof ->
        # the RECOMPUTED-path code is distinct from the passed-path code.
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        real = val_module.evaluate_pre_action_gate

        def fake(context):
            r = real(context)
            return _malformed_result(
                evidence_digest=r.evidence_digest, real_execution_permission=True
            )

        val_module.evaluate_pre_action_gate = fake
        try:
            res = build_capability_grant_envelope_candidate(
                ctx, result, candidate, "issuer-1", "iv1"
            )
        finally:
            val_module.evaluate_pre_action_gate = real
        _assert_failed(self, res, "recomputed_gate_boundary_flags_invalid")
        self.assertNotIn("gate_result_boundary_flags_invalid", res.failed_checks)


# ============================================================
# Type-check fail-closed
# ============================================================

class TypeCheckTests(unittest.TestCase):
    def setUp(self):
        self.ctx, self.result = _clean_allow()
        self.candidate = _clean_candidate(self.ctx, self.result)

    def test_wrong_type_context(self):
        res = build_capability_grant_envelope_candidate(
            "nope", self.result, self.candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "context_type_invalid")

    def test_none_context(self):
        res = build_capability_grant_envelope_candidate(
            None, self.result, self.candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "context_type_invalid")

    def test_wrong_type_gate_result(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, "nope", self.candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_result_type_invalid")

    def test_wrong_type_candidate(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, "nope", "issuer-1", "iv1"
        )
        _assert_failed(self, res, "candidate_type_invalid")

    def test_none_candidate(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, None, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "candidate_type_invalid")

    def test_empty_issuer_claim_id(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, self.candidate, "", "iv1"
        )
        _assert_failed(self, res, "issuer_claim_id_invalid")

    def test_nonstr_issuer_claim_id(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, self.candidate, 123, "iv1"
        )
        _assert_failed(self, res, "issuer_claim_id_invalid")

    def test_empty_issuer_claim_version(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, self.candidate, "issuer-1", ""
        )
        _assert_failed(self, res, "issuer_claim_version_invalid")


# ============================================================
# BLOCKER 3 (R2) — whitespace-only issuer metadata
# ============================================================

class WhitespaceIssuerTests(unittest.TestCase):
    def setUp(self):
        self.ctx, self.result = _clean_allow()
        self.candidate = _clean_candidate(self.ctx, self.result)

    def test_spaces_issuer_claim_id_maps_to_id_invalid(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, self.candidate, "   ", "iv1"
        )
        _assert_failed(self, res, "issuer_claim_id_invalid")
        self.assertNotIn("internal_error_fail_closed", res.failed_checks)

    def test_tab_issuer_claim_id_maps_to_id_invalid(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, self.candidate, "\t", "iv1"
        )
        _assert_failed(self, res, "issuer_claim_id_invalid")
        self.assertNotIn("internal_error_fail_closed", res.failed_checks)

    def test_spaces_issuer_claim_version_maps_to_version_invalid(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, self.candidate, "issuer-1", "   "
        )
        _assert_failed(self, res, "issuer_claim_version_invalid")
        self.assertNotIn("internal_error_fail_closed", res.failed_checks)

    def test_tab_issuer_claim_version_maps_to_version_invalid(self):
        res = build_capability_grant_envelope_candidate(
            self.ctx, self.result, self.candidate, "issuer-1", "\t"
        )
        _assert_failed(self, res, "issuer_claim_version_invalid")
        self.assertNotIn("internal_error_fail_closed", res.failed_checks)


# ============================================================
# Non-clean / forged claimed result
# ============================================================

class ClaimedResultTests(unittest.TestCase):
    def setUp(self):
        self.ctx, self.result = _clean_allow()
        self.candidate = _clean_candidate(self.ctx, self.result)

    def test_decision_not_allow(self):
        denied = PreActionGateResult(decision=_D.DENY, authorization_ready=False)
        res = build_capability_grant_envelope_candidate(
            self.ctx, denied, self.candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_result_not_allow")

    def test_allow_but_not_ready(self):
        not_ready = PreActionGateResult(decision=_D.ALLOW, authorization_ready=False)
        res = build_capability_grant_envelope_candidate(
            self.ctx, not_ready, self.candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_result_not_ready")

    def test_malformed_with_failed_checks(self):
        bad = _malformed_result(
            evidence_digest=self.result.evidence_digest, failed_checks=("snapshot:expired",)
        )
        res = build_capability_grant_envelope_candidate(
            self.ctx, bad, self.candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_result_has_failed_checks")

    def test_malformed_with_deny_count(self):
        bad = _malformed_result(evidence_digest=self.result.evidence_digest, matched_deny_count=3)
        res = build_capability_grant_envelope_candidate(
            self.ctx, bad, self.candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_result_deny_matched")

    def test_malformed_with_empty_digest(self):
        bad = _malformed_result(evidence_digest="")
        res = build_capability_grant_envelope_candidate(
            self.ctx, bad, self.candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_result_evidence_digest_empty")


# ============================================================
# Boundary-flag forgery on the PASSED result (claimed-path code)
# ============================================================

class BoundaryFlagTests(unittest.TestCase):
    def _attack(self, **flag):
        ctx, real = _clean_allow()
        candidate = _clean_candidate(ctx, real)
        bad = _malformed_result(evidence_digest=real.evidence_digest, **flag)
        res = build_capability_grant_envelope_candidate(
            ctx, bad, candidate, "issuer-1", "iv1"
        )
        # BLOCKER 7: the PASSED-path code is "gate_result_boundary_flags_invalid".
        _assert_failed(self, res, "gate_result_boundary_flags_invalid")
        self.assertNotIn("recomputed_gate_boundary_flags_invalid", res.failed_checks)

    def test_provider_authority_proven_rejected(self):
        self._attack(provider_authority_proven=True)

    def test_global_ledger_authority_proven_rejected(self):
        self._attack(global_ledger_authority_proven=True)

    def test_global_ledger_freshness_proven_rejected(self):
        self._attack(global_ledger_freshness_proven=True)

    def test_toctou_resolved_rejected(self):
        self._attack(toctou_resolved=True)

    def test_real_execution_permission_rejected(self):
        self._attack(real_execution_permission=True)

    def test_truthy_nonbool_flag_rejected(self):
        self._attack(real_execution_permission=1)


# ============================================================
# Forged / foreign / mismatched results
# ============================================================

class ForgedResultTests(unittest.TestCase):
    def test_forged_allow_wrong_digest(self):
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        forged = _forged_allow("a" * 64)
        res = build_capability_grant_envelope_candidate(
            ctx, forged, candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "evidence_digest_mismatch")

    def test_foreign_clean_allow(self):
        other_ctx = _context(request=_make_request(request_id="req-OTHER"))
        other_result = evaluate_pre_action_gate(other_ctx)
        self.assertTrue(other_result.authorization_ready)
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        res = build_capability_grant_envelope_candidate(
            ctx, other_result, candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "evidence_digest_mismatch")

    def test_real_deny_context_with_forged_allow(self):
        ledger = _matching_deny_ledger()
        ctx = _context(ledger=ledger)
        real = evaluate_pre_action_gate(ctx)
        self.assertEqual(real.decision, _D.DENY)
        clean_ctx, clean_result = _clean_allow()
        candidate = _clean_candidate(clean_ctx, clean_result)
        forged = _forged_allow("b" * 64)
        res = build_capability_grant_envelope_candidate(
            ctx, forged, candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_reevaluation_not_clean_allow")

    def test_naive_decision_time_context(self):
        naive = datetime(2026, 6, 15, 12, 0, 0)
        ctx = _context(decision_time=naive, ledger_evidence=_make_ledger_ev(DenyLedger()))
        clean_ctx, clean_result = _clean_allow()
        candidate = _clean_candidate(clean_ctx, clean_result)
        forged = _forged_allow("c" * 64)
        res = build_capability_grant_envelope_candidate(
            ctx, forged, candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_reevaluation_not_clean_allow")

    def test_missing_ledger_evidence_context(self):
        ctx = _context(ledger_evidence=None)
        clean_ctx, clean_result = _clean_allow()
        candidate = _clean_candidate(clean_ctx, clean_result)
        forged = _forged_allow("e" * 64)
        res = build_capability_grant_envelope_candidate(
            ctx, forged, candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "gate_reevaluation_not_clean_allow")


# ============================================================
# Candidate binding (exact-match-or-fail-closed)
# ============================================================

class CandidateBindingTests(unittest.TestCase):
    def test_tampered_candidate_stale_digest_rejected(self):
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        tampered = dataclasses.replace(candidate, actor_id="actor-EVIL")
        self.assertFalse(verify_candidate_digest(tampered))
        res = build_capability_grant_envelope_candidate(
            ctx, result, tampered, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "candidate_digest_invalid")

    def test_tampered_candidate_resealed_field_mismatch_rejected(self):
        # Mutate a field AND recompute its digest: verify passes, but the
        # rebuilt (context-derived) candidate will not match -> fail-closed.
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        evil = dataclasses.replace(candidate, actor_id="actor-EVIL")
        evil = dataclasses.replace(evil, candidate_digest=compute_candidate_digest(evil))
        self.assertTrue(verify_candidate_digest(evil))
        res = build_capability_grant_envelope_candidate(
            ctx, result, evil, "issuer-1", "iv1"
        )
        # BLOCKER 7: full-rebuild mismatch code is "candidate_rebuild_mismatch".
        _assert_failed(self, res, "candidate_rebuild_mismatch")

    def test_candidate_expiry_over_derived_max_rebuild_collapses(self):
        # candidate.expires_at drives the rebuild's requested_expires_at; an
        # expiry beyond the derived max makes the AK-5A rebuild fail closed,
        # and the failure COLLAPSES to exactly ("candidate_rebuild_failed",).
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        stretched = dataclasses.replace(candidate, expires_at=T_LATE)
        stretched = dataclasses.replace(
            stretched, candidate_digest=compute_candidate_digest(stretched)
        )
        res = build_capability_grant_envelope_candidate(
            ctx, result, stretched, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "candidate_rebuild_failed")
        # No AK-5A sub-codes leak through.
        self.assertEqual(res.failed_checks, ("candidate_rebuild_failed",))

    def test_candidate_from_foreign_context_mismatch(self):
        ctx, result = _clean_allow()
        other_ctx = _context(request=_make_request(request_id="req-OTHER"))
        other_result = evaluate_pre_action_gate(other_ctx)
        foreign_candidate = _clean_candidate(other_ctx, other_result)
        res = build_capability_grant_envelope_candidate(
            ctx, result, foreign_candidate, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "candidate_rebuild_mismatch")


# ============================================================
# Internal exception fail-closed
# ============================================================

class InternalExceptionTests(unittest.TestCase):
    def test_malformed_candidate_object_fails_closed(self):
        ctx, result = _clean_allow()
        malformed = object.__new__(CapabilityGrantCandidate)
        res = build_capability_grant_envelope_candidate(
            ctx, result, malformed, "issuer-1", "iv1"
        )
        _assert_failed(self, res, "internal_error_fail_closed")

    def test_malformed_context_object_fails_closed(self):
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        malformed_ctx = object.__new__(PreActionGateContext)
        forged = _forged_allow("f" * 64)
        res = build_capability_grant_envelope_candidate(
            malformed_ctx, forged, candidate, "issuer-1", "iv1"
        )
        self.assertFalse(res.ok)
        self.assertIsNone(res.envelope_candidate)
        for code in res.failed_checks:
            self.assertIn(code, _KNOWN_CODES)


# ============================================================
# KNOWN_FAIL_CODES vocabulary
# ============================================================

class KnownFailCodesTests(unittest.TestCase):
    def test_known_fail_codes_is_frozenset(self):
        self.assertIsInstance(KNOWN_FAIL_CODES, frozenset)

    def test_collapsed_and_distinct_codes_present(self):
        for code in (
            "candidate_rebuild_failed",
            "candidate_rebuild_mismatch",
            "recomputed_gate_boundary_flags_invalid",
            "gate_result_boundary_flags_invalid",
        ):
            self.assertIn(code, KNOWN_FAIL_CODES)


# ============================================================
# BLOCKER 2 (R2) — _fail() defensive collapse (no leak, no recursion)
# ============================================================

class FailHelperTests(unittest.TestCase):
    def test_fail_with_known_code(self):
        res = val_module._fail("context_type_invalid")
        self.assertFalse(res.ok)
        self.assertEqual(res.failed_checks, ("context_type_invalid",))

    def test_fail_unknown_code_collapses_no_leak(self):
        res = val_module._fail("unknown_code")
        self.assertFalse(res.ok)
        self.assertEqual(res.failed_checks, ("internal_error_fail_closed",))
        self.assertNotIn("unknown_code", res.failed_checks)

    def test_fail_empty_call_collapses(self):
        res = val_module._fail()
        self.assertEqual(res.failed_checks, ("internal_error_fail_closed",))

    def test_fail_mixed_known_and_unknown_collapses(self):
        res = val_module._fail("context_type_invalid", "unknown_code")
        self.assertEqual(res.failed_checks, ("internal_error_fail_closed",))

    def test_fail_does_not_recurse_on_internal_code(self):
        # _fail must construct its fallback directly, not call itself.
        tree = ast.parse(inspect.getsource(val_module))
        fail_func = next(
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "_fail"
        )
        inner_calls = [
            n for n in ast.walk(fail_func)
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_fail"
        ]
        self.assertEqual(inner_calls, [], "_fail must not recurse")

    def test_all_factory_fail_codes_are_known(self):
        # Every literal string passed to _fail() in the factory source must be
        # a member of KNOWN_FAIL_CODES.
        tree = ast.parse(inspect.getsource(val_module))
        codes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_fail":
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        codes.add(arg.value)
        self.assertTrue(codes, "expected at least one _fail(...) literal code")
        for code in codes:
            self.assertIn(code, KNOWN_FAIL_CODES, f"unknown factory code: {code!r}")


# ============================================================
# BLOCKER 2 (R2) — Result code-membership / expiry-source validation
# ============================================================

class ResultValidationTests(unittest.TestCase):
    def test_unknown_failed_check_code_rejected(self):
        with self.assertRaises(ValueError):
            CapabilityGrantEnvelopeBuildResult(ok=False, failed_checks=("unknown_code",))

    def test_nonstr_failed_check_code_rejected(self):
        with self.assertRaises(TypeError):
            CapabilityGrantEnvelopeBuildResult(ok=False, failed_checks=(123,))

    def test_empty_string_failed_check_code_rejected(self):
        with self.assertRaises(ValueError):
            CapabilityGrantEnvelopeBuildResult(ok=False, failed_checks=("",))

    def test_known_code_accepted(self):
        res = CapabilityGrantEnvelopeBuildResult(
            ok=False, failed_checks=("internal_error_fail_closed",)
        )
        self.assertFalse(res.ok)
        self.assertEqual(res.failed_checks, ("internal_error_fail_closed",))

    def test_nonstr_expiry_bound_source_rejected(self):
        with self.assertRaises(TypeError):
            CapabilityGrantEnvelopeBuildResult(
                ok=False,
                failed_checks=("internal_error_fail_closed",),
                expiry_bound_source=123,
            )

    def test_ok_false_requires_none_expiry_bound_source(self):
        with self.assertRaises(ValueError):
            CapabilityGrantEnvelopeBuildResult(
                ok=False,
                failed_checks=("internal_error_fail_closed",),
                expiry_bound_source="snapshot",
            )


# ============================================================
# CapabilityGrantEnvelopeBuildResult invariants
# ============================================================

class BuildResultInvariantTests(unittest.TestCase):
    def test_ok_true_requires_envelope_candidate(self):
        with self.assertRaises(ValueError):
            CapabilityGrantEnvelopeBuildResult(ok=True, envelope_candidate=None, failed_checks=())

    def test_ok_true_requires_empty_failed_checks(self):
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        env = build_capability_grant_envelope_candidate(
            ctx, result, candidate, "issuer-1", "iv1"
        ).envelope_candidate
        with self.assertRaises(ValueError):
            CapabilityGrantEnvelopeBuildResult(
                ok=True, envelope_candidate=env, failed_checks=("internal_error_fail_closed",)
            )

    def test_ok_false_requires_no_envelope_candidate(self):
        ctx, result = _clean_allow()
        candidate = _clean_candidate(ctx, result)
        env = build_capability_grant_envelope_candidate(
            ctx, result, candidate, "issuer-1", "iv1"
        ).envelope_candidate
        with self.assertRaises(ValueError):
            CapabilityGrantEnvelopeBuildResult(
                ok=False, envelope_candidate=env, failed_checks=("internal_error_fail_closed",)
            )

    def test_ok_false_requires_failed_checks(self):
        with self.assertRaises(ValueError):
            CapabilityGrantEnvelopeBuildResult(
                ok=False, envelope_candidate=None, failed_checks=()
            )

    def test_is_frozen(self):
        res = CapabilityGrantEnvelopeBuildResult(
            ok=False, failed_checks=("internal_error_fail_closed",)
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            res.ok = True  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
