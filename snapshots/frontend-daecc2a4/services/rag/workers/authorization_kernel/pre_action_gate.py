"""
GOAA Authorization Kernel AK-4 — Pure Pre-Action Gate
======================================================
Combines AK-1/AK-2/AK-3 evidence into a single, pure authorization
decision. No I/O, no subprocess, no network, no clock reads. Every input
is supplied via PreActionGateContext; the only output is a
PreActionGateResult.

Reused real interfaces (verified against worktree @ 5d99956):
  - bind_snapshot()                 (AK-2 snapshot binding)
  - merge_policy_decisions()        (AK-2 strictest-policy precedence)
  - verify_attestation_hash()       (AK-1)
  - classification_matches()        (AK-1)
  - verify_ledger_integrity()       (AK-3)
  - find_matching_denies()          (AK-3)
  - sha256_hex / canonical serialization  (AK-1)

Decision precedence (reused, NOT reimplemented):
    POLICY_CONFLICT > DENY > OUT_OF_SCOPE > REQUIRES_APPROVAL > ALLOW

Fail-closed: any exception, missing required proof, or inconsistency
yields a non-ALLOW decision with authorization_ready=False and NO leakage
of raw exceptions, tokens, or out-of-scope sensitive content into
failed_checks (only stable, opaque check codes).

Honest boundary (a pure AK-4 result NEVER claims these):
    AK4_PROVES_CLASSIFICATION_PROVIDER_AUTHORITY=NO
    AK4_PROVES_GLOBAL_LEDGER_AUTHORITY=NO
    AK4_PROVES_GLOBAL_LEDGER_FRESHNESS=NO
    TOCTOU_FULLY_SOLVED_BY_PURE_AK4=NO
    REAL_EXECUTION_PERMISSION_EMITTED=NO

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §18; FINAL_SPEC
GOAA-AK4-CODE-20260615-002.
"""

from __future__ import annotations

from datetime import datetime

from authorization_kernel.enums import AuthorizationDecision
from authorization_kernel.classification_attestation import (
    ClassificationAttestation,
    classification_matches,
    verify_attestation_hash,
)
from authorization_kernel.snapshot_binding import bind_snapshot
from authorization_kernel.policy_merge import merge_policy_decisions
from authorization_kernel.deny_ledger_state import verify_ledger_integrity
from authorization_kernel.deny_matcher import find_matching_denies
from authorization_kernel.resource_scope import canonical_resource_identity
from authorization_kernel.canonical_serialization import SetLikeTuple, sha256_hex
from authorization_kernel.effect_classifier import RecomputedClassification
from authorization_kernel.authorization_evidence import (
    AuthoritativeLedgerEvidence,
    PreActionGateContext,
    PreActionGateResult,
    TrustedClassificationEvidence,
)

_D = AuthorizationDecision


# ============================================================
# Pure helpers
# ============================================================

def _is_aware(value: object) -> bool:
    """True only for a timezone-aware datetime."""
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _within_window(issued_at: datetime, expires_at: datetime, now: datetime) -> bool:
    """Inclusive validity window: issued_at <= now <= expires_at.

    Mirrors AK-2 expiry semantics (now == expires_at is still valid).
    """
    return issued_at <= now <= expires_at


def _recomputed_matches_attestation(
    recomputed: RecomputedClassification,
    attestation: ClassificationAttestation,
) -> bool:
    """Whether evidence's recomputed classification equals the attestation's."""
    return (
        recomputed.primary_effect == attestation.recomputed_primary_effect
        and recomputed.secondary_effects
        == attestation.recomputed_secondary_effects
        and recomputed.equivalent_action_groups
        == attestation.recomputed_equivalent_groups
    )


def _scope_identities(scopes: tuple) -> SetLikeTuple:
    """Stable set-like wrapper of canonical resource identities for digest."""
    idents: list[str] = []
    for scope in scopes:
        try:
            idents.append(canonical_resource_identity(scope))
        except Exception:
            idents.append("__invalid_scope__")
    return SetLikeTuple(tuple(idents))


