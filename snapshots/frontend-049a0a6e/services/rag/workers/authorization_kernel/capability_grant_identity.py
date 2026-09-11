"""AK-5B2A Capability Grant Identity Candidate.

This module derives a stable *content identity* for an AK-5B1 capability
grant envelope candidate and wraps it in a fail-closed identity candidate.

The identity layer answers a single question: *given a sealed envelope
candidate, what is its deterministic, domain-separated content identity?*
The answer is the ``grant_id`` produced by :func:`derive_grant_id`. The
``grant_id`` is a pure function of the envelope's self-digest under a fixed
domain constant. It is **not** an authority issuance, not a signature, and
not a lifecycle token. Deriving an identity proves nothing about authority;
it only names content that has already been verified by lower layers.

Like every artifact in the Authorization Kernel up to this point, the
identity candidate is a content-addressed, fail-closed *candidate*.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from authorization_kernel.pre_action_gate import compute_evidence_digest
from authorization_kernel.canonical_serialization import SetLikeTuple, sha256_hex
from authorization_kernel.capability_grant_envelope import (
    CapabilityGrantEnvelopeCandidate,
    verify_envelope_candidate_digest,
)
from authorization_kernel.capability_grant_envelope_validation import (
    build_capability_grant_envelope_candidate,
)
from authorization_kernel.capability_grant_identity_validation import (
    validate_identity_candidate_fields,
)
from authorization_kernel.capability_validation import build_capability_grant_candidate
from authorization_kernel.enums import ActionEffect
from authorization_kernel.pre_action_gate import (
    AuthorizationDecision,
    PreActionGateContext,
    PreActionGateResult,
    evaluate_pre_action_gate,
)
from authorization_kernel.resource_scope import TypedResourceScope, canonical_resource_identity


__all__ = [
    "GRANT_ID_DOMAIN",
    "CapabilityGrantIdentityCandidate",
    "CapabilityGrantIdentityBuildResult",
    "build_capability_grant_identity_candidate",
    "derive_grant_id",
    "compute_grant_identity_digest",
    "verify_grant_identity_digest",
    "grant_identity_payload",
]


# Module-level domain constant. This is intentionally NOT a ClassVar on the
# dataclass and NOT an instance field: it never appears in the instance and
# never appears in the content digest. It only domain-separates the derived
# grant identity from any other sha256 input.
GRANT_ID_DOMAIN = "GOAA_AK5B2A_GRANT_ID_V1"


@dataclass(frozen=True)
class CapabilityGrantIdentityCandidate:
    """A fail-closed, content-addressed capability grant identity candidate."""

    grant_identity_digest: str
    grant_id: str

    envelope_candidate_digest: str
    candidate_digest: str
    evidence_digest: str

    request_id: str
    task_id: str
    actor_id: str

    primary_effect: ActionEffect
    secondary_effects: frozenset[ActionEffect]
    resource_scopes: tuple[TypedResourceScope, ...]
    equivalent_action_groups: frozenset[str]

    requested_tool: str

    snapshot_id: str
    policy_version: str
    classification_attestation_hash: str

    issued_at: datetime
    not_before: datetime
    expires_at: datetime

    issuer_claim_id: str
    issuer_claim_version: str
    authority_proof_type: str

    # Boundary markers. These are ClassVars, not instance fields, and never
    # appear in the content digest. They document what this artifact is NOT.
    NOT_REAL_EXECUTION_PERMISSION: ClassVar[bool] = True
    NOT_RUNTIME_ENFORCEABLE_TOKEN: ClassVar[bool] = True
    NOT_CAPABILITY_LEASE: ClassVar[bool] = True
    NOT_SIGNED_AUTHORITY: ClassVar[bool] = True
    NOT_AUTHORITY_PROOF: ClassVar[bool] = True
    NOT_REPLAY_PROTECTED: ClassVar[bool] = True
    NOT_PERSISTED: ClassVar[bool] = True
    NOT_AUTHORITATIVE_GRANT: ClassVar[bool] = True
    NOT_ISSUED_GRANT: ClassVar[bool] = True
    NOT_LIFECYCLE_STATE: ClassVar[bool] = True
    NOT_GRANT_ID_AUTHORITY: ClassVar[bool] = True

    def __post_init__(self) -> None:
        validate_identity_candidate_fields(self)


@dataclass(frozen=True)
class CapabilityGrantIdentityBuildResult:
    """Result of attempting to build a grant identity candidate."""

    ok: bool
    grant_identity_candidate: CapabilityGrantIdentityCandidate | None
    failed_checks: tuple[str, ...]
    expiry_bound_source: str | None

    KNOWN_FAIL_CODES: ClassVar[frozenset[str]] = frozenset(
        {
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
    )

    def __post_init__(self) -> None:
        _validate_identity_build_result(self)


def _validate_identity_build_result(
    result: CapabilityGrantIdentityBuildResult,
) -> None:
    """Enforce the result invariants at runtime, fail-closed."""

    if not isinstance(result.ok, bool):
        raise TypeError("ok must be a bool")

    failed_checks = result.failed_checks
    if not isinstance(failed_checks, tuple):
        raise TypeError("failed_checks must be a tuple")

    for code in failed_checks:
        if not isinstance(code, str):
            raise TypeError("failed_checks entries must be str")
        if not code:
            raise ValueError("failed_checks entries must be non-empty")
        if code not in CapabilityGrantIdentityBuildResult.KNOWN_FAIL_CODES:
            raise ValueError("unknown failed_checks code")

    if result.ok:
        if result.grant_identity_candidate is None:
            raise ValueError("ok result requires a grant_identity_candidate")
        if failed_checks:
            raise ValueError("ok result must not carry failed_checks")
        if result.expiry_bound_source is None:
            raise ValueError("ok result requires expiry_bound_source")
    else:
        if result.grant_identity_candidate is not None:
            raise ValueError("failed result must not carry a candidate")
        if failed_checks == ():
            raise ValueError("failed result requires failed_checks")
        if result.expiry_bound_source is not None:
            raise ValueError(
                "failed result must not carry expiry_bound_source"
            )


def _is_strict_sha256_hex(value: object) -> bool:
    """Return ``True`` iff ``value`` is a 64-char lowercase hex string."""

    if not isinstance(value, str):
        return False
    if len(value) != 64:
        return False
    return all(c in "0123456789abcdef" for c in value)


def _constant_time_equals(left: str, right: str) -> bool:
    """Constant-time string comparison wrapper."""

    import hmac

    return hmac.compare_digest(left, right)


def derive_grant_id(value: object) -> str:
    """Derive the stable, domain-separated content identity of an envelope.

    ``value`` must be a sealed :class:`CapabilityGrantEnvelopeCandidate`. The
    returned ``grant_id`` is a pure function of the envelope's self-digest
    under :data:`GRANT_ID_DOMAIN`. It uses no clock, no randomness, no UUID,
    no database, and no process state.

    A successful derivation is **not** authority verification: it only names
    content that lower layers have already verified.
    """

    if not isinstance(value, CapabilityGrantEnvelopeCandidate):
        raise TypeError("value must be a CapabilityGrantEnvelopeCandidate")

    if verify_envelope_candidate_digest(value) is not True:
        raise ValueError("envelope candidate must be sealed and verifiable")

    envelope_digest = value.envelope_candidate_digest
    if not _is_strict_sha256_hex(envelope_digest):
        raise ValueError(
            "envelope_candidate_digest must be strict sha256 hex"
        )

    return sha256_hex(
        {
            "grant_identity_domain": GRANT_ID_DOMAIN,
            "envelope_candidate_digest": envelope_digest,
        }
    )


def grant_identity_payload(
    value: CapabilityGrantIdentityCandidate,
) -> dict[str, object]:
    """Return the canonical payload for an identity candidate.

    The payload intentionally excludes ``grant_identity_digest`` (the
    self-digest) and includes every other instance field, including the
    derived ``grant_id``. The payload is fed to :func:`sha256_hex`, which
    performs canonical serialization (enum ``.value`` extraction, UTC
    RFC3339 datetime formatting, NFC normalization, and set-like sorting).
    """

    return {
        "grant_id": value.grant_id,
        "envelope_candidate_digest": value.envelope_candidate_digest,
        "candidate_digest": value.candidate_digest,
        "evidence_digest": value.evidence_digest,
        "request_id": value.request_id,
        "task_id": value.task_id,
        "actor_id": value.actor_id,
        "primary_effect": value.primary_effect,
        "secondary_effects": SetLikeTuple(value.secondary_effects),
        "resource_scopes": SetLikeTuple(
            tuple(
                canonical_resource_identity(scope)
                for scope in value.resource_scopes
            )
        ),
        "equivalent_action_groups": SetLikeTuple(
            value.equivalent_action_groups
        ),
        "requested_tool": value.requested_tool,
        "snapshot_id": value.snapshot_id,
        "policy_version": value.policy_version,
        "classification_attestation_hash": (
            value.classification_attestation_hash
        ),
        "issued_at": value.issued_at,
        "not_before": value.not_before,
        "expires_at": value.expires_at,
        "issuer_claim_id": value.issuer_claim_id,
        "issuer_claim_version": value.issuer_claim_version,
        "authority_proof_type": value.authority_proof_type,
    }


def compute_grant_identity_digest(
    value: CapabilityGrantIdentityCandidate,
) -> str:
    """Compute the canonical self-digest for an identity candidate."""

    return sha256_hex(grant_identity_payload(value))


def verify_grant_identity_digest(value: object) -> bool:
    """Return ``True`` iff ``value`` is a sealed identity candidate.

    This is a *total* function: it never raises. Any non-candidate input,
    any transient (empty-digest) candidate, any malformed candidate, or any
    digest mismatch yields ``False``.
    """

    if not isinstance(value, CapabilityGrantIdentityCandidate):
        return False

    digest = value.grant_identity_digest
    if not isinstance(digest, str):
        return False
    if not _is_strict_sha256_hex(digest):
        return False

    try:
        expected = compute_grant_identity_digest(value)
    except Exception:
        return False

    return _constant_time_equals(digest, expected)


def build_capability_grant_identity_candidate(
    context: PreActionGateContext,
    gate_result: PreActionGateResult,
    envelope_candidate: CapabilityGrantEnvelopeCandidate,
) -> CapabilityGrantIdentityBuildResult:
    """Build a fail-closed capability grant identity candidate.

    This public entry point is *total* and fail-closed: any internal error is
    folded into a single ``internal_error_fail_closed`` failure code and no
    raw exception text ever escapes.

    The factory deliberately does **not** accept a ``grant_id`` parameter.
    The identity is always derived from the trusted, rebuilt envelope; a
    caller cannot inject or override it.
    """

    try:
        failures, payload = _build_identity_failures(
            context, gate_result, envelope_candidate
        )
        if failures:
            return CapabilityGrantIdentityBuildResult(
                ok=False,
                grant_identity_candidate=None,
                failed_checks=tuple(failures),
                expiry_bound_source=None,
            )

        candidate, expiry_source = _assemble_identity_candidate(payload)
        return CapabilityGrantIdentityBuildResult(
            ok=True,
            grant_identity_candidate=candidate,
            failed_checks=(),
            expiry_bound_source=expiry_source,
        )
    except Exception:
        return CapabilityGrantIdentityBuildResult(
            ok=False,
            grant_identity_candidate=None,
            failed_checks=("internal_error_fail_closed",),
            expiry_bound_source=None,
        )


def _build_identity_failures(
    context: object,
    gate_result: object,
    envelope_candidate: object,
) -> tuple[list[str], dict[str, object]]:
    """Return ``(failures, payload)`` for the identity build."""

    failures: list[str] = []
    payload: dict[str, object] = {}

    # 1. Exact type checks. Stop early if any basic type is wrong so we never
    #    touch attributes on an untrusted object.
    if not isinstance(context, PreActionGateContext):
        failures.append("context_type_invalid")
    if not isinstance(gate_result, PreActionGateResult):
        failures.append("gate_result_type_invalid")
    if not isinstance(envelope_candidate, CapabilityGrantEnvelopeCandidate):
        failures.append("envelope_candidate_type_invalid")
    if failures:
        return failures, payload

    # 2. Validate the *passed-in* gate result's surface state.
    failures.extend(_check_gate_result_state(gate_result))

    # 3-6. Re-run the gate, re-derive evidence, and triple-bind the digest.
    failures.extend(_check_gate_reevaluation(context, gate_result))

    # 7. The envelope candidate must be sealed and self-verifying.
    if verify_envelope_candidate_digest(envelope_candidate) is not True:
        failures.append("envelope_candidate_digest_invalid")

    # If anything has failed up to this point, do not attempt the (more
    # expensive) rebuilds. We never pass through lower-layer failure codes.
    if failures:
        return failures, payload

    # 8. Rebuild the AK-5A candidate using the caller's ORIGINAL gate_result
    #    (never the recomputed result) and the envelope's own expiry bound.
    candidate_build = build_capability_grant_candidate(
        context=context,
        gate_result=gate_result,
        requested_expires_at=envelope_candidate.expires_at,
    )
    if (
        not candidate_build.ok
        or candidate_build.candidate is None
        or candidate_build.failed_checks
    ):
        failures.append("candidate_rebuild_failed")
        return failures, payload

    # 9. Rebuild the AK-5B1 envelope using the caller's ORIGINAL gate_result
    #    and the issuer claim carried by the passed-in envelope.
    envelope_build = build_capability_grant_envelope_candidate(
        context=context,
        gate_result=gate_result,
        candidate=candidate_build.candidate,
        issuer_claim_id=envelope_candidate.issuer_claim_id,
        issuer_claim_version=envelope_candidate.issuer_claim_version,
    )
    if (
        not envelope_build.ok
        or envelope_build.envelope_candidate is None
        or envelope_build.failed_checks
    ):
        failures.append("envelope_rebuild_failed")
        return failures, payload

    # 10. Strong bind: the rebuilt envelope must equal the passed-in envelope
    #     as a *full dataclass*, not merely by digest comparison.
    rebuilt = envelope_build.envelope_candidate
    if rebuilt != envelope_candidate:
        failures.append("envelope_rebuild_mismatch")
        return failures, payload

    # 11. Derive the grant identity from the trusted, rebuilt envelope.
    try:
        grant_id = derive_grant_id(rebuilt)
    except Exception:
        failures.append("grant_id_derivation_failed")
        return failures, payload

    # 12. Carry the trusted, rebuilt envelope and the derived identity
    #     forward. The caller never supplies any of these security fields.
    payload["grant_id"] = grant_id
    payload["rebuilt_envelope"] = rebuilt
    payload["expiry_bound_source"] = envelope_build.expiry_bound_source
    return failures, payload


def _check_gate_result_state(gate_result: PreActionGateResult) -> list[str]:
    """Validate the *passed-in* gate result's surface state."""

    failures: list[str] = []

    decision = getattr(gate_result, "decision", None)
    if decision is not AuthorizationDecision.ALLOW:
        failures.append("gate_result_not_allow")

    if getattr(gate_result, "authorization_ready", None) is not True:
        failures.append("gate_result_not_ready")

    gate_failed = getattr(gate_result, "failed_checks", None)
    if gate_failed != ():
        failures.append("gate_result_has_failed_checks")

    matched = getattr(gate_result, "matched_deny_count", None)
    if matched != 0:
        failures.append("gate_result_deny_matched")

    evidence = getattr(gate_result, "evidence_digest", None)
    if not isinstance(evidence, str) or not evidence:
        failures.append("gate_result_evidence_digest_empty")

    if not _gate_boundary_flags_all_false(gate_result):
        failures.append("gate_result_boundary_flags_invalid")

    return failures


