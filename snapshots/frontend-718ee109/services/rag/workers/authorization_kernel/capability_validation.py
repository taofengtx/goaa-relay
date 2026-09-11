"""
GOAA Authorization Kernel AK-5A — Capability Grant Candidate Factory
====================================================================
Total, fail-closed factory that derives a CapabilityGrantCandidate from a
trusted AK-4 PreActionGateContext and a *claimed* clean-ALLOW
PreActionGateResult. The factory NEVER trusts the caller's claims: it
re-runs the pure gate, re-derives the evidence digest, binds the claimed
result to the recomputed result, and derives every security-relevant field
from the context itself.

Honest boundary (unchanged from AK-4, restated so it is impossible to miss):

    A CapabilityGrantCandidate is NOT a real execution permission, NOT a
    runtime-enforceable token, NOT a capability lease, and NOT a signed
    authority. This module creates NO grant_id, NO status, and performs NO
    consume / revoke / persistence / Runtime enforcement. See
    capability_models.CapabilityGrantCandidate.

Fail-closed contract: ANY type error, claim/recompute mismatch, non-clean
ALLOW, missing proof, expiry-bound failure, or internal exception yields
CapabilityGrantBuildResult(ok=False, candidate=None, failed_checks=...).
Raw exception strings are NEVER leaked — only stable, opaque check codes.

These functions are pure: no I/O, no subprocess, no network, no clock reads.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md; FINAL_SPEC
GOAA-AK5A-CLAUDE-CODE-20260617-001.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime

from authorization_kernel.enums import AuthorizationDecision
from authorization_kernel.authorization_evidence import (
    PreActionGateContext,
    PreActionGateResult,
)
from authorization_kernel.pre_action_gate import (
    compute_evidence_digest,
    evaluate_pre_action_gate,
)
from authorization_kernel.capability_models import (
    CapabilityGrantCandidate,
    compute_candidate_digest,
)


# ============================================================
# Expiry derivation
# ============================================================

@dataclass(frozen=True)
class CandidateExpiry:
    """Result of derive_candidate_expiry().

    On success (ok=True): issued_at / not_before / expires_at are aware
    datetimes, source names the evidence that produced the binding bound,
    and failed_checks is empty. On failure (ok=False): the datetimes and
    source are None and failed_checks is non-empty.
    """

    ok: bool
    issued_at: datetime | None = None
    not_before: datetime | None = None
    expires_at: datetime | None = None
    source: str | None = None
    failed_checks: tuple[str, ...] = field(default_factory=tuple)


def _is_aware(value: object) -> bool:
    """True only for a timezone-aware datetime."""
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _expiry_fail(codes: tuple[str, ...]) -> CandidateExpiry:
    return CandidateExpiry(ok=False, failed_checks=codes)


def derive_candidate_expiry(
    context: PreActionGateContext,
    requested_expires_at: datetime | None = None,
) -> CandidateExpiry:
    """Derive a bounded validity window for a candidate from context evidence.

        issued_at  = context.decision_time
        not_before = context.decision_time
        derived_max = min(
            snapshot.expires_at,
            classification_evidence.expires_at,
            classification_evidence.provider.expires_at,
            ledger_evidence.expires_at,
        )   # over whichever of these are actually present

    The normal factory path always supplies at least one real datetime upper
    bound. When NONE is available the result is ok=False with
    'expiry_bound_missing' — expires_at is NEVER None.

    If requested_expires_at is given it must be timezone-aware, >= decision
    time, and <= derived_max; otherwise the request is HARD-rejected (never
    clamped).
    """
    if not isinstance(context, PreActionGateContext):
        return _expiry_fail(("context_type_invalid",))

    decision_time = context.decision_time
    if not _is_aware(decision_time):
        return _expiry_fail(("decision_time_not_aware",))

    issued_at = decision_time
    not_before = decision_time

    # Collect candidate upper bounds in a fixed priority order so the chosen
    # source is deterministic on ties.
    bounds: list[tuple[datetime, str]] = []
    snap = context.snapshot
    if snap.expires_at is not None:
        bounds.append((snap.expires_at, "snapshot"))
    cls_ev = context.classification_evidence
    if cls_ev is not None:
        bounds.append((cls_ev.expires_at, "classification_evidence"))
        if cls_ev.provider is not None:
            bounds.append((cls_ev.provider.expires_at, "provider_evidence"))
    led_ev = context.ledger_evidence
    if led_ev is not None:
        bounds.append((led_ev.expires_at, "ledger_evidence"))

    if not bounds:
        return _expiry_fail(("expiry_bound_missing",))

    derived_max, source = bounds[0]
    for value, src in bounds[1:]:
        if value < derived_max:
            derived_max, source = value, src

    # A bound earlier than the decision time can never yield a valid window.
    if derived_max < not_before:
        return _expiry_fail(("expiry_bound_before_decision_time",))

    if requested_expires_at is not None:
        if not _is_aware(requested_expires_at):
            return _expiry_fail(("requested_expiry_not_aware",))
        if requested_expires_at < decision_time:
            return _expiry_fail(("requested_expiry_before_decision_time",))
        if requested_expires_at > derived_max:
            return _expiry_fail(("requested_expiry_exceeds_derived_max",))
        return CandidateExpiry(
            ok=True,
            issued_at=issued_at,
            not_before=not_before,
            expires_at=requested_expires_at,
            source="requested_expires_at",
        )

    return CandidateExpiry(
        ok=True,
        issued_at=issued_at,
        not_before=not_before,
        expires_at=derived_max,
        source=source,
    )


# ============================================================
# CapabilityGrantBuildResult
# ============================================================

@dataclass(frozen=True)
class CapabilityGrantBuildResult:
    """Total result of build_capability_grant_candidate().

    Invariants (enforced below):
      - ok=True  -> candidate is not None AND failed_checks is empty.
      - ok=False -> candidate is None     AND failed_checks is non-empty.

    expiry_bound_source records which evidence produced the binding expiry
    bound. It lives ONLY on the build result — it is never a candidate field
    and never enters the candidate_digest.
    """

    ok: bool
    candidate: CapabilityGrantCandidate | None = None
    failed_checks: tuple[str, ...] = field(default_factory=tuple)
    expiry_bound_source: str | None = None

    def __post_init__(self) -> None:
        if type(self.ok) is not bool:
            raise TypeError("ok must be a bool")
        if not isinstance(self.failed_checks, tuple):
            raise TypeError("failed_checks must be a tuple")
        if self.candidate is not None and not isinstance(
            self.candidate, CapabilityGrantCandidate
        ):
            raise TypeError("candidate must be a CapabilityGrantCandidate or None")
        if self.ok:
            if self.candidate is None:
                raise ValueError("ok=True requires a candidate")
            if self.failed_checks:
                raise ValueError("ok=True requires empty failed_checks")
        else:
            if self.candidate is not None:
                raise ValueError("ok=False requires candidate=None")
            if not self.failed_checks:
                raise ValueError("ok=False requires non-empty failed_checks")


def _fail(*codes: str) -> CapabilityGrantBuildResult:
    """A fail-closed build result carrying only stable, opaque check codes."""
    return CapabilityGrantBuildResult(
        ok=False,
        candidate=None,
        failed_checks=tuple(codes),
        expiry_bound_source=None,
    )


def _is_clean_allow(result: PreActionGateResult) -> bool:
    """A clean ALLOW: ALLOW, ready, no failed checks, zero matched denies."""
    return (
        result.decision is AuthorizationDecision.ALLOW
        and result.authorization_ready is True
        and result.failed_checks == ()
        and result.matched_deny_count == 0
    )


# The five AK-4 boundary flags. A pure AK-4 result keeps every one strictly
# False (see authorization_evidence.PreActionGateResult). The factory must
# re-verify them on BOTH the claimed and recomputed results and refuse to
# trust any malformed result — e.g. one built via object.__new__ to bypass
# AK-4's __post_init__ — that asserts any of these proofs.
_BOUNDARY_FLAGS = (
    "provider_authority_proven",
    "global_ledger_authority_proven",
    "global_ledger_freshness_proven",
    "toctou_resolved",
    "real_execution_permission",
)


def _boundary_flags_all_false(result: PreActionGateResult) -> bool:
    """True only if all five AK-4 boundary flags are strictly False.

    getattr defaults to True (a non-False sentinel) so a malformed result that
    LACKS a flag entirely is treated as invalid rather than silently trusted.
    Any flag that is not exactly False (including truthy non-bools) fails.
    """
    for flag_name in _BOUNDARY_FLAGS:
        if getattr(result, flag_name, True) is not False:
            return False
    return True


# ============================================================
# build_capability_grant_candidate
# ============================================================

def build_capability_grant_candidate(
    context: PreActionGateContext,
    gate_result: PreActionGateResult,
    requested_expires_at: datetime | None = None,
) -> CapabilityGrantBuildResult:
    """Build a CapabilityGrantCandidate, fail-closed on any anomaly.

    Steps (every one is a security check; none is skipped):
      1. Type-check context and gate_result (and requested_expires_at).
      2. Verify the *claimed* gate_result is a clean ALLOW with a digest and
         that all five AK-4 boundary flags are strictly False.
      3. Re-run evaluate_pre_action_gate(context) — never trust the claim.
      4. Verify the re-evaluation is itself a clean ALLOW with all five
         boundary flags strictly False.
      5. Re-derive the evidence digest via compute_evidence_digest(context).
      6. Bind: recomputed digest == re-evaluation digest == claimed digest.
      7. Derive a bounded expiry window from context evidence.
      8. Derive ALL candidate fields from the CONTEXT (never the caller's
         re-declared request/task/actor/effects/resources/policy).
      9. Construct the candidate and compute its candidate_digest.

    Any exception is swallowed into a fail-closed result; no raw exception
    text ever escapes.
    """
    try:
        return _build(context, gate_result, requested_expires_at)
    except Exception:
        return _fail("internal_error_fail_closed")


def _build(
    context: PreActionGateContext,
    gate_result: PreActionGateResult,
    requested_expires_at: datetime | None,
) -> CapabilityGrantBuildResult:
    # ---- Step 1: types ----
    if not isinstance(context, PreActionGateContext):
        return _fail("context_type_invalid")
    if not isinstance(gate_result, PreActionGateResult):
        return _fail("gate_result_type_invalid")
    if requested_expires_at is not None and not isinstance(
        requested_expires_at, datetime
    ):
        return _fail("requested_expiry_type_invalid")

    # ---- Step 2: claimed gate_result must be a clean ALLOW with a digest ----
    if gate_result.decision is not AuthorizationDecision.ALLOW:
        return _fail("gate_result_not_allow")
    if gate_result.authorization_ready is not True:
        return _fail("gate_result_not_ready")
    if gate_result.failed_checks != ():
        return _fail("gate_result_has_failed_checks")
    if gate_result.matched_deny_count != 0:
        return _fail("gate_result_deny_matched")
    if not gate_result.evidence_digest:
        return _fail("gate_result_evidence_digest_empty")
    # The claimed result must assert NONE of the five AK-4 boundary proofs.
    if not _boundary_flags_all_false(gate_result):
        return _fail("gate_result_boundary_flags_invalid")

    # ---- Step 3-4: re-run the pure gate and require a clean ALLOW ----
    recomputed_result = evaluate_pre_action_gate(context)
    if not _is_clean_allow(recomputed_result):
        return _fail("gate_reevaluation_not_clean_allow")
    # The recomputed result must also keep every boundary flag strictly False.
    if not _boundary_flags_all_false(recomputed_result):
        return _fail("gate_result_boundary_flags_invalid")

    # ---- Step 5-6: re-derive evidence digest and bind all three ----
    recomputed_digest = compute_evidence_digest(context)
    if not recomputed_digest:
        return _fail("evidence_digest_empty")
    if recomputed_result.evidence_digest != recomputed_digest:
        return _fail("reevaluation_digest_mismatch")
    if gate_result.evidence_digest != recomputed_digest:
        return _fail("evidence_digest_mismatch")

    # ---- Step 7: bounded expiry ----
    expiry = derive_candidate_expiry(context, requested_expires_at)
    if not expiry.ok:
        return _fail(*expiry.failed_checks)

    # ---- Step 8-9: derive fields from context, construct, digest ----
    req = context.request
    snap = context.snapshot
    att = context.attestation

    candidate = CapabilityGrantCandidate(
        candidate_digest="",
        evidence_digest=recomputed_digest,
        request_id=req.request_id,
        task_id=req.task_id,
        actor_id=req.actor_id,
        primary_effect=req.primary_effect,
        secondary_effects=req.secondary_effects,
        resource_scopes=req.resource_scopes,
        equivalent_action_groups=req.equivalent_action_groups,
        requested_tool=req.requested_tool,
        snapshot_id=snap.snapshot_id,
        policy_version=snap.policy_version,
        classification_attestation_hash=att.classification_attestation_hash,
        issued_at=expiry.issued_at,
        not_before=expiry.not_before,
        expires_at=expiry.expires_at,
    )
    digest = compute_candidate_digest(candidate)
    candidate = dataclasses.replace(candidate, candidate_digest=digest)

    return CapabilityGrantBuildResult(
        ok=True,
        candidate=candidate,
        failed_checks=(),
        expiry_bound_source=expiry.source,
    )