def _classification_evidence_payload(
    evidence: TrustedClassificationEvidence | None,
) -> object:
    if evidence is None:
        return None
    provider = evidence.provider
    return {
        "subject_request_id": evidence.subject_request_id,
        "subject_task_id": evidence.subject_task_id,
        "classification_policy_version": evidence.classification_policy_version,
        "attestation_hash": evidence.attestation_hash,
        "recomputed_primary_effect": evidence.recomputed.primary_effect,
        "recomputed_secondary_effects": evidence.recomputed.secondary_effects,
        "recomputed_equivalent_groups": evidence.recomputed.equivalent_action_groups,
        "issued_at": evidence.issued_at,
        "expires_at": evidence.expires_at,
        "provider": None
        if provider is None
        else {
            "provider_id": provider.provider_id,
            "issued_at": provider.issued_at,
            "expires_at": provider.expires_at,
        },
    }


def _ledger_evidence_payload(
    evidence: AuthoritativeLedgerEvidence | None,
) -> object:
    if evidence is None:
        return None
    return {
        "ledger_tip_hash": evidence.ledger_tip_hash,
        "ledger_entry_count": evidence.ledger_entry_count,
        "decision_time": evidence.decision_time,
        "issued_at": evidence.issued_at,
        "expires_at": evidence.expires_at,
    }


def _build_evidence_payload(context: PreActionGateContext) -> dict:
    """Canonical, digest-able view of every pure datum the decision depends on.

    Excludes the digest itself. Set-like collections are wrapped so that
    semantically-equal inputs in different orders hash identically; every
    security-relevant field is included so any change alters the digest.
    """
    req = context.request
    snap = context.snapshot
    att = context.attestation
    ledger = context.ledger
    observed_tip = ledger.entries[-1].entry_hash if ledger.entries else None
    observed_count = len(ledger.entries)

    return {
        "request": {
            "request_id": req.request_id,
            "task_id": req.task_id,
            "authorization_snapshot_id": req.authorization_snapshot_id,
            "actor_id": req.actor_id,
            "primary_effect": req.primary_effect,
            "secondary_effects": req.secondary_effects,
            "resource_scopes": _scope_identities(req.resource_scopes),
            "equivalent_action_groups": req.equivalent_action_groups,
            "requested_tool": req.requested_tool,
            "parameters_digest": req.parameters_digest,
            "classification_policy_version": req.classification_policy_version,
        },
        "snapshot": {
            "snapshot_id": snap.snapshot_id,
            "task_id": snap.task_id,
            "policy_version": snap.policy_version,
            "snapshot_hash": snap.snapshot_hash,
            "created_at": snap.created_at,
            "expires_at": snap.expires_at,
            "allowed_effects": snap.allowed_effects,
            "allowed_equivalent_groups": snap.allowed_equivalent_groups,
            "allowed_resource_scopes": _scope_identities(snap.allowed_resource_scopes),
        },
        "attestation": {
            "classification_policy_version": att.classification_policy_version,
            "classification_attestation_hash": att.classification_attestation_hash,
            "declared_primary_effect": att.declared_primary_effect,
            "declared_secondary_effects": att.declared_secondary_effects,
            "recomputed_primary_effect": att.recomputed_primary_effect,
            "recomputed_secondary_effects": att.recomputed_secondary_effects,
            "declared_equivalent_groups": att.declared_equivalent_groups,
            "recomputed_equivalent_groups": att.recomputed_equivalent_groups,
        },
        "classification_evidence": _classification_evidence_payload(
            context.classification_evidence
        ),
        "ledger_evidence": _ledger_evidence_payload(context.ledger_evidence),
        "ledger_observed": {
            "tip_hash": observed_tip,
            "entry_count": observed_count,
        },
        "decision_time": context.decision_time,
        "requires_human_approval": context.requires_human_approval,
        "human_approval_valid": context.human_approval_valid,
    }


def compute_evidence_digest(context: PreActionGateContext) -> str:
    """Public, pure digest of the gate's evidence (reuses AK-1 sha256_hex)."""
    return sha256_hex(_build_evidence_payload(context))