def _gate_boundary_flags_all_false(gate_result: object) -> bool:
    """Return ``True`` iff all five gate boundary flags are exactly False."""

    flag_names = (
        "provider_authority_proven",
        "global_ledger_authority_proven",
        "global_ledger_freshness_proven",
        "toctou_resolved",
        "real_execution_permission",
    )
    for name in flag_names:
        if getattr(gate_result, name, None) is not False:
            return False
    return True


def _check_gate_reevaluation(
    context: PreActionGateContext, gate_result: PreActionGateResult
) -> list[str]:
    """Re-run the gate and triple-bind the evidence digest."""

    failures: list[str] = []

    recomputed = evaluate_pre_action_gate(context)

    if not _is_clean_allow(recomputed):
        failures.append("gate_reevaluation_not_clean_allow")

    if not _gate_boundary_flags_all_false(recomputed):
        failures.append("recomputed_gate_boundary_flags_invalid")

    recomputed_evidence = getattr(recomputed, "evidence_digest", None)
    context_evidence = compute_evidence_digest(context)

    if not isinstance(recomputed_evidence, str) or not recomputed_evidence:
        failures.append("evidence_digest_empty")
        return failures

    if not _constant_time_equals(recomputed_evidence, context_evidence):
        failures.append("reevaluation_digest_mismatch")

    gate_evidence = getattr(gate_result, "evidence_digest", None)
    if not isinstance(gate_evidence, str) or not gate_evidence:
        failures.append("evidence_digest_empty")
    elif not _constant_time_equals(recomputed_evidence, gate_evidence):
        failures.append("evidence_digest_mismatch")

    return failures


