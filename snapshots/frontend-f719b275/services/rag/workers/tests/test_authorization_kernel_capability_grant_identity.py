"""Tests for the AK-5B2A capability grant identity candidate."""

from __future__ import annotations

import ast
import dataclasses
import inspect
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from authorization_kernel import (
    capability_grant_identity as identity_mod,
)
from authorization_kernel.canonical_serialization import (
    sha256_hex,
)
from authorization_kernel.capability_grant_envelope import (
    CapabilityGrantEnvelopeCandidate,
    compute_envelope_candidate_digest,
)
from authorization_kernel.capability_grant_envelope_validation import (
    build_capability_grant_envelope_candidate,
)
from authorization_kernel.capability_grant_identity import (
    GRANT_ID_DOMAIN,
    CapabilityGrantIdentityCandidate,
    CapabilityGrantIdentityBuildResult,
    build_capability_grant_identity_candidate,
    compute_grant_identity_digest,
    derive_grant_id,
    grant_identity_payload,
    verify_grant_identity_digest,
)
from authorization_kernel.capability_validation import (
    build_capability_grant_candidate,
)
from authorization_kernel.enums import (
    ActionEffect,
    ResourceScopeType,
)
from authorization_kernel.pre_action_gate import (
    AuthorizationDecision,
    PreActionGateContext,
    PreActionGateResult,
    evaluate_pre_action_gate,
)
from authorization_kernel.action_request import (
    ActionRequest,
)
from authorization_kernel.authorization_snapshot import (
    AuthorizationSnapshot,
    compute_snapshot_hash,
)
from authorization_kernel.deny_ledger_state import (
    DenyLedger,
)
from authorization_kernel.effect_classifier import (
    RecomputedClassification,
    build_classification_attestation,
)
from authorization_kernel.authorization_evidence import (
    AuthoritativeLedgerEvidence,
    ProviderEvidence,
    TrustedClassificationEvidence,
)
from authorization_kernel.resource_scope import (
    TypedResourceScope,
)


UTC = timezone.utc

_T_NOW = datetime(2026, 6, 18, tzinfo=UTC)
_T_PAST = datetime(2026, 1, 1, tzinfo=UTC)
_T_FUTURE = datetime(2026, 12, 31, tzinfo=UTC)

_OMIT = object()


def _scope(*, path: str = "/tmp/x") -> TypedResourceScope:
    return TypedResourceScope(ResourceScopeType.FILE_PATH, path)


def _make_request(
    *,
    request_id: str = "req-1",
    task_id: str = "task-1",
    snapshot_id: str = "snap-1",
    actor_id: str = "actor-1",
    primary_effect: ActionEffect = ActionEffect.READ,
    resource_scopes=(_scope(),),
    requested_tool: str = "tool-1",
    policy_version: str = "pol-1",
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
    policy_version: str = "pol-1",
    allowed_effects=frozenset({ActionEffect.READ}),
    allowed_resource_scopes=(_scope(),),
    created_at: datetime = _T_PAST,
    expires_at: datetime | None = _T_FUTURE,
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
    issued_at: datetime = _T_PAST,
    expires_at: datetime = _T_FUTURE,
) -> TrustedClassificationEvidence:
    provider = ProviderEvidence(provider_id="prov-1", issued_at=_T_PAST, expires_at=_T_FUTURE)
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


def _make_ledger_ev(ledger: DenyLedger) -> AuthoritativeLedgerEvidence:
    tip = ledger.entries[-1].entry_hash if ledger.entries else None
    return AuthoritativeLedgerEvidence(
        ledger_tip_hash=tip,
        ledger_entry_count=len(ledger.entries),
        decision_time=_T_NOW,
        issued_at=_T_PAST,
        expires_at=_T_FUTURE,
    )


