"""
GOAA Authorization Kernel AK-5A — Capability Grant Candidate (Schema + Digest)
==============================================================================
Pure, frozen data model for a *Capability Grant Candidate* plus its
canonical payload / digest functions. AK-5A is deliberately tiny: it
defines the candidate envelope and a deterministic, total digest over it.
Nothing here grants, leases, signs, persists, or enforces anything.

WHAT A CapabilityGrantCandidate IS NOT (read this before trusting one):

    NOT_REAL_EXECUTION_PERMISSION
        A candidate never authorizes a real side-effecting action. It is
        a record that a *pure* Pre-Action Gate (AK-4) produced a clean
        ALLOW for some evidence at some decision time. Runtime execution
        authority is out of scope for AK-5A.

    NOT_RUNTIME_ENFORCEABLE_TOKEN
        No Runtime, Shell, Router, Worker, or Executor consumes this. It
        carries no bearer secret, no nonce, no session binding, and is not
        wired into any enforcement path.

    NOT_CAPABILITY_LEASE
        There is no grant_id, no status, no consume/revoke lifecycle, no
        lease counter, and no state machine. A candidate is immutable data
        with an advisory validity window; it is not a redeemable lease.

    NOT_SIGNED_AUTHORITY
        The candidate_digest is a plain SHA-256 content hash for integrity
        and binding only. It is NOT a signature and proves no authority,
        provenance, or non-repudiation.

The digest reuses AK-1 canonical serialization (sha256_hex, SetLikeTuple)
and AK-1 canonical resource identity, so semantically-equal candidates
hash identically (NFC text, UTC-normalized time, order-independent
set-like fields) and any field change alters the digest.

These models are pure data: no I/O, no subprocess, no network, no clock
reads. ActionEffect / TypedResourceScope are reused from AK-1 and are NOT
redefined here.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md; FINAL_SPEC
GOAA-AK5A-CLAUDE-CODE-20260617-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from authorization_kernel.enums import ActionEffect
from authorization_kernel.resource_scope import (
    TypedResourceScope,
    canonical_resource_identity,
)
from authorization_kernel.canonical_serialization import (
    SetLikeTuple,
    sha256_hex,
)


# ============================================================
# Shared validation helpers (pure)
# ============================================================

def _is_sha256_hex(value: object) -> bool:
    """True only for a 64-char lowercase hex string (no uppercase, no spaces)."""
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(c in "0123456789abcdef" for c in value)


def _require_nonempty_str(value: object, field_name: str) -> None:
    """Raise unless value is a non-empty, non-whitespace string."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_aware(value: object, field_name: str) -> None:
    """Raise unless value is a timezone-aware datetime.

    Rejects naive datetimes AND datetimes whose tzinfo is present but whose
    utcoffset() is None (a malformed/incomplete tzinfo).
    """
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


# ============================================================
# CapabilityGrantCandidate
# ============================================================

