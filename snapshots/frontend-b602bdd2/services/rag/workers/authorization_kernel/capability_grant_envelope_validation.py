"""
GOAA Authorization Kernel AK-5B — Capability Grant Envelope Factory
====================================================================
Total, fail-closed factory that derives a CapabilityGrantEnvelopeCandidate
from a trusted AK-4 PreActionGateContext, a *claimed* clean-ALLOW
PreActionGateResult, a *claimed* AK-5A CapabilityGrantCandidate, and issuer
claim metadata. The factory NEVER trusts the caller's claims: it re-runs the
pure gate, re-derives the evidence digest, re-builds the AK-5A candidate from
the context, and requires the rebuilt candidate to match the passed candidate
EXACTLY on every field before wrapping it in an envelope.

Honest boundary (unchanged, restated so it is impossible to miss): a
CapabilityGrantEnvelopeCandidate is NOT a real execution permission, NOT a
runtime-enforceable token, NOT a capability lease, NOT a signed authority,
NOT an authority proof, NOT replay-protected, NOT persisted, NOT an
authoritative grant, and NOT an issued grant. This module creates NO
grant_id, NO status, and performs NO consume / revoke / persistence /
Runtime enforcement.

Fail-closed contract: ANY type error, claim/recompute mismatch, non-clean
ALLOW, boundary-flag forgery, evidence-digest mismatch, candidate rebuild
failure, candidate mismatch, or internal exception yields
CapabilityGrantEnvelopeBuildResult(ok=False, envelope_candidate=None,
failed_checks=...). Raw exception strings are NEVER leaked — only stable,
opaque check codes drawn from KNOWN_FAIL_CODES.

BLOCKER 2 (revision R2): code-membership is enforced at RUNTIME, not just by
convention.
  - CapabilityGrantEnvelopeBuildResult.__post_init__ rejects any failed_checks
    entry that is not a non-empty str drawn from KNOWN_FAIL_CODES, rejects a
    non-None non-str expiry_bound_source, and forces expiry_bound_source to be
    None on every ok=False result.
  - _fail() validates its arguments: an empty call or any unknown code
    collapses DIRECTLY (no recursion) to ("internal_error_fail_closed",), so a
    programming slip can never leak an unknown/empty code out of this module.

BLOCKER 3 (revision R2): _non_empty_str treats whitespace-only issuer metadata
("   ", "\\t") as invalid, mapping it to issuer_claim_id_invalid /
issuer_claim_version_invalid — NOT internal_error_fail_closed.

BLOCKER 5: the AK-5A rebuild is fed the CALLER's ORIGINAL gate_result (not
the recomputed result). The gate is still independently re-run for
verification, but the original claimed result is what flows into the AK-5A
factory so the rebuild reproduces from exactly the inputs the caller
asserted. A passed-but-fake recomputation fails closed with a distinct code.

BLOCKER 7: error codes are stable and collapsed —
  - recomputed boundary-flag failure: "recomputed_gate_boundary_flags_invalid"
  - claimed/passed boundary-flag failure: "gate_result_boundary_flags_invalid"
  - full rebuild field mismatch: "candidate_rebuild_mismatch"
  - AK-5A rebuild failure collapses to exactly ("candidate_rebuild_failed",)
    (no sub-codes leak through).
Every failure result contains ONLY codes in KNOWN_FAIL_CODES.

These functions are pure: no I/O, no subprocess, no network, no clock reads.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md; FINAL_SPEC
GOAA-AK5B-CLAUDE-CODE-20260617-001.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

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
    verify_candidate_digest,
)
from authorization_kernel.capability_validation import (
    build_capability_grant_candidate,
)
from authorization_kernel.capability_grant_envelope import (
    CapabilityGrantEnvelopeCandidate,
    compute_envelope_candidate_digest,
)


# ============================================================
# Stable check-code vocabulary (BLOCKER 7)
# ============================================================

# The complete, closed set of opaque codes this factory may emit. The AK-5A
# rebuild failure is COLLAPSED to a single "candidate_rebuild_failed" code, so
# no AK-5A sub-codes ever leak through here. Tests assert every failed_checks
# entry is a member of this frozenset.
KNOWN_FAIL_CODES: frozenset[str] = frozenset(
    {
        "context_type_invalid",
        "gate_result_type_invalid",
        "candidate_type_invalid",
        "issuer_claim_id_invalid",
        "issuer_claim_version_invalid",
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
        "candidate_rebuild_failed",
        "candidate_digest_invalid",
        "candidate_rebuild_mismatch",
        "internal_error_fail_closed",
    }
)


# ============================================================
# CapabilityGrantEnvelopeBuildResult
# ============================================================

@dataclass(frozen=True)
class CapabilityGrantEnvelopeBuildResult:
    """Total result of build_capability_grant_envelope_candidate().

    Invariants (enforced at runtime in __post_init__):
      - ok=True  -> envelope_candidate is not None AND failed_checks is empty.
      - ok=False -> envelope_candidate is None     AND failed_checks is non-empty
                    AND expiry_bound_source is None.
      - every failed_checks entry is a non-empty str drawn from KNOWN_FAIL_CODES
        (BLOCKER 2): no empty strings, no non-str entries, no unknown codes.
      - expiry_bound_source, when present, is a str (carried up from the AK-5A
        rebuild). It lives ONLY on the build result — never on the envelope and
        never in any digest.

    BLOCKER 6: the success payload field is named `envelope_candidate` (there
    is NO backward-compatible `envelope` alias).
    """

    ok: bool
    envelope_candidate: CapabilityGrantEnvelopeCandidate | None = None
    failed_checks: tuple[str, ...] = field(default_factory=tuple)
    expiry_bound_source: str | None = None

    def __post_init__(self) -> None:
        # ---- structural type checks ----
        if type(self.ok) is not bool:
            raise TypeError("ok must be a bool")
        if not isinstance(self.failed_checks, tuple):
            raise TypeError("failed_checks must be a tuple")
        if self.envelope_candidate is not None and not isinstance(
            self.envelope_candidate, CapabilityGrantEnvelopeCandidate
        ):
            raise TypeError(
                "envelope_candidate must be a CapabilityGrantEnvelopeCandidate or None"
            )
        if self.expiry_bound_source is not None and not isinstance(
            self.expiry_bound_source, str
        ):
            raise TypeError("expiry_bound_source must be a str or None")

        # ---- BLOCKER 2: code membership enforced at runtime ----
        # Each entry must be a non-empty str AND a member of KNOWN_FAIL_CODES.
        for code in self.failed_checks:
            if not isinstance(code, str):
                raise TypeError("failed_checks entries must be str")
            if not code:
                raise ValueError("failed_checks entries must not be empty")
            if code not in KNOWN_FAIL_CODES:
                raise ValueError("failed_checks contains an unknown code")

        # ---- ok / payload consistency ----
        if self.ok:
            if self.envelope_candidate is None:
                raise ValueError("ok=True requires an envelope_candidate")
            if self.failed_checks:
                raise ValueError("ok=True requires empty failed_checks")
        else:
            if self.envelope_candidate is not None:
                raise ValueError("ok=False requires envelope_candidate=None")
            if not self.failed_checks:
                raise ValueError("ok=False requires non-empty failed_checks")
            if self.expiry_bound_source is not None:
                raise ValueError("ok=False requires expiry_bound_source=None")


def _fail(*codes: str) -> CapabilityGrantEnvelopeBuildResult:
    """A fail-closed build result carrying only stable, opaque check codes.

    BLOCKER 2: this helper is itself defensive. An empty call, or any code that
    is not a member of KNOWN_FAIL_CODES, collapses DIRECTLY to
    ("internal_error_fail_closed",). The fallback is constructed inline — _fail
    NEVER calls itself (no recursion) — so a programming slip can never leak an
    unknown or empty code out of this module.
    """
    if not codes or any(code not in KNOWN_FAIL_CODES for code in codes):
        safe_codes: tuple[str, ...] = ("internal_error_fail_closed",)
    else:
        safe_codes = tuple(codes)
    return CapabilityGrantEnvelopeBuildResult(
        ok=False,
        envelope_candidate=None,
        failed_checks=safe_codes,
        expiry_bound_source=None,
    )


# ============================================================
# Clean-ALLOW + boundary-flag helpers (re-checked independently)
# ============================================================

# The five AK-4 boundary flags. A pure AK-4 result keeps each strictly False.
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
    """
    for flag_name in _BOUNDARY_FLAGS:
        if getattr(result, flag_name, True) is not False:
            return False
    return True


