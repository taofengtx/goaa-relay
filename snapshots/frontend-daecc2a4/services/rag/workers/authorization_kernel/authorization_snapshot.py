"""
GOAA Authorization Kernel AK-1 — Authorization Snapshot
==========================================================
Defines the immutable AuthorizationSnapshot with hash verification.

An AuthorizationSnapshot is a point-in-time, immutable record of
what effects, scopes, and groups are authorized for a given task.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §11, §12
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from authorization_kernel.enums import ActionEffect
from authorization_kernel.resource_scope import (
    TypedResourceScope,
    canonical_resource_identity,
)


@dataclass(frozen=True)
class AuthorizationSnapshot:
    """Immutable snapshot of authorization state for a task.

    snapshot_hash covers all fields except itself — computed via
    compute_snapshot_hash().
    """

    snapshot_id: str
    task_id: str
    policy_version: str
    created_at: datetime
    expires_at: datetime | None = None

    source_authorizations: tuple[str, ...] = ()
    approved_by: str | None = None

    allowed_effects: frozenset[ActionEffect] = field(default_factory=frozenset)
    allowed_resource_scopes: tuple[TypedResourceScope, ...] = ()
    allowed_equivalent_groups: frozenset[str] = field(default_factory=frozenset)

    snapshot_hash: str = ""

    def __post_init__(self) -> None:
        # Core ID fields
        if not self.snapshot_id:
            raise ValueError("snapshot_id must not be empty")
        if not self.task_id:
            raise ValueError("task_id must not be empty")
        if not self.policy_version:
            raise ValueError("policy_version must not be empty")

        # Timezone awareness
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")

        # Expiry ordering
        if self.expires_at is not None and self.expires_at < self.created_at:
            raise ValueError("expires_at must not be earlier than created_at")

        # source_authorizations must be a tuple
        if not isinstance(self.source_authorizations, tuple):
            raise TypeError("source_authorizations must be a tuple")

        # allowed_resource_scopes: no duplicate canonical identities
        seen_identities: set[str] = set()
        for scope in self.allowed_resource_scopes:
            ident = canonical_resource_identity(scope)
            if ident in seen_identities:
                raise ValueError(
                    f"duplicate resource scope identity in allowed_resource_scopes: {ident}"
                )
            seen_identities.add(ident)

        # Validate snapshot_hash format if non-empty
        if self.snapshot_hash and not _is_valid_sha256_hex(self.snapshot_hash):
            raise ValueError(
                f"snapshot_hash must be 64-char lowercase hex, got '{self.snapshot_hash}'"
            )


def _is_valid_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def snapshot_payload(snapshot: AuthorizationSnapshot) -> dict[str, object]:
    """Extract the hashable payload from a snapshot, excluding snapshot_hash itself."""
    # Sort frozenset by enum .value
    allowed_effects_sorted = sorted(
        snapshot.allowed_effects, key=lambda e: e.value
    )
    allowed_groups_sorted = sorted(snapshot.allowed_equivalent_groups)
    source_auths_sorted = sorted(snapshot.source_authorizations)

    payload: dict[str, object] = {
        "snapshot_id": snapshot.snapshot_id,
        "task_id": snapshot.task_id,
        "policy_version": snapshot.policy_version,
        "created_at": snapshot.created_at.isoformat(),
        "expires_at": snapshot.expires_at.isoformat() if snapshot.expires_at else None,
        "source_authorizations": source_auths_sorted,
        "approved_by": snapshot.approved_by,
        "allowed_effects": [e.value for e in allowed_effects_sorted],
        "allowed_groups": allowed_groups_sorted,
        "allowed_resource_scopes": [
            {
                "scope_type": s.scope_type.value,
                "canonical_id": s.canonical_id,
                "attributes": sorted(s.attributes),
            }
            for s in snapshot.allowed_resource_scopes
        ],
    }
    return payload


def compute_snapshot_hash(snapshot: AuthorizationSnapshot) -> str:
    """Compute the SHA-256 hash of the snapshot payload."""
    payload = snapshot_payload(snapshot)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_snapshot_hash(snapshot: AuthorizationSnapshot) -> bool:
    """Verify that the snapshot's snapshot_hash matches its recomputed hash."""
    if not snapshot.snapshot_hash:
        return False
    return snapshot.snapshot_hash == compute_snapshot_hash(snapshot)