@dataclass(frozen=True)
class CapabilityGrantCandidate:
    """An immutable record of a clean AK-4 ALLOW, ready for downstream review.

    A CapabilityGrantCandidate is:

        NOT_REAL_EXECUTION_PERMISSION
        NOT_RUNTIME_ENFORCEABLE_TOKEN
        NOT_CAPABILITY_LEASE
        NOT_SIGNED_AUTHORITY

    It deliberately has NO grant_id, NO status, NO real_execution_permission
    flag, NO runtime_enforced flag, NO consumed_at, and NO revoked_at field —
    none of the lifecycle / enforcement machinery exists in AK-5A.

    Field notes:
      - candidate_digest: SHA-256 content hash over every other field
        (see candidate_payload). Empty string is permitted ONLY as the
        transient pre-digest state used by the factory; once set it must be
        64-char lowercase hex.
      - evidence_digest: the AK-4 evidence digest this candidate is bound to.
      - requested_tool: recorded for AUDIT ONLY. It is part of the digest but
        is NEVER an authorization input — effect/scope/group fields are the
        only authorization-relevant facts.
      - issued_at / not_before: both equal the gate decision_time.
      - expires_at: a real, bounded datetime — NEVER None.
    """

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

    def __post_init__(self) -> None:
        # ---- digests ----
        # candidate_digest may be "" (transient pre-digest); else must be hex.
        if self.candidate_digest != "" and not _is_sha256_hex(self.candidate_digest):
            raise ValueError("candidate_digest must be 64-char lowercase hex")
        if not _is_sha256_hex(self.evidence_digest):
            raise ValueError("evidence_digest must be 64-char lowercase hex")
        if not _is_sha256_hex(self.classification_attestation_hash):
            raise ValueError(
                "classification_attestation_hash must be 64-char lowercase hex"
            )

        # ---- identity strings ----
        _require_nonempty_str(self.request_id, "request_id")
        _require_nonempty_str(self.task_id, "task_id")
        _require_nonempty_str(self.actor_id, "actor_id")
        _require_nonempty_str(self.snapshot_id, "snapshot_id")
        _require_nonempty_str(self.policy_version, "policy_version")

        # requested_tool is audit-only and MAY be empty, but must be a str.
        if not isinstance(self.requested_tool, str):
            raise TypeError("requested_tool must be a str")

        # ---- effects ----
        if not isinstance(self.primary_effect, ActionEffect):
            raise TypeError("primary_effect must be an ActionEffect")
        if not isinstance(self.secondary_effects, frozenset):
            raise TypeError("secondary_effects must be a frozenset")
        for eff in self.secondary_effects:
            if not isinstance(eff, ActionEffect):
                raise TypeError("secondary_effects must contain only ActionEffect")
        if self.primary_effect in self.secondary_effects:
            raise ValueError(
                "primary_effect must not appear in secondary_effects"
            )

        # ---- resource scopes ----
        if not isinstance(self.resource_scopes, tuple):
            raise TypeError("resource_scopes must be a tuple")
        if not self.resource_scopes:
            raise ValueError("resource_scopes must not be empty")
        seen_identities: set[str] = set()
        for scope in self.resource_scopes:
            if not isinstance(scope, TypedResourceScope):
                raise TypeError("resource_scopes must contain only TypedResourceScope")
            ident = canonical_resource_identity(scope)
            if ident in seen_identities:
                raise ValueError(f"duplicate resource scope identity: {ident}")
            seen_identities.add(ident)

        # ---- equivalent action groups ----
        if not isinstance(self.equivalent_action_groups, frozenset):
            raise TypeError("equivalent_action_groups must be a frozenset")
        for group in self.equivalent_action_groups:
            if not isinstance(group, str):
                raise TypeError("equivalent_action_groups must contain only str")
            if not group:
                raise ValueError(
                    "equivalent_action_groups must not contain empty strings"
                )

        # ---- temporal window ----
        _require_aware(self.issued_at, "issued_at")
        _require_aware(self.not_before, "not_before")
        _require_aware(self.expires_at, "expires_at")
        if self.not_before != self.issued_at:
            raise ValueError("not_before must equal issued_at")
        if self.expires_at < self.not_before:
            raise ValueError("expires_at must not be earlier than not_before")


# ============================================================
# Canonical payload + digest
# ============================================================

def _scope_identities(scopes: tuple[TypedResourceScope, ...]) -> SetLikeTuple:
    """Stable set-like wrapper of canonical resource identities for digest.

    Order-independent (SetLikeTuple sorts), so scope ordering never affects
    the digest. Reuses AK-1 canonical_resource_identity.
    """
    idents = tuple(canonical_resource_identity(scope) for scope in scopes)
    return SetLikeTuple(idents)


def candidate_payload(candidate: CapabilityGrantCandidate) -> dict[str, object]:
    """Canonical, digest-able view of EVERY candidate field except the digest.

    Set-like fields are wrapped in SetLikeTuple so order does not matter;
    enums and datetimes are canonicalized by AK-1 serialization (enum.value,
    UTC RFC3339). candidate_digest itself is intentionally excluded.
    """
    return {
        "evidence_digest": candidate.evidence_digest,
        "request_id": candidate.request_id,
        "task_id": candidate.task_id,
        "actor_id": candidate.actor_id,
        "primary_effect": candidate.primary_effect,
        "secondary_effects": SetLikeTuple(tuple(candidate.secondary_effects)),
        "resource_scopes": _scope_identities(candidate.resource_scopes),
        "equivalent_action_groups": SetLikeTuple(
            tuple(candidate.equivalent_action_groups)
        ),
        "requested_tool": candidate.requested_tool,
        "snapshot_id": candidate.snapshot_id,
        "policy_version": candidate.policy_version,
        "classification_attestation_hash": candidate.classification_attestation_hash,
        "issued_at": candidate.issued_at,
        "not_before": candidate.not_before,
        "expires_at": candidate.expires_at,
    }


def compute_candidate_digest(candidate: CapabilityGrantCandidate) -> str:
    """SHA-256 over the canonical candidate payload (reuses AK-1 sha256_hex)."""
    return sha256_hex(candidate_payload(candidate))


def verify_candidate_digest(candidate: CapabilityGrantCandidate) -> bool:
    """Whether candidate.candidate_digest matches its recomputed digest.

    Returns False for an empty (pre-digest) candidate_digest.
    """
    if not candidate.candidate_digest:
        return False
    return candidate.candidate_digest == compute_candidate_digest(candidate)
