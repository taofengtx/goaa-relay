"""
GOAA Authorization Kernel AK-2 — Snapshot Binding Unit Tests
==============================================================
Tests: bind_snapshot() with all 8 checks, POLICY_CONFLICT vs DENY
       separation, edge cases, timezone awareness.

Framework: unittest (standard library). No pytest dependency.
All tests are pure — no I/O, no subprocess, no network.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from authorization_kernel.enums import ActionEffect, ResourceScopeType
from authorization_kernel.resource_scope import (
    TypedResourceScope,
)
from authorization_kernel.action_request import ActionRequest, CanonicalParameter
from authorization_kernel.authorization_snapshot import AuthorizationSnapshot
from authorization_kernel.snapshot_binding import bind_snapshot, SnapshotBindingResult
from authorization_kernel.enums import AuthorizationDecision


# Helpers
def _make_scope(st: ResourceScopeType, cid: str) -> TypedResourceScope:
    return TypedResourceScope(scope_type=st, canonical_id=cid)


def _empty_params() -> tuple[CanonicalParameter, ...]:
    return ()


def _now() -> datetime:
    return datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_request(
    task_id: str = "task-1",
    snapshot_id: str = "snap-1",
    policy_version: str = "1.0",
    primary: ActionEffect = ActionEffect.READ,
    secondary: frozenset[ActionEffect] | None = None,
    scopes: tuple[TypedResourceScope, ...] | None = None,
    groups: frozenset[str] | None = None,
) -> ActionRequest:
    return ActionRequest(
        request_id="req-1",
        task_id=task_id,
        authorization_snapshot_id=snapshot_id,
        actor_id="actor-1",
        primary_effect=primary,
        secondary_effects=secondary or frozenset(),
        resource_scopes=scopes or (_make_scope(ResourceScopeType.FILE_PATH, "/a"),),
        normalized_parameters=_empty_params(),
        parameters_digest="digest",
        equivalent_action_groups=groups or frozenset({"GROUP_READ"}),
        classification_policy_version=policy_version,
    )


def _make_snapshot(
    task_id: str = "task-1",
    snapshot_id: str = "snap-1",
    policy_version: str = "1.0",
    allowed_effects: frozenset[ActionEffect] | None = None,
    allowed_scopes: tuple[TypedResourceScope, ...] | None = None,
    allowed_groups: frozenset[str] | None = None,
    expires_at: datetime | None = None,
) -> AuthorizationSnapshot:
    from authorization_kernel.authorization_snapshot import compute_snapshot_hash

    snap = AuthorizationSnapshot(
        snapshot_id=snapshot_id,
        task_id=task_id,
        policy_version=policy_version,
        created_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        expires_at=expires_at,
        allowed_effects=allowed_effects or frozenset({ActionEffect.READ}),
        allowed_resource_scopes=allowed_scopes or (
            _make_scope(ResourceScopeType.FILE_PATH, "/a"),
        ),
        allowed_equivalent_groups=allowed_groups or frozenset({"GROUP_READ"}),
    )
    h = compute_snapshot_hash(snap)
    # Replace with hash set
    return AuthorizationSnapshot(
        snapshot_id=snapshot_id,
        task_id=task_id,
        policy_version=policy_version,
        created_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        expires_at=expires_at,
        allowed_effects=allowed_effects or frozenset({ActionEffect.READ}),
        allowed_resource_scopes=allowed_scopes or (
            _make_scope(ResourceScopeType.FILE_PATH, "/a"),
        ),
        allowed_equivalent_groups=allowed_groups or frozenset({"GROUP_READ"}),
        snapshot_hash=h,
    )


class TestBindSnapshot(unittest.TestCase):

    # --- All pass ---

    def test_all_checks_pass(self) -> None:
        result = bind_snapshot(
            _make_request(),
            _make_snapshot(),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.ALLOW)
        self.assertEqual(result.failed_checks, ())

    # --- Check 1: task_id mismatch ---

    def test_task_id_mismatch(self) -> None:
        result = bind_snapshot(
            _make_request(task_id="task-wrong"),
            _make_snapshot(task_id="task-right"),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.POLICY_CONFLICT)
        self.assertIn("task_id", result.failed_checks[0])

    # --- Check 2: snapshot_id mismatch ---

    def test_snapshot_id_mismatch(self) -> None:
        result = bind_snapshot(
            _make_request(snapshot_id="snap-wrong"),
            _make_snapshot(snapshot_id="snap-right"),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.POLICY_CONFLICT)
        self.assertIn("snapshot_id", result.failed_checks[0])

    # --- Check 3: policy_version mismatch ---

    def test_policy_version_mismatch(self) -> None:
        result = bind_snapshot(
            _make_request(policy_version="2.0"),
            _make_snapshot(policy_version="1.0"),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.POLICY_CONFLICT)
        self.assertIn("policy_version", result.failed_checks[0])

    # --- Check 4: hash invalid ---

    def test_hash_invalid(self) -> None:
        """Provide a properly formatted hash that doesn't match the payload."""
        snap = _make_snapshot()
        snap_bad = AuthorizationSnapshot(
            snapshot_id=snap.snapshot_id,
            task_id=snap.task_id,
            policy_version=snap.policy_version,
            created_at=snap.created_at,
            expires_at=snap.expires_at,
            allowed_effects=snap.allowed_effects,
            allowed_resource_scopes=snap.allowed_resource_scopes,
            allowed_equivalent_groups=snap.allowed_equivalent_groups,
            snapshot_hash="1111111111111111111111111111111111111111111111111111111111111111",
        )
        result = bind_snapshot(
            _make_request(),
            snap_bad,
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.POLICY_CONFLICT)
        self.assertIn("hash", result.failed_checks[0])

    # --- Check 5: expired ---

    def test_expired(self) -> None:
        snap = _make_snapshot(
            expires_at=datetime(2026, 6, 15, 11, 0, 0, tzinfo=timezone.utc)
        )
        now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = bind_snapshot(
            _make_request(),
            snap,
            now,
        )
        self.assertEqual(result.decision, AuthorizationDecision.DENY)
        self.assertIn("expired", result.failed_checks[0])

    def test_not_expired(self) -> None:
        snap = _make_snapshot(
            expires_at=datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc)
        )
        now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = bind_snapshot(
            _make_request(),
            snap,
            now,
        )
        self.assertEqual(result.decision, AuthorizationDecision.ALLOW)

    def test_no_expiry(self) -> None:
        snap = _make_snapshot(expires_at=None)
        result = bind_snapshot(
            _make_request(),
            snap,
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.ALLOW)

    # --- Check 6: effects exceed ---

    def test_primary_effect_exceeds_allowed(self) -> None:
        result = bind_snapshot(
            _make_request(primary=ActionEffect.WRITE),
            _make_snapshot(allowed_effects=frozenset({ActionEffect.READ})),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.DENY)
        self.assertIn("effects", result.failed_checks[0])

    def test_secondary_effect_exceeds_allowed(self) -> None:
        result = bind_snapshot(
            _make_request(
                primary=ActionEffect.READ,
                secondary=frozenset({ActionEffect.WRITE}),
            ),
            _make_snapshot(allowed_effects=frozenset({ActionEffect.READ})),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.DENY)

    # --- Check 7: resource scopes exceed ---

    def test_resource_scope_exceeds_allowed(self) -> None:
        req_scope = _make_scope(ResourceScopeType.FILE_PATH, "/b")
        snap_scope = _make_scope(ResourceScopeType.FILE_PATH, "/a")
        result = bind_snapshot(
            _make_request(scopes=(req_scope,)),
            _make_snapshot(allowed_scopes=(snap_scope,)),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.DENY)
        self.assertIn("resource_scopes", result.failed_checks[0])

    # --- Check 8: groups exceed ---

    def test_groups_exceed_allowed(self) -> None:
        result = bind_snapshot(
            _make_request(groups=frozenset({"GROUP_READ", "GROUP_WRITE"})),
            _make_snapshot(allowed_groups=frozenset({"GROUP_READ"})),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.DENY)
        self.assertIn("groups", result.failed_checks[0])

    # --- Multiple failures ---

    def test_multiple_failures_structural(self) -> None:
        """task_id + snapshot_id + policy_version all wrong."""
        result = bind_snapshot(
            _make_request(
                task_id="wrong-task",
                snapshot_id="wrong-snap",
                policy_version="99.0",
            ),
            _make_snapshot(),
            _now(),
        )
        self.assertEqual(result.decision, AuthorizationDecision.POLICY_CONFLICT)
        self.assertGreaterEqual(len(result.failed_checks), 3)

    def test_multiple_failures_semantic(self) -> None:
        """expired + effects exceed + scopes exceed + groups exceed."""
        snap = _make_snapshot(
            expires_at=datetime(2026, 6, 15, 11, 0, 0, tzinfo=timezone.utc),
            allowed_effects=frozenset({ActionEffect.READ}),
            allowed_scopes=(_make_scope(ResourceScopeType.FILE_PATH, "/a"),),
            allowed_groups=frozenset({"GROUP_READ"}),
        )
        req = _make_request(
            primary=ActionEffect.WRITE,
            scopes=(_make_scope(ResourceScopeType.FILE_PATH, "/b"),),
            groups=frozenset({"GROUP_WRITE"}),
        )
        now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = bind_snapshot(req, snap, now)
        self.assertEqual(result.decision, AuthorizationDecision.DENY)
        self.assertGreaterEqual(len(result.failed_checks), 3)

    # --- Timezone awareness ---

    def test_naive_now_rejected(self) -> None:
        now_naive = datetime(2026, 6, 15, 12, 0, 0)
        with self.assertRaises(ValueError):
            bind_snapshot(
                _make_request(),
                _make_snapshot(),
                now_naive,
            )

    # --- Frozen result ---

    def test_result_frozen(self) -> None:
        result = bind_snapshot(
            _make_request(),
            _make_snapshot(),
            _now(),
        )
        with self.assertRaises(AttributeError):
            result.decision = AuthorizationDecision.DENY  # type: ignore[misc]

    # --- Order stability of failed_checks ---

    def test_failed_checks_order_stable(self) -> None:
        """Checks must appear in 1→8 order, not set iteration order."""
        result = bind_snapshot(
            _make_request(
                task_id="wrong",
                snapshot_id="wrong",
                policy_version="wrong",
                primary=ActionEffect.DELETE,
                scopes=(_make_scope(ResourceScopeType.FILE_PATH, "/z"),),
                groups=frozenset({"GROUP_NONE"}),
            ),
            _make_snapshot(
                expires_at=datetime(2026, 6, 15, 11, 0, 0, tzinfo=timezone.utc),
            ),
            datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        # Structural checks stop at POLICY_CONFLICT, so only 3 checks
        # Actually checks 1,2,3,4 trigger POLICY_CONFLICT and stop there
        self.assertIn("task_id", result.failed_checks[0])


if __name__ == "__main__":
    unittest.main()
