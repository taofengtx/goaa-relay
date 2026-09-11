"""
GOAA Authorization Kernel AK-4 — Pre-Action Gate Evidence Models
=================================================================
Pure, frozen data models that carry the *evidence* combined by the
AK-4 Pre-Action Gate. These models add NO new authority of their own —
they are structural envelopes whose internal consistency the gate
validates against the real AK-1/AK-2/AK-3 schemas.

Trust boundary (honest, deliberately narrow):

    AK4_VALIDATES_CLASSIFICATION_EVIDENCE_STRUCTURE=YES
    AK4_PROVES_CLASSIFICATION_PROVIDER_AUTHORITY=NO

    AK4_VALIDATES_LEDGER_INTERNAL_INTEGRITY=YES
    AK4_PROVES_GLOBAL_LEDGER_AUTHORITY=NO
    AK4_PROVES_GLOBAL_LEDGER_FRESHNESS=NO

    TOCTOU_FULLY_SOLVED_BY_PURE_AK4=NO
    REAL_EXECUTION_PERMISSION_EMITTED=NO

These models are pure data: no I/O, no subprocess, no network, no clock
reads. `AuthorizationDecision` is reused from AK-1 enums and is NOT
redefined here.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §18 (Eleven-Step
Pre-Action Gate); FINAL_SPEC GOAA-AK4-CODE-20260615-002.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from authorization_kernel.enums import AuthorizationDecision
from authorization_kernel.action_request import ActionRequest
from authorization_kernel.authorization_snapshot import AuthorizationSnapshot
from authorization_kernel.classification_attestation import ClassificationAttestation
from authorization_kernel.effect_classifier import RecomputedClassification
from authorization_kernel.deny_ledger_state import DenyLedger


# ============================================================
# Shared validation helpers (pure)
# ============================================================

def _require_aware(value: object, field_name: str) -> None:
    """Raise ValueError unless value is a timezone-aware datetime."""
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_nonempty_str(value: object, field_name: str) -> None:
    """Raise unless value is a non-empty, non-whitespace string."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


# ============================================================
# ProviderEvidence
# ============================================================

@dataclass(frozen=True)
class ProviderEvidence:
    """A claim that some provider issued a classification attestation.

    IMPORTANT: AK-4 validates the *structure* and validity window of this
    evidence only. AK-4 does NOT prove the provider's real-world authority
    (AK4_PROVES_CLASSIFICATION_PROVIDER_AUTHORITY=NO). Presence of valid,
    unexpired provider evidence is a *necessary* — never a *sufficient* —
    condition for ALLOW.
    """

    provider_id: str
    issued_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        _require_nonempty_str(self.provider_id, "provider_id")
        _require_aware(self.issued_at, "issued_at")
        _require_aware(self.expires_at, "expires_at")
        if self.expires_at < self.issued_at:
            raise ValueError("expires_at must not be earlier than issued_at")


# ============================================================
# TrustedClassificationEvidence
# ============================================================

@dataclass(frozen=True)
class TrustedClassificationEvidence:
    """Evidence binding a ClassificationAttestation to a specific request.

    subject_request_id / subject_task_id: must equal the ActionRequest.
    attestation_hash: must equal the attestation's own hash.
    recomputed: must equal the attestation's recomputed_* fields.

    The structure is validated by AK-4; the underlying provider authority
    is NOT proven (see ProviderEvidence).
    """

    subject_request_id: str
    subject_task_id: str
    classification_policy_version: str
    attestation_hash: str
    recomputed: RecomputedClassification
    issued_at: datetime
    expires_at: datetime
    provider: ProviderEvidence | None = None

    def __post_init__(self) -> None:
        _require_nonempty_str(self.subject_request_id, "subject_request_id")
        _require_nonempty_str(self.subject_task_id, "subject_task_id")
        _require_nonempty_str(
            self.classification_policy_version, "classification_policy_version"
        )
        _require_nonempty_str(self.attestation_hash, "attestation_hash")
        if not isinstance(self.recomputed, RecomputedClassification):
            raise TypeError("recomputed must be a RecomputedClassification")
        _require_aware(self.issued_at, "issued_at")
        _require_aware(self.expires_at, "expires_at")
        if self.expires_at < self.issued_at:
            raise ValueError("expires_at must not be earlier than issued_at")
        if self.provider is not None and not isinstance(
            self.provider, ProviderEvidence
        ):
            raise TypeError("provider must be a ProviderEvidence or None")


# ============================================================
# AuthoritativeLedgerEvidence
# ============================================================

@dataclass(frozen=True)
class AuthoritativeLedgerEvidence:
    """Evidence binding a fold/match decision to an observed Deny Ledger.

    ledger_tip_hash / ledger_entry_count: must equal the observed tip and
    count of the ledger passed in the same context (binds the decision to
    a specific ledger state).
    decision_time: must equal the context decision_time.

    IMPORTANT: AK-4 validates the ledger's *internal* integrity and that
    this evidence is *bound* to the supplied ledger. AK-4 does NOT prove
    that the supplied ledger is the globally-authoritative or freshest
    ledger (AK4_PROVES_GLOBAL_LEDGER_AUTHORITY=NO,
    AK4_PROVES_GLOBAL_LEDGER_FRESHNESS=NO).
    """

    ledger_tip_hash: str | None
    ledger_entry_count: int
    decision_time: datetime
    issued_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if self.ledger_tip_hash is not None:
            _require_nonempty_str(self.ledger_tip_hash, "ledger_tip_hash")
        if type(self.ledger_entry_count) is not int:
            raise TypeError("ledger_entry_count must be an int")
        if self.ledger_entry_count < 0:
            raise ValueError("ledger_entry_count must be non-negative")
        # An empty ledger has no tip; a non-empty ledger must have one.
        if self.ledger_entry_count == 0 and self.ledger_tip_hash is not None:
            raise ValueError("empty ledger must have ledger_tip_hash=None")
        if self.ledger_entry_count > 0 and self.ledger_tip_hash is None:
            raise ValueError("non-empty ledger must have a ledger_tip_hash")
        _require_aware(self.decision_time, "decision_time")
        _require_aware(self.issued_at, "issued_at")
        _require_aware(self.expires_at, "expires_at")
        if self.expires_at < self.issued_at:
            raise ValueError("expires_at must not be earlier than issued_at")