def _context(
    *,
    request=None,
    snapshot=None,
    attestation=None,
    ledger=None,
    decision_time: datetime = _T_NOW,
    request_id: str = "req-1",
    task_id: str = "task-1",
    actor_id: str = "actor-1",
    primary_effect: ActionEffect = ActionEffect.READ,
    resource_scopes=(_scope(),),
    requested_tool: str = "tool-1",
    policy_version: str = "pol-1",
    snapshot_id: str = "snap-1",
) -> PreActionGateContext:
    """Build a valid PreActionGateContext for tests."""
    if request is None:
        request = _make_request(
            request_id=request_id,
            task_id=task_id,
            snapshot_id=snapshot_id,
            actor_id=actor_id,
            primary_effect=primary_effect,
            resource_scopes=resource_scopes,
            requested_tool=requested_tool,
            policy_version=policy_version,
        )
    if snapshot is None:
        snapshot = _make_snapshot(
            task_id=task_id,
            snapshot_id=snapshot_id,
            policy_version=policy_version,
        )
    if attestation is None:
        recomputed = _make_recomputed(request)
        attestation = build_classification_attestation(
            request, recomputed, request.classification_policy_version
        )
    if ledger is None:
        ledger = DenyLedger()
    cls_ev = _make_cls_ev(request, attestation, _make_recomputed(request))
    ledger_ev = _make_ledger_ev(ledger)
    return PreActionGateContext(
        request=request,
        snapshot=snapshot,
        attestation=attestation,
        ledger=ledger,
        decision_time=decision_time,
        classification_evidence=cls_ev,
        ledger_evidence=ledger_ev,
    )


def _gate_result(context):
    """Return a clean ALLOW gate result for ``context``."""
    return evaluate_pre_action_gate(context)


def _clean_allow():
    """Return (context, result) for a normal ALLOW evaluation."""
    ctx = _context()
    result = evaluate_pre_action_gate(ctx)
    return ctx, result


def _make_default_expires_at() -> datetime:
    """Return a default expires_at for envelope construction."""
    return _T_NOW + timedelta(hours=1)


def _envelope(context=None, gate_result=None, **overrides):
    """Build a sealed envelope candidate for tests."""

    if context is None:
        context = _context()
    if gate_result is None:
        gate_result = evaluate_pre_action_gate(context)
    expires_at = overrides.pop(
        "requested_expires_at", _make_default_expires_at()
    )
    issuer_claim_id = overrides.pop("issuer_claim_id", "issuer-1")
    issuer_claim_version = overrides.pop("issuer_claim_version", "v1")
    candidate_build = build_capability_grant_candidate(
        context=context,
        gate_result=gate_result,
        requested_expires_at=expires_at,
    )
    envelope_build = build_capability_grant_envelope_candidate(
        context=context,
        gate_result=gate_result,
        candidate=candidate_build.candidate,
        issuer_claim_id=issuer_claim_id,
        issuer_claim_version=issuer_claim_version,
    )
    return envelope_build.envelope_candidate


def _build_identity(context=None, gate_result=None, envelope=None):
    """Run the identity factory and return the build result."""

    if context is None:
        context = _context()
    if gate_result is None:
        gate_result = evaluate_pre_action_gate(context)
    if envelope is None:
        envelope = _envelope(context, gate_result)
    return build_capability_grant_identity_candidate(
        context=context,
        gate_result=gate_result,
        envelope_candidate=envelope,
    )


def _identity(context=None, gate_result=None, envelope=None):
    """Return a built, sealed identity candidate."""

    result = _build_identity(context, gate_result, envelope)
    return result.grant_identity_candidate


def _reseal_envelope(envelope, **overrides):
    """Return a tampered envelope that is re-sealed so its digest verifies."""

    tampered = dataclasses.replace(envelope, **overrides)
    new_digest = compute_envelope_candidate_digest(tampered)
    return dataclasses.replace(
        tampered, envelope_candidate_digest=new_digest
    )


