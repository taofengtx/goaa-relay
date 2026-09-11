"""
GOAA Authorization Kernel AK-1 — Classification Attestation
=============================================================
Defines ClassificationAttestation — the verified record that
an action's effect classification matches its recomputed values.

AK-1 defines only the data model and hash functions.
The actual effect reclassification logic is implemented in AK-3.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §14
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from authorization_kernel.enums import ActionEffect


@dataclass(frozen=True)
class ClassificationAttestation:
    """A verified record of action effect classification.

    declared_*: what the caller claims the effects are.
    recomputed_*: what the system independently classifies.

    If declared != recomputed, the Pre-Action Gate produces
    POLICY_CONFLICT and denies execution.
    """

    classification_policy_version: str

    declared_primary_effect: ActionEffect
    recomputed_primary_effect: ActionEffect

    declared_secondary_effects: frozenset[ActionEffect] = field(
        default_factory=frozenset
    )
    recomputed_secondary_effects: frozenset[ActionEffect] = field(
        default_factory=frozenset
    )
    declared_equivalent_groups: frozenset[str] = field(default_factory=frozenset)
    recomputed_equivalent_groups: frozenset[str] = field(default_factory=frozenset)

    classification_attestation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.classification_policy_version:
            raise ValueError("classification_policy_version must not be empty")


def attestation_payload(
    attestation: ClassificationAttestation,
) -> dict[str, object]:
    """Extract the hashable payload, excluding the hash field itself."""
    return {
        "classification_policy_version": attestation.classification_policy_version,
        "declared_primary_effect": attestation.declared_primary_effect.value,
        "declared_secondary_effects": sorted(
            e.value for e in attestation.declared_secondary_effects
        ),
        "recomputed_primary_effect": attestation.recomputed_primary_effect.value,
        "recomputed_secondary_effects": sorted(
            e.value for e in attestation.recomputed_secondary_effects
        ),
        "declared_equivalent_groups": sorted(
            attestation.declared_equivalent_groups
        ),
        "recomputed_equivalent_groups": sorted(
            attestation.recomputed_equivalent_groups
        ),
    }


def compute_attestation_hash(
    attestation: ClassificationAttestation,
) -> str:
    """Compute the SHA-256 hash of the attestation payload."""
    payload = attestation_payload(attestation)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_attestation_hash(attestation: ClassificationAttestation) -> bool:
    """Verify that the attestation's hash matches its recomputed hash."""
    if not attestation.classification_attestation_hash:
        return False
    return (
        attestation.classification_attestation_hash
        == compute_attestation_hash(attestation)
    )


def classification_matches(attestation: ClassificationAttestation) -> bool:
    """Check whether declared and recomputed classifications agree."""
    return (
        attestation.declared_primary_effect
        == attestation.recomputed_primary_effect
        and attestation.declared_secondary_effects
        == attestation.recomputed_secondary_effects
        and attestation.declared_equivalent_groups
        == attestation.recomputed_equivalent_groups
    )