def _fail_closed(decision: AuthorizationDecision, failed: tuple[str, ...]) -> PreActionGateResult:
    """A non-ready result. evidence_digest omitted (cannot/should not hash)."""
    return PreActionGateResult(
        decision=decision,
        authorization_ready=False,
        failed_checks=failed,
        evidence_digest="",
        matched_deny_count=0,
    )


# ============================================================
# evaluate_pre_action_gate
# ============================================================

def evaluate_pre_action_gate(context: PreActionGateContext) -> PreActionGateResult:
    """Evaluate the pure AK-4 Pre-Action Gate.

    Fixed evaluation order (steps merged only where a real interface
    demands it, never skipping a security check):

      1. context type + aware decision_time
      2. request <-> classification-evidence identity binding
      3. attestation hash validity
      4. declared vs recomputed classification agreement
      5. policy-version coherence (request / attestation / evidence)
      6. classification evidence binding, provider presence, validity window
      7. AK-2 bind_snapshot()
      8. ledger evidence binding (tip / count / decision_time) + window
      9. AK-3 verify_ledger_integrity()
     10. AK-3 find_matching_denies()  (+ match-context binding, active denies)
     11. human approval routing
     12. canonical evidence digest
     13. merge_policy_decisions() + authorization_ready

    Any exception fails closed (authorization_ready=False) without leaking
    sensitive content.
    """
    try:
        return _evaluate(context)
    except Exception:
        # Opaque, stable code only — never leak the raw exception.
        return _fail_closed(_D.OUT_OF_SCOPE, ("internal_error_fail_closed",))