def _malformed_result(**attrs) -> PreActionGateResult:
    """Bypass frozen dataclass to forge arbitrary field values."""
    obj = object.__new__(PreActionGateResult)
    defaults = dict(
        decision=AuthorizationDecision.ALLOW,
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


class IdentityModelConstructionTests(unittest.TestCase):
    """Construction and validation of the identity candidate."""

    def test_build_success_seals_digest(self):
        candidate = _identity()
        self.assertIsInstance(candidate, CapabilityGrantIdentityCandidate)
        self.assertNotEqual(candidate.grant_identity_digest, "")

    def test_instance_field_count_is_22(self):
        fields = dataclasses.fields(CapabilityGrantIdentityCandidate)
        self.assertEqual(len(fields), 22)

    def test_grant_identity_digest_can_be_empty_transient(self):
        candidate = _identity()
        transient = dataclasses.replace(candidate, grant_identity_digest="")
        self.assertEqual(transient.grant_identity_digest, "")

    def test_grant_id_must_be_strict_hex(self):
        candidate = _identity()
        with self.assertRaises(ValueError):
            dataclasses.replace(candidate, grant_id="not-hex")

    def test_authority_proof_type_is_none(self):
        candidate = _identity()
        self.assertEqual(candidate.authority_proof_type, "NONE")

    def test_not_issued_grant_marker_true(self):
        self.assertIs(
            CapabilityGrantIdentityCandidate.NOT_ISSUED_GRANT, True
        )

    def test_not_lifecycle_state_marker_true(self):
        self.assertIs(
            CapabilityGrantIdentityCandidate.NOT_LIFECYCLE_STATE, True
        )

    def test_not_grant_id_authority_marker_true(self):
        self.assertIs(
            CapabilityGrantIdentityCandidate.NOT_GRANT_ID_AUTHORITY, True
        )

    def test_frozen_cannot_mutate(self):
        candidate = _identity()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            candidate.grant_id = "x"  # type: ignore[misc]

    def test_grant_id_field_present(self):
        names = {f.name for f in dataclasses.fields(
            CapabilityGrantIdentityCandidate)}
        self.assertIn("grant_id", names)

    def test_grant_identity_digest_field_present(self):
        names = {f.name for f in dataclasses.fields(
            CapabilityGrantIdentityCandidate)}
        self.assertIn("grant_identity_digest", names)


class DeriveGrantIdTests(unittest.TestCase):
    """Tests for the pure ``derive_grant_id`` function."""

    def test_derive_returns_64_lower_hex(self):
        envelope = _envelope()
        grant_id = derive_grant_id(envelope)
        self.assertEqual(len(grant_id), 64)
        self.assertEqual(grant_id, grant_id.lower())
        self.assertTrue(all(c in "0123456789abcdef" for c in grant_id))

    def test_derive_deterministic_same_envelope(self):
        envelope = _envelope()
        self.assertEqual(
            derive_grant_id(envelope), derive_grant_id(envelope)
        )

    def test_derive_same_for_equal_envelopes(self):
        context = _context()
        gate_result = _gate_result(context)
        env_a = _envelope(context, gate_result)
        env_b = _envelope(context, gate_result)
        self.assertEqual(env_a, env_b)
        self.assertEqual(derive_grant_id(env_a), derive_grant_id(env_b))

    def test_derive_differs_for_different_envelope(self):
        env_a = _envelope(_context(request_id="req-A"))
        env_b = _envelope(_context(request_id="req-B"))
        self.assertNotEqual(derive_grant_id(env_a), derive_grant_id(env_b))

    def test_derive_domain_separated(self):
        envelope = _envelope()
        expected = sha256_hex(
            {
                "grant_identity_domain": GRANT_ID_DOMAIN,
                "envelope_candidate_digest": (
                    envelope.envelope_candidate_digest
                ),
            }
        )
        self.assertEqual(derive_grant_id(envelope), expected)

    def test_derive_not_bare_digest_hash(self):
        envelope = _envelope()
        bare = sha256_hex(envelope.envelope_candidate_digest)
        self.assertNotEqual(derive_grant_id(envelope), bare)

    def test_derive_rejects_non_envelope_type(self):
        with self.assertRaises(TypeError):
            derive_grant_id(object())

    def test_derive_rejects_none(self):
        with self.assertRaises(TypeError):
            derive_grant_id(None)

    def test_derive_rejects_bare_digest_string(self):
        envelope = _envelope()
        with self.assertRaises(TypeError):
            derive_grant_id(envelope.envelope_candidate_digest)

    def test_derive_rejects_unsealed_envelope(self):
        envelope = _envelope()
        unsealed = dataclasses.replace(
            envelope, envelope_candidate_digest=""
        )
        with self.assertRaises(ValueError):
            derive_grant_id(unsealed)

    def test_derive_rejects_tampered_unsealed(self):
        envelope = _envelope()
        tampered = dataclasses.replace(envelope, actor_id="evil")
        with self.assertRaises(ValueError):
            derive_grant_id(tampered)

    def test_derive_resealed_tampered_changes_id(self):
        envelope = _envelope()
        resealed = _reseal_envelope(envelope, actor_id="evil")
        self.assertNotEqual(
            derive_grant_id(envelope), derive_grant_id(resealed)
        )

    def test_derive_no_randomness_across_processes(self):
        envelope = _envelope()
        ids = {derive_grant_id(envelope) for _ in range(20)}
        self.assertEqual(len(ids), 1)

    def test_derive_success_is_not_authority(self):
        # Deriving an id does not change the boundary markers.
        envelope = _envelope()
        derive_grant_id(envelope)
        self.assertTrue(envelope.NOT_AUTHORITATIVE_GRANT)
        self.assertTrue(envelope.NOT_SIGNED_AUTHORITY)


class CanonicalPayloadTests(unittest.TestCase):
    """Tests for ``grant_identity_payload``."""

    def test_payload_is_plain_dict(self):
        payload = grant_identity_payload(_identity())
        self.assertIs(type(payload), dict)

    def test_payload_excludes_self_digest(self):
        payload = grant_identity_payload(_identity())
        self.assertNotIn("grant_identity_digest", payload)

    def test_payload_includes_grant_id(self):
        payload = grant_identity_payload(_identity())
        self.assertIn("grant_id", payload)

    def test_payload_has_21_keys(self):
        payload = grant_identity_payload(_identity())
        self.assertEqual(len(payload), 21)

    def test_payload_primary_effect_kept_enum(self):
        payload = grant_identity_payload(_identity())
        self.assertIsInstance(payload["primary_effect"], ActionEffect)

    def test_payload_datetimes_kept_aware(self):
        payload = grant_identity_payload(_identity())
        for key in ("issued_at", "not_before", "expires_at"):
            self.assertIsInstance(payload[key], datetime)
            self.assertIsNotNone(payload[key].tzinfo)

    def test_payload_authority_proof_type_none(self):
        payload = grant_identity_payload(_identity())
        self.assertEqual(payload["authority_proof_type"], "NONE")

    def test_payload_covers_all_non_digest_fields(self):
        candidate = _identity()
        payload = grant_identity_payload(candidate)
        field_names = {
            f.name for f in dataclasses.fields(candidate)
        } - {"grant_identity_digest"}
        self.assertEqual(set(payload.keys()), field_names)


class ComputeDigestTests(unittest.TestCase):
    """Tests for ``compute_grant_identity_digest``."""

    def test_compute_returns_64_lower_hex(self):
        digest = compute_grant_identity_digest(_identity())
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))

    def test_compute_deterministic(self):
        candidate = _identity()
        self.assertEqual(
            compute_grant_identity_digest(candidate),
            compute_grant_identity_digest(candidate),
        )

    def test_compute_ignores_self_digest(self):
        candidate = _identity()
        transient = dataclasses.replace(candidate, grant_identity_digest="")
        self.assertEqual(
            compute_grant_identity_digest(candidate),
            compute_grant_identity_digest(transient),
        )

    def test_compute_changes_with_grant_id(self):
        candidate = _identity()
        other = dataclasses.replace(candidate, grant_id=sha256_hex("other"))
        self.assertNotEqual(
            compute_grant_identity_digest(candidate),
            compute_grant_identity_digest(other),
        )

    def test_sealed_digest_matches_compute(self):
        candidate = _identity()
        transient = dataclasses.replace(candidate, grant_identity_digest="")
        self.assertEqual(
            candidate.grant_identity_digest,
            compute_grant_identity_digest(transient),
        )