def _is_clean_allow(result: object) -> bool:
    """Return ``True`` iff ``result`` is a clean ALLOW gate result."""

    if getattr(result, "decision", None) is not AuthorizationDecision.ALLOW:
        return False
    if getattr(result, "authorization_ready", None) is not True:
        return False
    if getattr(result, "failed_checks", None) != ():
        return False
    if getattr(result, "matched_deny_count", None) != 0:
        return False
    return True


def _assemble_identity_candidate(
    payload: dict[str, object],
) -> tuple[CapabilityGrantIdentityCandidate, str]:
    """Assemble the sealed identity candidate and its expiry source.

    Every security-relevant field is copied from the trusted, rebuilt
    envelope. The ``grant_id`` is the derived identity. The self-digest is
    computed last and written back via :func:`dataclasses.replace`.
    """

    rebuilt = payload["rebuilt_envelope"]
    grant_id = payload["grant_id"]
    expiry_source = payload["expiry_bound_source"]

    candidate = CapabilityGrantIdentityCandidate(
        grant_identity_digest="",
        grant_id=grant_id,
        envelope_candidate_digest=rebuilt.envelope_candidate_digest,
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
        classification_attestation_hash=(
            rebuilt.classification_attestation_hash
        ),
        issued_at=rebuilt.issued_at,
        not_before=rebuilt.not_before,
        expires_at=rebuilt.expires_at,
        issuer_claim_id=rebuilt.issuer_claim_id,
        issuer_claim_version=rebuilt.issuer_claim_version,
        authority_proof_type=rebuilt.authority_proof_type,
    )

    sealed_digest = compute_grant_identity_digest(candidate)
    candidate = dataclasses.replace(
        candidate, grant_identity_digest=sealed_digest
    )
    return candidate, expiry_source