def _evaluate(context: PreActionGateContext) -> PreActionGateResult:
    # ---- Step 1: context type + aware decision_time ----
    if not isinstance(context, PreActionGateContext):
        return _fail_closed(_D.POLICY_CONFLICT, ("context_type_invalid",))
    decision_time = context.decision_time
    if not _is_aware(decision_time):
        return _fail_closed(_D.POLICY_CONFLICT, ("decision_time_not_aware",))

    req = context.request
    snap = context.snapshot
    att = context.attestation
    ledger = context.ledger
    cls_ev = context.classification_evidence
    led_ev = context.ledger_evidence

    decisions: list[AuthorizationDecision] = []
    failed: list[str] = []

    def fail(code: str, decision: AuthorizationDecision) -> None:
        failed.append(code)
        decisions.append(decision)

    # ---- Step 2: request <-> classification-evidence identity binding ----
    if cls_ev is None:
        fail("classification_evidence_missing", _D.OUT_OF_SCOPE)
    else:
        if cls_ev.subject_request_id != req.request_id:
            fail("classification_evidence_request_mismatch", _D.POLICY_CONFLICT)
        if cls_ev.subject_task_id != req.task_id:
            fail("classification_evidence_task_mismatch", _D.POLICY_CONFLICT)

    # ---- Step 3: attestation hash validity ----
    if not verify_attestation_hash(att):
        fail("attestation_hash_invalid", _D.POLICY_CONFLICT)

    # ---- Step 4: declared vs recomputed classification agreement ----
    if not classification_matches(att):
        fail("classification_mismatch", _D.POLICY_CONFLICT)

    # ---- Step 5: policy-version coherence ----
    if req.classification_policy_version != att.classification_policy_version:
        fail("request_attestation_policy_version_mismatch", _D.POLICY_CONFLICT)
    if cls_ev is not None and (
        cls_ev.classification_policy_version != att.classification_policy_version
    ):
        fail("classification_evidence_policy_version_mismatch", _D.POLICY_CONFLICT)

    # ---- Step 6: classification evidence binding + provider + window ----
    if cls_ev is not None:
        if cls_ev.attestation_hash != att.classification_attestation_hash:
            fail("classification_evidence_hash_mismatch", _D.POLICY_CONFLICT)
        if not _recomputed_matches_attestation(cls_ev.recomputed, att):
            fail("classification_evidence_recomputed_mismatch", _D.POLICY_CONFLICT)
        # Provider presence is necessary (authority is NOT proven by AK-4).
        if cls_ev.provider is None:
            fail("provider_evidence_missing", _D.OUT_OF_SCOPE)
        elif not _within_window(
            cls_ev.provider.issued_at, cls_ev.provider.expires_at, decision_time
        ):
            fail("provider_evidence_outside_validity_window", _D.OUT_OF_SCOPE)
        if not _within_window(cls_ev.issued_at, cls_ev.expires_at, decision_time):
            fail("classification_evidence_outside_validity_window", _D.OUT_OF_SCOPE)

    # ---- Step 7: AK-2 snapshot binding ----
    try:
        binding = bind_snapshot(req, snap, decision_time)
    except Exception:
        binding = None
    if binding is None:
        fail("snapshot_binding_error", _D.POLICY_CONFLICT)
    else:
        decisions.append(binding.decision)
        if binding.decision is not _D.ALLOW:
            for code in binding.failed_checks:
                failed.append(f"snapshot:{code}")

    # ---- Step 8: ledger evidence binding (tip / count / decision_time) ----
    observed_tip = ledger.entries[-1].entry_hash if ledger.entries else None
    observed_count = len(ledger.entries)
    if led_ev is None:
        fail("ledger_evidence_missing", _D.OUT_OF_SCOPE)
    else:
        if led_ev.ledger_tip_hash != observed_tip:
            fail("ledger_evidence_tip_mismatch", _D.POLICY_CONFLICT)
        if led_ev.ledger_entry_count != observed_count:
            fail("ledger_evidence_count_mismatch", _D.POLICY_CONFLICT)
        if led_ev.decision_time != decision_time:
            fail("ledger_evidence_decision_time_mismatch", _D.POLICY_CONFLICT)
        if not _within_window(led_ev.issued_at, led_ev.expires_at, decision_time):
            fail("ledger_evidence_outside_validity_window", _D.OUT_OF_SCOPE)

    # ---- Step 9: AK-3 ledger integrity ----
    integrity = verify_ledger_integrity(ledger)
    if not integrity.valid:
        fail("ledger_integrity_invalid", _D.OUT_OF_SCOPE)

    # ---- Step 10: AK-3 matcher (binds to same request + decision_time) ----
    match_list = find_matching_denies(
        ledger,
        req.primary_effect,
        req.secondary_effects,
        req.equivalent_action_groups,
        req.resource_scopes,
        decision_time,
        observed_ledger=ledger,
    )
    fold = match_list.fold_result
    matcher_valid = (
        fold is not None
        and fold.valid
        and fold.fold_attemptable
        and not match_list.stale_fold
    )
    if not matcher_valid:
        fail("matcher_invalid", _D.OUT_OF_SCOPE)
    else:
        mc = match_list.match_context
        if mc is not None:
            if mc.evaluated_at != decision_time:
                fail("matcher_decision_time_mismatch", _D.POLICY_CONFLICT)
            if mc.ledger_tip_hash != observed_tip:
                fail("matcher_tip_mismatch", _D.POLICY_CONFLICT)
            if mc.ledger_entry_count != observed_count:
                fail("matcher_count_mismatch", _D.POLICY_CONFLICT)

    active = [r for r in match_list.matched_denies if r.matched]
    matched_deny_count = len(active)
    if matched_deny_count > 0:
        fail("active_deny_matched", _D.DENY)

    # ---- Step 11: human approval routing ----
    if context.requires_human_approval and not context.human_approval_valid:
        fail("human_approval_required", _D.REQUIRES_APPROVAL)

    # ---- Step 12: canonical evidence digest ----
    try:
        digest = compute_evidence_digest(context)
    except Exception:
        digest = ""
        fail("evidence_digest_error", _D.OUT_OF_SCOPE)

    # ---- Step 13: merge + authorization_ready ----
    final = merge_policy_decisions(tuple(decisions))
    authorization_ready = (
        final is _D.ALLOW
        and not failed
        and digest != ""
        and matched_deny_count == 0
    )

    return PreActionGateResult(
        decision=final,
        authorization_ready=authorization_ready,
        failed_checks=tuple(failed),
        evidence_digest=digest,
        matched_deny_count=matched_deny_count,
    )