class VerifyDigestTests(unittest.TestCase):
    """Tests for the total ``verify_grant_identity_digest`` function."""

    def test_verify_true_for_sealed(self):
        self.assertIs(verify_grant_identity_digest(_identity()), True)

    def test_verify_false_for_transient_empty(self):
        transient = dataclasses.replace(
            _identity(), grant_identity_digest=""
        )
        self.assertIs(verify_grant_identity_digest(transient), False)

    def test_verify_false_for_wrong_type(self):
        self.assertIs(verify_grant_identity_digest(object()), False)

    def test_verify_false_for_none(self):
        self.assertIs(verify_grant_identity_digest(None), False)

    def test_verify_false_for_tampered_field(self):
        tampered = dataclasses.replace(_identity(), actor_id="other-actor")
        self.assertIs(verify_grant_identity_digest(tampered), False)

    def test_verify_false_for_tampered_grant_id(self):
        tampered = dataclasses.replace(
            _identity(), grant_id=sha256_hex("evil")
        )
        self.assertIs(verify_grant_identity_digest(tampered), False)

    def test_verify_false_for_tampered_digest(self):
        tampered = dataclasses.replace(
            _identity(), grant_identity_digest=sha256_hex("bad")
        )
        self.assertIs(verify_grant_identity_digest(tampered), False)

    def test_verify_false_for_uppercase_digest(self):
        candidate = _identity()
        upper = candidate.grant_identity_digest.upper()
        # Constructing with an uppercase digest is itself rejected, so we
        # confirm the validation layer blocks it, keeping verify total.
        with self.assertRaises(ValueError):
            dataclasses.replace(candidate, grant_identity_digest=upper)

    def test_verify_never_raises_on_foreign(self):
        for bad in (0, "", [], {}, 3.14, b"x"):
            self.assertIs(verify_grant_identity_digest(bad), False)