def _is_clean_allow(result: PreActionGateResult) -> bool:
    """A clean ALLOW: ALLOW, ready, no failed checks, zero matched denies."""
    return (
        result.decision is AuthorizationDecision.ALLOW
        and result.authorization_ready is True
        and result.failed_checks == ()
        and result.matched_deny_count == 0
    )


def _non_empty_str(value: object) -> bool:
    """True only for a str with at least one non-whitespace character.

    BLOCKER 3: whitespace-only values ("   ", "\\t") are invalid. This routes a
    blank issuer_claim_id / issuer_claim_version to its dedicated
    *_invalid code rather than to internal_error_fail_closed.
    """
    return isinstance(value, str) and bool(value.strip())


# ============================================================
# build_capability_grant_envelope_candidate
# ============================================================

def build_capability_grant_envelope_candidate(
    context: PreActionGateContext,
    gate_result: PreActionGateResult,
    candidate: CapabilityGrantCandidate,
    issuer_claim_id: str,
    issuer_claim_version: str,
) -> CapabilityGrantEnvelopeBuildResult:
    """Build a CapabilityGrantEnvelopeCandidate, fail-closed on any anomaly.

    Any exception is swallowed into a fail-closed result; no raw exception
    text ever escapes. authority_proof_type is always the literal "NONE".
    """
    try:
        return _build(
            context, gate_result, candidate, issuer_claim_id, issuer_claim_version
        )
    except Exception:
        return _fail("internal_error_fail_closed")


