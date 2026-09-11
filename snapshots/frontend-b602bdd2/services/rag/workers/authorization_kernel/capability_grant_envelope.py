"""
GOAA Authorization Kernel AK-5B — Capability Grant *Envelope* Candidate
========================================================================
Pure, frozen data model for a *Capability Grant Envelope Candidate* plus
its canonical payload / digest functions. AK-5B wraps a clean AK-5A
CapabilityGrantCandidate with issuer-claim metadata and a second-order
content digest. Like AK-5A, it grants, leases, signs, persists, and
enforces NOTHING.

WHAT A CapabilityGrantEnvelopeCandidate IS NOT (read before trusting one):

    NOT_REAL_EXECUTION_PERMISSION   — never authorizes a side-effecting action.
    NOT_RUNTIME_ENFORCEABLE_TOKEN   — no Runtime/Shell/Router/Worker consumes it.
    NOT_CAPABILITY_LEASE            — no grant_id, status, consume/revoke lifecycle.
    NOT_SIGNED_AUTHORITY            — the digest is a plain SHA-256 hash, not a signature.
    NOT_AUTHORITY_PROOF             — proves no real-world authority of any kind.
    NOT_REPLAY_PROTECTED            — carries no nonce, session binding, or replay defense.
    NOT_PERSISTED                   — pure in-memory data; nothing is written anywhere.
    NOT_AUTHORITATIVE_GRANT         — an advisory candidate, not an authoritative grant.
    NOT_ISSUED_GRANT                — issuer_claim_* is a recorded *claim*, not an issuance.

The issuer_claim_id / issuer_claim_version fields record a *claimed* issuer
identity for audit only; they confer no authority. authority_proof_type is
ALWAYS the literal string "NONE": any other value is a MODEL_CONSTRUCTION_
REJECTION because AK-5B can never carry a real authority proof.

The envelope_candidate_digest reuses AK-1 canonical serialization
(sha256_hex, SetLikeTuple) and AK-1 canonical resource identity, so
semantically-equal envelopes hash identically and any field change alters
the digest. The candidate_digest / evidence_digest it carries are the
AK-5A / AK-4 digests this envelope is bound to.

SECURITY-VALIDATION NOTE (BLOCKER 1): every invariant below is enforced with
an explicit `if ... raise TypeError/ValueError`. There is NOT a single
`assert` statement in this module, so validation behaves identically under
plain `python3` and `python3 -O` (which strips asserts). The private helpers
_is_sha256_hex / _require_nonempty_str / _require_aware mirror AK-5A exactly.

BLOCKER 1 (revision R2): verify_envelope_candidate_digest is now a TOTAL
predicate over `object`. It accepts ANY value, never reads an attribute on a
wrong-type input, and NEVER raises — every anomalous input (None, int, plain
object, wrong-type/missing/malformed digest, transient-empty digest, tampered
fields) returns False. Only a correctly sealed, untampered
CapabilityGrantEnvelopeCandidate returns True.

These models are pure data: no I/O, no subprocess, no network, no clock
reads. ActionEffect / TypedResourceScope are reused from AK-1.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md; FINAL_SPEC
GOAA-AK5B-CLAUDE-CODE-20260617-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from authorization_kernel.enums import ActionEffect
from authorization_kernel.resource_scope import (
    TypedResourceScope,
    canonical_resource_identity,
)
from authorization_kernel.canonical_serialization import SetLikeTuple, sha256_hex


# ============================================================
# Shared validation helpers (pure) — NO asserts (BLOCKER 1)
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
# CapabilityGrantEnvelopeCandidate
# ============================================================

@dataclass(frozen=True)
class CapabilityGrantEnvelopeCandidate:
    """An immutable envelope wrapping a clean AK-5A candidate + issuer claim.

    The nine ClassVar boundary markers below are part of the type itself —
    they are not instance fields, never enter any digest, and exist so the
    honest boundary is impossible to miss in code. authority_proof_type is
    the ONLY proof-shaped field and must always equal "NONE".
    """

    # ---- Nine honest boundary markers (class-level, never digested) ----
    NOT_REAL_EXECUTION_PERMISSION: ClassVar[bool] = True
    NOT_RUNTIME_ENFORCEABLE_TOKEN: ClassVar[bool] = True
    NOT_CAPABILITY_LEASE: ClassVar[bool] = True
    NOT_SIGNED_AUTHORITY: ClassVar[bool] = True
    NOT_AUTHORITY_PROOF: ClassVar[bool] = True
    NOT_REPLAY_PROTECTED: ClassVar[bool] = True
    NOT_PERSISTED: ClassVar[bool] = True
    NOT_AUTHORITATIVE_GRANT: ClassVar[bool] = True
    NOT_ISSUED_GRANT: ClassVar[bool] = True

    # ---- 20 instance fields, all required, no defaults ----
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
    authority_proof_type: str  # must be "NONE"

    def __post_init__(self) -> None:
        # ---- digests (BLOCKER 2): exact 64-char lowercase hex ----
        # envelope_candidate_digest may be "" ONLY as the transient pre-seal
        # state; any non-empty value must be 64-char lowercase hex.
        if self.envelope_candidate_digest != "" and not _is_sha256_hex(
            self.envelope_candidate_digest
        ):
            raise ValueError(
                "envelope_candidate_digest must be 64-char lowercase hex or ''"
            )
        if not _is_sha256_hex(self.candidate_digest):
            raise ValueError("candidate_digest must be 64-char lowercase hex")
        if not _is_sha256_hex(self.evidence_digest):
            raise ValueError("evidence_digest must be 64-char lowercase hex")
        if not _is_sha256_hex(self.classification_attestation_hash):
            raise ValueError(
                "classification_attestation_hash must be 64-char lowercase hex"
            )

        # ---- identity strings (BLOCKER 2): non-empty str only ----
        _require_nonempty_str(self.request_id, "request_id")
        _require_nonempty_str(self.task_id, "task_id")
        _require_nonempty_str(self.actor_id, "actor_id")
        _require_nonempty_str(self.snapshot_id, "snapshot_id")
        _require_nonempty_str(self.policy_version, "policy_version")
        _require_nonempty_str(self.issuer_claim_id, "issuer_claim_id")
        _require_nonempty_str(self.issuer_claim_version, "issuer_claim_version")

        # ---- requested_tool: audit-only, MAY be empty, must be a str ----
        if not isinstance(self.requested_tool, str):
            raise TypeError("requested_tool must be a str")

        # ---- effects (BLOCKER 2) ----
        if not isinstance(self.primary_effect, ActionEffect):
            raise TypeError("primary_effect must be an ActionEffect")
        if not isinstance(self.secondary_effects, frozenset):
            raise TypeError("secondary_effects must be a frozenset")
        for eff in self.secondary_effects:
            if not isinstance(eff, ActionEffect):
                raise TypeError("secondary_effects must contain only ActionEffect")
        if self.primary_effect in self.secondary_effects:
            raise ValueError("primary_effect must not appear in secondary_effects")

        # ---- resource scopes (BLOCKER 2) ----
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

        # ---- equivalent action groups (BLOCKER 2) ----
        if not isinstance(self.equivalent_action_groups, frozenset):
            raise TypeError("equivalent_action_groups must be a frozenset")
        for group in self.equivalent_action_groups:
            if not isinstance(group, str):
                raise TypeError("equivalent_action_groups must contain only str")
            if not group:
                raise ValueError(
                    "equivalent_action_groups must not contain empty strings"
                )

        # ---- temporal window (BLOCKER 2) ----
        _require_aware(self.issued_at, "issued_at")
        _require_aware(self.not_before, "not_before")
        _require_aware(self.expires_at, "expires_at")
        if self.not_before != self.issued_at:
            raise ValueError("not_before must equal issued_at")
        if self.expires_at < self.not_before:
            raise ValueError("expires_at must not be earlier than not_before")

        # ---- authority_proof_type: ONLY "NONE" (else MODEL_CONSTRUCTION_REJECTION) ----
        if not isinstance(self.authority_proof_type, str):
            raise TypeError("authority_proof_type must be a str")
        if self.authority_proof_type != "NONE":
            raise ValueError("authority_proof_type must be 'NONE'")


# ============================================================
# Canonical payload + digest (BLOCKER 3 — reuse AK-1)
# ============================================================

def _scope_identities(scopes: tuple[TypedResourceScope, ...]) -> SetLikeTuple:
    """Stable set-like wrapper of canonical resource identities for digest.

    Order-independent (SetLikeTuple sorts), so scope ordering never affects
    the digest. Reuses AK-1 canonical_resource_identity.
    """
    idents = tuple(canonical_resource_identity(scope) for scope in scopes)
    return SetLikeTuple(idents)


def envelope_candidate_payload(
    envelope: CapabilityGrantEnvelopeCandidate,
) -> dict[str, object]:
    """Canonical, digest-able view of EVERY envelope field except its own
    envelope_candidate_digest.

    BLOCKER 3: this returns a plain dict[str, object] — NOT an OrderedDict and
    NOT a pre-serialized string. Enum objects stay Enum, datetimes stay aware
    datetime, and set-like fields are wrapped in SetLikeTuple. AK-1
    canonical_serialization (applied externally via sha256_hex) handles enum
    .value extraction, UTC RFC3339 datetime formatting, NFC text, sorted keys,
    and SetLikeTuple sorting — so there is NO sorted(), NO isoformat(), and NO
    manual JSON/NFC here. This mirrors AK-5A candidate_payload exactly.
    """
    return {
        "candidate_digest": envelope.candidate_digest,
        "evidence_digest": envelope.evidence_digest,
        "request_id": envelope.request_id,
        "task_id": envelope.task_id,
        "actor_id": envelope.actor_id,
        "primary_effect": envelope.primary_effect,
        "secondary_effects": SetLikeTuple(tuple(envelope.secondary_effects)),
        "resource_scopes": _scope_identities(envelope.resource_scopes),
        "equivalent_action_groups": SetLikeTuple(
            tuple(envelope.equivalent_action_groups)
        ),
        "requested_tool": envelope.requested_tool,
        "snapshot_id": envelope.snapshot_id,
        "policy_version": envelope.policy_version,
        "classification_attestation_hash": envelope.classification_attestation_hash,
        "issued_at": envelope.issued_at,
        "not_before": envelope.not_before,
        "expires_at": envelope.expires_at,
        "issuer_claim_id": envelope.issuer_claim_id,
        "issuer_claim_version": envelope.issuer_claim_version,
        "authority_proof_type": envelope.authority_proof_type,
    }


def compute_envelope_candidate_digest(
    envelope: CapabilityGrantEnvelopeCandidate,
) -> str:
    """SHA-256 over the canonical envelope payload (reuses AK-1 sha256_hex).

    sha256_hex canonically JSON-serializes the payload dict (NFC text, sorted
    keys, enum.value, UTC RFC3339 datetimes, SetLikeTuple sorted by canonical
    identity) and returns 64-char lowercase hex.
    """
    return sha256_hex(envelope_candidate_payload(envelope))


def verify_envelope_candidate_digest(value: object) -> bool:
    """Whether `value` is a correctly SEALED CapabilityGrantEnvelopeCandidate.

    BLOCKER 1 (revision R2): this is a TOTAL bool predicate over `object`. It
    NEVER raises — AttributeError, TypeError, or any other exception is caught
    and collapsed to False. Concretely:

      - object(), None, int, or any non-envelope value          -> False
      - an envelope with a transient/empty envelope_candidate_digest -> False
      - an envelope whose digest is non-hex / wrong-type        -> False
      - an envelope whose fields were tampered after sealing     -> False
      - a correctly sealed, untampered envelope                 -> True

    The empty string is permitted only as the dataclass's initial pre-seal
    state; it is NEVER a verified digest.
    """
    try:
        if not isinstance(value, CapabilityGrantEnvelopeCandidate):
            return False
        if not value.envelope_candidate_digest:
            return False
        if not _is_sha256_hex(value.envelope_candidate_digest):
            return False
        return (
            value.envelope_candidate_digest
            == compute_envelope_candidate_digest(value)
        )
    except Exception:
        return False