class FactorySuccessTests(unittest.TestCase):
    """Tests for the happy-path factory build."""

    def test_factory_ok_true(self):
        self.assertTrue(_build_identity().ok)

    def test_factory_candidate_not_none(self):
        self.assertIsNotNone(_build_identity().grant_identity_candidate)

    def test_factory_no_failed_checks(self):
        self.assertEqual(_build_identity().failed_checks, ())

    def test_factory_expiry_bound_source_is_requested(self):
        self.assertEqual(
            _build_identity().expiry_bound_source, "requested_expires_at"
        )

    def test_factory_grant_id_matches_derive(self):
        context = _context()
        gate_result = _gate_result(context)
        envelope = _envelope(context, gate_result)
        result = _build_identity(context, gate_result, envelope)
        self.assertEqual(
            result.grant_identity_candidate.grant_id,
            derive_grant_id(envelope),
        )

    def test_factory_digest_verifies(self):
        candidate = _build_identity().grant_identity_candidate
        self.assertIs(verify_grant_identity_digest(candidate), True)

    def test_factory_copies_envelope_fields(self):
        context = _context()
        gate_result = _gate_result(context)
        envelope = _envelope(context, gate_result)
        candidate = _build_identity(
            context, gate_result, envelope
        ).grant_identity_candidate
        self.assertEqual(
            candidate.envelope_candidate_digest,
            envelope.envelope_candidate_digest,
        )
        self.assertEqual(candidate.candidate_digest, envelope.candidate_digest)
        self.assertEqual(candidate.evidence_digest, envelope.evidence_digest)
        self.assertEqual(candidate.issuer_claim_id, envelope.issuer_claim_id)

    def test_factory_deterministic_grant_id(self):
        context = _context()
        gate_result = _gate_result(context)
        envelope = _envelope(context, gate_result)
        a = _build_identity(context, gate_result, envelope)
        b = _build_identity(context, gate_result, envelope)
        self.assertEqual(
            a.grant_identity_candidate.grant_id,
            b.grant_identity_candidate.grant_id,
        )

    def test_factory_deterministic_digest(self):
        context = _context()
        gate_result = _gate_result(context)
        envelope = _envelope(context, gate_result)
        a = _build_identity(context, gate_result, envelope)
        b = _build_identity(context, gate_result, envelope)
        self.assertEqual(
            a.grant_identity_candidate.grant_identity_digest,
            b.grant_identity_candidate.grant_identity_digest,
        )

    def test_factory_authority_proof_none(self):
        candidate = _build_identity().grant_identity_candidate
        self.assertEqual(candidate.authority_proof_type, "NONE")

    def test_factory_has_no_grant_id_parameter(self):
        sig = inspect.signature(build_capability_grant_identity_candidate)
        self.assertNotIn("grant_id", sig.parameters)

    def test_factory_parameters_exact(self):
        sig = inspect.signature(build_capability_grant_identity_candidate)
        self.assertEqual(
            list(sig.parameters.keys()),
            ["context", "gate_result", "envelope_candidate"],
        )