def _build(
    context: PreActionGateContext,
    gate_result: PreActionGateResult,
    candidate: CapabilityGrantCandidate,
    issuer_claim_id: str,
    issuer_claim_version: str,
) -> CapabilityGrantEnvelopeBuildResult:
    # ---- Step 1: type-check all five parameters ----
    if not isinstance(context, PreActionGateContext):
        return _fail("context_type_invalid")
    if not isinstance(gate_result, PreActionGateResult):
        return _fail("gate_result_type_invalid")
    if not isinstance(candidate, CapabilityGrantCandidate):
        return _fail("candidate_type_invalid")
    if not _non_empty_str(issuer_claim_id):
        return _fail("issuer_claim_id_invalid")
    if not _non_empty_str(issuer_claim_version):
        return _fail("issuer_claim_version_invalid")

    # ---- Step 2: claimed/passed gate_result must be a clean ALLOW + digest --
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
    # The claimed/passed result must assert NONE of the five AK-4 proofs.
    if not _boundary_flags_all_false(gate_result):
        return _fail("gate_result_boundary_flags_invalid")

    # ---- Step 3: re-run the pure gate; require a clean ALLOW (verification) --
    # BLOCKER 5: this recomputation is for VERIFICATION ONLY. The recomputed
    # result is NOT what feeds the AK-5A rebuild (the original gate_result is).
    recomputed_result = evaluate_pre_action_gate(context)
    if not _is_clean_allow(recomputed_result):
        return _fail("gate_reevaluation_not_clean_allow")
    # BLOCKER 7: the RECOMPUTED boundary-flag failure has its OWN distinct code,
    # separate from the claimed/passed-path "gate_result_boundary_flags_invalid".
    if not _boundary_flags_all_false(recomputed_result):
        return _fail("recomputed_gate_boundary_flags_invalid")

    # ---- Step 4: re-derive evidence digest and bind all three ----
    recomputed_digest = compute_evidence_digest(context)
    if not recomputed_digest:
        return _fail("evidence_digest_empty")
    if recomputed_result.evidence_digest != recomputed_digest:
        return _fail("reevaluation_digest_mismatch")
    if gate_result.evidence_digest != recomputed_digest:
        return _fail("evidence_digest_mismatch")

    # ---- Step 5: rebuild the AK-5A candidate from the CONTEXT ----
    # BLOCKER 5: the AK-5A factory receives the CALLER'S ORIGINAL gate_result,
    # NOT recomputed_result. The AK-5A factory performs its own independent
    # re-evaluation and digest binding internally, so passing the original is
    # safe and ensures the rebuild is reproduced from exactly the asserted
    # inputs. requested_expires_at is taken from the passed candidate so the
    # rebuild reproduces the same window; the rebuilt candidate must match the
    # passed candidate EXACTLY (no "prefer rebuilt value" behaviour).
    #
    # BLOCKER 7: any AK-5A rebuild failure collapses to a single opaque code;
    # AK-5A sub-codes are intentionally NOT forwarded.
    rebuild = build_capability_grant_candidate(
        context=context,
        gate_result=gate_result,
        requested_expires_at=candidate.expires_at,
    )
    if not rebuild.ok or rebuild.candidate is None:
        return _fail("candidate_rebuild_failed")
    rebuilt = rebuild.candidate

    # ---- Step 6: the passed candidate's own digest must verify ----
    if not verify_candidate_digest(candidate):
        return _fail("candidate_digest_invalid")

    # ---- Step 7: full field-by-field equality (frozen dataclass __eq__) ----
    # Compares every field, including candidate_digest; any divergence between
    # the rebuilt (context-derived) candidate and the passed candidate is a
    # hard, fail-closed rejection (BLOCKER 7: "candidate_rebuild_mismatch").
    if rebuilt != candidate:
        return _fail("candidate_rebuild_mismatch")

    # ---- Step 8: construct the envelope from the rebuilt candidate ----
    envelope = CapabilityGrantEnvelopeCandidate(
        envelope_candidate_digest="",
        candidate_digest=rebuilt.candidate_digest,
        evidence_digest=rebuilt.evidence_digest,
        request_id=rebuilt.request_id,
        task_id=rebuilt.task_id,
        actor_id=rebuilt.actor_id,
        primary_effect=rebuilt.primary_effect,
        secondary_effects=rebuilt.secondary_effects,
        resource_scopes=rebuilt.resource_scopes,
        equivalent_action_groups=rebuilt.equivalent_action_groups,
        requested_tool=rebuilt.requested_tool,
        snapshot_id=rebuilt.snapshot_id,
        policy_version=rebuilt.policy_version,
        classification_attestation_hash=rebuilt.classification_attestation_hash,
        issued_at=rebuilt.issued_at,
        not_before=rebuilt.not_before,
        expires_at=rebuilt.expires_at,
        issuer_claim_id=issuer_claim_id,
        issuer_claim_version=issuer_claim_version,
        authority_proof_type="NONE",
    )

    # ---- Step 9: compute and seal the envelope_candidate_digest ----
    digest = compute_envelope_candidate_digest(envelope)
    envelope = dataclasses.replace(envelope, envelope_candidate_digest=digest)

    # ---- BLOCKER 2: expiry_bound_source must be a real AK-5A source str ----
    # On the success path the AK-5A rebuild always reports a non-empty source;
    # if it is somehow absent we fall closed rather than emit an ok=True result
    # with an unusable expiry_bound_source.
    if not _non_empty_str(rebuild.expiry_bound_source):
        return _fail("candidate_rebuild_failed")

    return CapabilityGrantEnvelopeBuildResult(
        ok=True,
        envelope_candidate=envelope,
        failed_checks=(),
        expiry_bound_source=rebuild.expiry_bound_source,
    )
