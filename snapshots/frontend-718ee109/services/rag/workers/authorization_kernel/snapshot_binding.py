"""
GOAA Authorization Kernel AK-2 — Snapshot Binding
===================================================
Defines SnapshotBindingResult and bind_snapshot() — the pure
function that verifies an ActionRequest against an AuthorizationSnapshot.

No I/O, no subprocess, no network. All verification is in-memory.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §7.2, §11, §22
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from authorization_kernel.enums import AuthorizationDecision
from authorization_kernel.action_request import ActionRequest
from authorization_kernel.authorization_snapshot import (
    AuthorizationSnapshot,
    verify_snapshot_hash,
)
from authorization_kernel.resource_scope import canonical_resource_identity


@dataclass(frozen=True)
class SnapshotBindingResult:
    """Result of binding an ActionRequest to an AuthorizationSnapshot.

    decision:
      ALLOW             — all 8 checks passed
      POLICY_CONFLICT   — task_id / snapshot_id / policy_version / hash mismatch
      DENY              — expired or effects/resources/groups exceed authorization

    failed_checks: tuple of failed check descriptions in 1→8 order.
    """

    decision: AuthorizationDecision = AuthorizationDecision.ALLOW
    failed_checks: tuple[str, ...] = field(default_factory=tuple)


def _now_is_timezone_aware(now: datetime) -> bool:
    """Check that now is timezone-aware."""
    return now.tzinfo is not None


def bind_snapshot(
    request: ActionRequest,
    snapshot: AuthorizationSnapshot,
    now: datetime,
) -> SnapshotBindingResult:
    """Bind an ActionRequest to an AuthorizationSnapshot.

    Verifies all 8 checks in fixed order:

     1. request.task_id == snapshot.task_id
     2. request.authorization_snapshot_id == snapshot.snapshot_id
     3. request.classification_policy_version == snapshot.policy_version
     4. snapshot_hash is valid (via verify_snapshot_hash)
     5. snapshot not expired (now <= snapshot.expires_at)
     6. request effects ⊆ snapshot.allowed_effects
     7. request resource_scopes ⊆ snapshot.allowed_resource_scopes
     8. request equivalent_action_groups ⊆ snapshot.allowed_equivalent_groups

    Checks 1-4 failure → POLICY_CONFLICT
    Checks 5-8 failure → DENY
    All pass           → ALLOW

    'now' must be timezone-aware. Naive datetime raises ValueError.
    """
    if not _now_is_timezone_aware(now):
        raise ValueError("now must be timezone-aware")

    failed: list[str] = []

    # --- STRUCTURAL CHECKS (POLICY_CONFLICT) ---

    # 1. task_id
    if request.task_id != snapshot.task_id:
        failed.append("task_id mismatch")

    # 2. authorization_snapshot_id
    if request.authorization_snapshot_id != snapshot.snapshot_id:
        failed.append("snapshot_id mismatch")

    # 3. classification_policy_version
    if request.classification_policy_version != snapshot.policy_version:
        failed.append("policy_version mismatch")

    # 4. snapshot hash validity
    if not verify_snapshot_hash(snapshot):
        failed.append("snapshot_hash invalid")

    if failed:
        return SnapshotBindingResult(
            decision=AuthorizationDecision.POLICY_CONFLICT,
            failed_checks=tuple(failed),
        )

    # --- SEMANTIC CHECKS (DENY) ---

    # 5. expiry
    if snapshot.expires_at is not None and now > snapshot.expires_at:
        failed.append("snapshot expired")

    # 6. effects ⊆ allowed_effects
    request_effects: set = {request.primary_effect}
    request_effects.update(request.secondary_effects)
    if not request_effects.issubset(snapshot.allowed_effects):
        failed.append("effects exceed allowed_effects")

    # 7. resource_scopes ⊆ allowed_resource_scopes
    if not _resource_scopes_allowed(
        request.resource_scopes, snapshot.allowed_resource_scopes
    ):
        failed.append("resource_scopes exceed allowed_resource_scopes")

    # 8. equivalent_action_groups ⊆ allowed_equivalent_groups
    if not request.equivalent_action_groups.issubset(
        snapshot.allowed_equivalent_groups
    ):
        failed.append("groups exceed allowed_equivalent_groups")

    if failed:
        return SnapshotBindingResult(
            decision=AuthorizationDecision.DENY,
            failed_checks=tuple(failed),
        )

    return SnapshotBindingResult(
        decision=AuthorizationDecision.ALLOW,
        failed_checks=(),
    )


def _resource_scopes_allowed(
    request_scopes: tuple,
    allowed_scopes: tuple,
) -> bool:
    """Check that every request resource scope is allowed by the snapshot.

    Uses canonical_resource_identity() for scope comparison.
    """
    allowed_identities: set[str] = {
        canonical_resource_identity(s) for s in allowed_scopes
    }
    for scope in request_scopes:
        ident = canonical_resource_identity(scope)
        if ident not in allowed_identities:
            return False
    return True