class FactoryFailureTests(unittest.TestCase):
    """Tests for fail-closed factory behavior."""

    def _good_evidence(self, context):
        return evaluate_pre_action_gate(context).evidence_digest

    def test_context_type_invalid(self):
        context = _context()
        result = build_capability_grant_identity_candidate(
            context=object(),
            gate_result=_gate_result(context),
            envelope_candidate=_envelope(context),
        )
        self.assertFalse(result.ok)
        self.assertIn("context_type_invalid", result.failed_checks)

    def test_gate_result_type_invalid(self):
        context = _context()
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=object(),
            envelope_candidate=_envelope(context),
        )
        self.assertIn("gate_result_type_invalid", result.failed_checks)

    def test_envelope_candidate_type_invalid(self):
        context = _context()
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=_gate_result(context),
            envelope_candidate=object(),
        )
        self.assertIn("envelope_candidate_type_invalid", result.failed_checks)

    def test_all_none(self):
        result = build_capability_grant_identity_candidate(
            context=None, gate_result=None, envelope_candidate=None
        )
        self.assertFalse(result.ok)
        self.assertIsNone(result.grant_identity_candidate)

    def test_gate_result_not_allow(self):
        context = _context()
        bad = _malformed_result(
            decision=AuthorizationDecision.DENY,
        )
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=bad,
            envelope_candidate=_envelope(context),
        )
        self.assertIn("gate_result_not_allow", result.failed_checks)

    def test_gate_result_has_failed_checks(self):
        context = _context()
        bad = _malformed_result(
            failed_checks=("some_check",),
        )
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=bad,
            envelope_candidate=_envelope(context),
        )
        self.assertIn("gate_result_has_failed_checks", result.failed_checks)

    def test_gate_result_evidence_empty(self):
        context = _context()
        bad = _malformed_result(evidence_digest="")
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=bad,
            envelope_candidate=_envelope(context),
        )
        self.assertIn(
            "gate_result_evidence_digest_empty", result.failed_checks
        )

    def test_gate_result_boundary_flags_invalid(self):
        context = _context()
        bad = _malformed_result(
            provider_authority_proven=True,
        )
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=bad,
            envelope_candidate=_envelope(context),
        )
        self.assertIn(
            "gate_result_boundary_flags_invalid", result.failed_checks
        )

    def test_gate_result_deny_matched(self):
        context = _context()
        bad = _malformed_result(
            matched_deny_count=3,
        )
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=bad,
            envelope_candidate=_envelope(context),
        )
        self.assertIn("gate_result_deny_matched", result.failed_checks)

    def test_evidence_digest_mismatch(self):
        context = _context()
        bad = _malformed_result(
            evidence_digest=sha256_hex("wrong-evidence"),
        )
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=bad,
            envelope_candidate=_envelope(context),
        )
        self.assertIn("evidence_digest_mismatch", result.failed_checks)

    def test_envelope_candidate_digest_invalid_unsealed(self):
        context = _context()
        gate_result = _gate_result(context)
        unsealed = dataclasses.replace(
            _envelope(context, gate_result), envelope_candidate_digest=""
        )
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=gate_result,
            envelope_candidate=unsealed,
        )
        self.assertIn(
            "envelope_candidate_digest_invalid", result.failed_checks
        )

    def test_envelope_rebuild_mismatch_foreign_actor(self):
        context = _context()
        gate_result = _gate_result(context)
        envelope = _envelope(context, gate_result)
        resealed = _reseal_envelope(envelope, actor_id="evil-actor")
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=gate_result,
            envelope_candidate=resealed,
        )
        self.assertFalse(result.ok)
        self.assertIn("envelope_rebuild_mismatch", result.failed_checks)

    def test_envelope_rebuild_mismatch_different_context(self):
        context_a = _context(request_id="req-A")
        context_b = _context(request_id="req-B")
        gate_result_b = _gate_result(context_b)
        envelope_a = _envelope(context_a)
        # Pass envelope built from A but context/gate from B.
        result = build_capability_grant_identity_candidate(
            context=context_b,
            gate_result=gate_result_b,
            envelope_candidate=envelope_a,
        )
        self.assertFalse(result.ok)

    def test_failed_result_candidate_none(self):
        result = build_capability_grant_identity_candidate(
            context=None, gate_result=None, envelope_candidate=None
        )
        self.assertIsNone(result.grant_identity_candidate)

    def test_failed_result_has_failed_checks(self):
        result = build_capability_grant_identity_candidate(
            context=None, gate_result=None, envelope_candidate=None
        )
        self.assertTrue(result.failed_checks)

    def test_failed_result_expiry_none(self):
        result = build_capability_grant_identity_candidate(
            context=None, gate_result=None, envelope_candidate=None
        )
        self.assertIsNone(result.expiry_bound_source)

    def test_failed_codes_are_known(self):
        result = build_capability_grant_identity_candidate(
            context=object(), gate_result=object(), envelope_candidate=object()
        )
        for code in result.failed_checks:
            self.assertIn(
                code, CapabilityGrantIdentityBuildResult.KNOWN_FAIL_CODES
            )