# ============================================================
# PreActionGateContext
# ============================================================

@dataclass(frozen=True)
class PreActionGateContext:
    """The single, pure input to evaluate_pre_action_gate().

    classification_evidence / ledger_evidence are Optional so the gate can
    fail closed (OUT_OF_SCOPE) when a required proof is absent, rather than
    being unconstructable.

    requires_human_approval / human_approval_valid express a *mock* human
    approval contract for test/integration scaffolding. AK-4 does not
    itself issue or verify real approvals; it only routes the
    REQUIRES_APPROVAL outcome when an approval is required but absent.
    """

    request: ActionRequest
    snapshot: AuthorizationSnapshot
    attestation: ClassificationAttestation
    ledger: DenyLedger
    decision_time: datetime
    classification_evidence: TrustedClassificationEvidence | None = None
    ledger_evidence: AuthoritativeLedgerEvidence | None = None
    requires_human_approval: bool = False
    human_approval_valid: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.request, ActionRequest):
            raise TypeError("request must be an ActionRequest")
        if not isinstance(self.snapshot, AuthorizationSnapshot):
            raise TypeError("snapshot must be an AuthorizationSnapshot")
        if not isinstance(self.attestation, ClassificationAttestation):
            raise TypeError("attestation must be a ClassificationAttestation")
        if not isinstance(self.ledger, DenyLedger):
            raise TypeError("ledger must be a DenyLedger")
        # decision_time awareness is intentionally NOT enforced here — the
        # gate fail-closes on a naive decision_time as a security check.
        if not isinstance(self.decision_time, datetime):
            raise TypeError("decision_time must be a datetime")
        if self.classification_evidence is not None and not isinstance(
            self.classification_evidence, TrustedClassificationEvidence
        ):
            raise TypeError(
                "classification_evidence must be TrustedClassificationEvidence or None"
            )
        if self.ledger_evidence is not None and not isinstance(
            self.ledger_evidence, AuthoritativeLedgerEvidence
        ):
            raise TypeError(
                "ledger_evidence must be AuthoritativeLedgerEvidence or None"
            )
        if type(self.requires_human_approval) is not bool:
            raise TypeError("requires_human_approval must be a bool")
        if type(self.human_approval_valid) is not bool:
            raise TypeError("human_approval_valid must be a bool")


# ============================================================
# PreActionGateResult
# ============================================================

@dataclass(frozen=True)
class PreActionGateResult:
    """The pure result of evaluate_pre_action_gate().

    authorization_ready is True ONLY for a clean ALLOW with a non-empty
    evidence_digest and no failed checks — enforced as an invariant below.

    The five boundary flags are ALWAYS False: a pure AK-4 evaluation never
    proves provider authority, never proves global ledger authority or
    freshness, never resolves real execution-time TOCTOU, and never emits a
    real execution permission. They exist to make the boundary explicit in
    every result rather than relying on documentation alone.
    """

    decision: AuthorizationDecision
    authorization_ready: bool = False
    failed_checks: tuple[str, ...] = field(default_factory=tuple)
    evidence_digest: str = ""
    matched_deny_count: int = 0

    # Honest, immutable boundary markers — never True for a pure AK-4 run.
    provider_authority_proven: bool = False
    global_ledger_authority_proven: bool = False
    global_ledger_freshness_proven: bool = False
    toctou_resolved: bool = False
    real_execution_permission: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.decision, AuthorizationDecision):
            raise TypeError("decision must be an AuthorizationDecision")
        if type(self.authorization_ready) is not bool:
            raise TypeError("authorization_ready must be a bool")
        if not isinstance(self.failed_checks, tuple):
            raise TypeError("failed_checks must be a tuple")
        if type(self.matched_deny_count) is not int:
            raise TypeError("matched_deny_count must be an int")
        if self.matched_deny_count < 0:
            raise ValueError("matched_deny_count must be non-negative")

        # Boundary flags must never be claimed True by a pure AK-4 result.
        for flag_name in (
            "provider_authority_proven",
            "global_ledger_authority_proven",
            "global_ledger_freshness_proven",
            "toctou_resolved",
            "real_execution_permission",
        ):
            if getattr(self, flag_name) is not False:
                raise ValueError(f"{flag_name} must be False for a pure AK-4 result")

        # authorization_ready invariant: only a clean, digested ALLOW.
        if self.authorization_ready:
            if self.decision is not AuthorizationDecision.ALLOW:
                raise ValueError("authorization_ready=True requires decision==ALLOW")
            if self.failed_checks:
                raise ValueError(
                    "authorization_ready=True requires empty failed_checks"
                )
            if not self.evidence_digest:
                raise ValueError(
                    "authorization_ready=True requires a non-empty evidence_digest"
                )
            if self.matched_deny_count != 0:
                raise ValueError(
                    "authorization_ready=True requires matched_deny_count==0"
                )