class FailClosedAttackTests(unittest.TestCase):
    """Adversarial inputs must never leak data or raise."""

    def test_foreign_envelope_no_candidate_leak(self):
        context = _context()
        gate_result = _gate_result(context)
        resealed = _reseal_envelope(
            _envelope(context, gate_result), task_id="evil-task"
        )
        result = build_capability_grant_identity_candidate(
            context=context,
            gate_result=gate_result,
            envelope_candidate=resealed,
        )
        self.assertIsNone(result.grant_identity_candidate)

    def test_factory_never_raises_for_assorted_inputs(self):
        samples = [None, 0, "x", [], {}, object(), 3.14, b"bytes", True]
        for ctx in samples:
            for gr in samples:
                result = build_capability_grant_identity_candidate(
                    context=ctx, gate_result=gr, envelope_candidate=ctx
                )
                self.assertIsInstance(
                    result, CapabilityGrantIdentityBuildResult
                )
                self.assertFalse(result.ok)

    def test_internal_error_folds_closed(self):
        context = _context()
        gate_result = _gate_result(context)
        envelope = _envelope(context, gate_result)
        with mock.patch.object(
            identity_mod,
            "compute_grant_identity_digest",
            side_effect=RuntimeError("boom"),
        ):
            result = build_capability_grant_identity_candidate(
                context=context,
                gate_result=gate_result,
                envelope_candidate=envelope,
            )
        self.assertFalse(result.ok)
        self.assertEqual(
            result.failed_checks, ("internal_error_fail_closed",)
        )

    def test_no_exception_text_in_failed_checks(self):
        context = _context()
        gate_result = _gate_result(context)
        envelope = _envelope(context, gate_result)
        with mock.patch.object(
            identity_mod,
            "_assemble_identity_candidate",
            side_effect=ValueError("secret detail leak"),
        ):
            result = build_capability_grant_identity_candidate(
                context=context,
                gate_result=gate_result,
                envelope_candidate=envelope,
            )
        for code in result.failed_checks:
            self.assertNotIn("secret", code)
            self.assertNotIn("leak", code)

    def test_grant_id_derivation_failure_code(self):
        context = _context()
        gate_result = _gate_result(context)
        envelope = _envelope(context, gate_result)
        with mock.patch.object(
            identity_mod,
            "derive_grant_id",
            side_effect=ValueError("nope"),
        ):
            result = build_capability_grant_identity_candidate(
                context=context,
                gate_result=gate_result,
                envelope_candidate=envelope,
            )
        self.assertIn("grant_id_derivation_failed", result.failed_checks)


class ResultInvariantTests(unittest.TestCase):
    """Tests for ``CapabilityGrantIdentityBuildResult`` invariants."""

    def test_ok_requires_candidate(self):
        with self.assertRaises(ValueError):
            CapabilityGrantIdentityBuildResult(
                ok=True,
                grant_identity_candidate=None,
                failed_checks=(),
                expiry_bound_source="requested",
            )

    def test_ok_rejects_failed_checks(self):
        candidate = _identity()
        with self.assertRaises(ValueError):
            CapabilityGrantIdentityBuildResult(
                ok=True,
                grant_identity_candidate=candidate,
                failed_checks=("internal_error_fail_closed",),
                expiry_bound_source="requested",
            )

    def test_ok_requires_expiry_bound_source(self):
        candidate = _identity()
        with self.assertRaises(ValueError):
            CapabilityGrantIdentityBuildResult(
                ok=True,
                grant_identity_candidate=candidate,
                failed_checks=(),
                expiry_bound_source=None,
            )

    def test_failed_rejects_candidate(self):
        candidate = _identity()
        with self.assertRaises(ValueError):
            CapabilityGrantIdentityBuildResult(
                ok=False,
                grant_identity_candidate=candidate,
                failed_checks=("internal_error_fail_closed",),
                expiry_bound_source=None,
            )

    def test_failed_requires_failed_checks(self):
        with self.assertRaises(ValueError):
            CapabilityGrantIdentityBuildResult(
                ok=False,
                grant_identity_candidate=None,
                failed_checks=(),
                expiry_bound_source=None,
            )

    def test_failed_rejects_expiry_bound_source(self):
        with self.assertRaises(ValueError):
            CapabilityGrantIdentityBuildResult(
                ok=False,
                grant_identity_candidate=None,
                failed_checks=("internal_error_fail_closed",),
                expiry_bound_source="requested",
            )

    def test_unknown_code_rejected(self):
        with self.assertRaises(ValueError):
            CapabilityGrantIdentityBuildResult(
                ok=False,
                grant_identity_candidate=None,
                failed_checks=("totally_unknown_code",),
                expiry_bound_source=None,
            )

    def test_empty_code_rejected(self):
        with self.assertRaises(ValueError):
            CapabilityGrantIdentityBuildResult(
                ok=False,
                grant_identity_candidate=None,
                failed_checks=("",),
                expiry_bound_source=None,
            )

    def test_nonstr_code_rejected(self):
        with self.assertRaises(TypeError):
            CapabilityGrantIdentityBuildResult(
                ok=False,
                grant_identity_candidate=None,
                failed_checks=(123,),
                expiry_bound_source=None,
            )

    def test_failed_checks_must_be_tuple(self):
        with self.assertRaises(TypeError):
            CapabilityGrantIdentityBuildResult(
                ok=False,
                grant_identity_candidate=None,
                failed_checks=["internal_error_fail_closed"],
                expiry_bound_source=None,
            )

    def test_known_fail_codes_superset(self):
        required = {
            "context_type_invalid",
            "gate_result_type_invalid",
            "envelope_candidate_type_invalid",
            "gate_result_not_allow",
            "gate_result_not_ready",
            "gate_result_has_failed_checks",
            "gate_result_deny_matched",
            "gate_result_evidence_digest_empty",
            "gate_result_boundary_flags_invalid",
            "gate_reevaluation_not_clean_allow",
            "recomputed_gate_boundary_flags_invalid",
            "evidence_digest_empty",
            "reevaluation_digest_mismatch",
            "evidence_digest_mismatch",
            "envelope_candidate_digest_invalid",
            "candidate_rebuild_failed",
            "envelope_rebuild_failed",
            "envelope_rebuild_mismatch",
            "grant_id_derivation_failed",
            "internal_error_fail_closed",
        }
        self.assertTrue(
            required.issubset(
                CapabilityGrantIdentityBuildResult.KNOWN_FAIL_CODES
            )
        )


class BoundaryMarkerTests(unittest.TestCase):
    """Tests for the eleven boundary markers."""

    EXPECTED = (
        "NOT_REAL_EXECUTION_PERMISSION",
        "NOT_RUNTIME_ENFORCEABLE_TOKEN",
        "NOT_CAPABILITY_LEASE",
        "NOT_SIGNED_AUTHORITY",
        "NOT_AUTHORITY_PROOF",
        "NOT_REPLAY_PROTECTED",
        "NOT_PERSISTED",
        "NOT_AUTHORITATIVE_GRANT",
        "NOT_ISSUED_GRANT",
        "NOT_LIFECYCLE_STATE",
        "NOT_GRANT_ID_AUTHORITY",
    )

    def test_eleven_markers_present(self):
        for name in self.EXPECTED:
            self.assertTrue(
                hasattr(CapabilityGrantIdentityCandidate, name), name
            )
        self.assertEqual(len(self.EXPECTED), 11)

    def test_all_markers_true(self):
        for name in self.EXPECTED:
            self.assertIs(
                getattr(CapabilityGrantIdentityCandidate, name), True, name
            )

    def test_markers_are_not_instance_fields(self):
        field_names = {
            f.name for f in dataclasses.fields(CapabilityGrantIdentityCandidate)
        }
        for name in self.EXPECTED:
            self.assertNotIn(name, field_names)

    def test_no_forbidden_fields(self):
        forbidden = {
            "status",
            "lifecycle_state",
            "consumed_at",
            "revoked_at",
            "expired_at",
            "usage_limit",
            "nonce",
            "idempotency_key",
            "revision",
            "signature",
            "key_id",
            "authority_id",
            "authority_proof_ref",
            "real_execution_permission",
            "runtime_enforced",
        }
        field_names = {
            f.name for f in dataclasses.fields(CapabilityGrantIdentityCandidate)
        }
        self.assertEqual(field_names & forbidden, set())


class SecurityNoAssertTests(unittest.TestCase):
    """Production code must contain no executable assert statements."""

    def _assert_no_assert(self, module):
        source = inspect.getsource(module)
        tree = ast.parse(source)
        asserts = [
            node for node in ast.walk(tree) if isinstance(node, ast.Assert)
        ]
        self.assertEqual(asserts, [])

    def test_no_assert_in_identity_module(self):
        self._assert_no_assert(identity_mod)

    def test_no_assert_in_validation_module(self):
        from authorization_kernel import (
            capability_grant_identity_validation as v,
        )

        self._assert_no_assert(v)

    def test_grant_id_domain_is_module_level(self):
        field_names = {
            f.name for f in dataclasses.fields(CapabilityGrantIdentityCandidate)
        }
        self.assertNotIn("grant_id_domain", field_names)
        self.assertEqual(GRANT_ID_DOMAIN, "GOAA_AK5B2A_GRANT_ID_V1")

    def test_grant_id_domain_not_classvar(self):
        self.assertFalse(
            hasattr(CapabilityGrantIdentityCandidate, "GRANT_ID_DOMAIN")
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()