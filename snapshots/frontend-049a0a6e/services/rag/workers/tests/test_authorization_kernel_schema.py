"""
GOAA Authorization Kernel AK-1 — Schema Unit Tests
====================================================
Tests: enum values/counts, dataclass invariants, validation rules.

Framework: unittest (standard library). No pytest dependency.
All tests are pure — no I/O, no subprocess, no network.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from typing import Any

from authorization_kernel.enums import (
    ActionEffect,
    AuthorizationDecision,
    ControlPlaneEvent,
    DenyEventType,
    DenyOrigin,
    DenyScope,
    ResourceScopeType,
)
from authorization_kernel.resource_scope import (
    NetworkDestination,
    TypedResourceScope,
    canonical_resource_identity,
)
from authorization_kernel.action_request import CanonicalParameter, ActionRequest
from authorization_kernel.authorization_snapshot import AuthorizationSnapshot
from authorization_kernel.deny_event import DenyEvent
from authorization_kernel.classification_attestation import (
    ClassificationAttestation,
)


# ============================================================
# Enum tests
# ============================================================

class TestActionEffectEnum(unittest.TestCase):

    def test_count(self) -> None:
        self.assertEqual(len(ActionEffect), 14)

    def test_values_all_lowercase_snake(self) -> None:
        for member in ActionEffect:
            value: str = member.value
            self.assertFalse(value.startswith("_"), f"unexpected prefix: {value}")
            self.assertEqual(value, value.lower(), f"not lowercase: {value}")

    def test_known_members(self) -> None:
        expected = {
            "READ", "WRITE", "CREATE", "DELETE", "RENAME",
            "MOVE_OUT_OF_DISCOVERY", "EXECUTE", "COMMIT", "PUSH",
            "DEPLOY", "SERVICE_RESTART", "SECRET_READ",
            "NETWORK_EGRESS", "PERMISSION_CHANGE",
        }
        names = {m.name for m in ActionEffect}
        self.assertEqual(names, expected)

    def test_unique_values(self) -> None:
        values = [m.value for m in ActionEffect]
        self.assertEqual(len(values), len(set(values)))


class TestControlPlaneEventEnum(unittest.TestCase):

    def test_count(self) -> None:
        self.assertEqual(len(ControlPlaneEvent), 4)

    def test_known_members(self) -> None:
        expected = {"APPROVAL_GRANTED", "APPROVAL_DENIED",
                     "APPROVAL_EXPIRED", "APPROVAL_REVOKED"}
        names = {m.name for m in ControlPlaneEvent}
        self.assertEqual(names, expected)


class TestResourceScopeTypeEnum(unittest.TestCase):

    def test_count(self) -> None:
        self.assertEqual(len(ResourceScopeType), 9)

    def test_known_members(self) -> None:
        expected = {
            "FILE_PATH", "DIRECTORY_PATH", "GIT_REPOSITORY",
            "GIT_REF", "SERVICE_UNIT", "REMOTE_NODE",
            "API_RESOURCE", "NETWORK_DESTINATION", "SECRET_RESOURCE",
        }
        names = {m.name for m in ResourceScopeType}
        self.assertEqual(names, expected)


class TestDenyEventTypeEnum(unittest.TestCase):

    def test_count(self) -> None:
        self.assertEqual(len(DenyEventType), 4)

    def test_known_members(self) -> None:
        expected = {"DENY_CREATED", "DENY_REVOKED",
                     "DENY_SUPERSEDED", "DENY_EXPIRED"}
        names = {m.name for m in DenyEventType}
        self.assertEqual(names, expected)


class TestDenyScopeEnum(unittest.TestCase):

    def test_count(self) -> None:
        self.assertEqual(len(DenyScope), 4)

    def test_known_members(self) -> None:
        expected = {"CURRENT_ACTION", "CURRENT_TASK",
                     "CURRENT_SESSION", "PERSISTENT_POLICY"}
        names = {m.name for m in DenyScope}
        self.assertEqual(names, expected)


class TestDenyOriginEnum(unittest.TestCase):

    def test_count(self) -> None:
        self.assertEqual(len(DenyOrigin), 4)

    def test_known_members(self) -> None:
        expected = {"USER_DENIAL", "APPROVER_DENIAL",
                     "PERSISTENT_POLICY", "AUTOMATIC_POLICY_BLOCK"}
        names = {m.name for m in DenyOrigin}
        self.assertEqual(names, expected)


class TestAuthorizationDecisionEnum(unittest.TestCase):

    def test_count(self) -> None:
        self.assertEqual(len(AuthorizationDecision), 5)

    def test_known_members(self) -> None:
        expected = {"ALLOW", "DENY", "REQUIRES_APPROVAL",
                     "OUT_OF_SCOPE", "POLICY_CONFLICT"}
        names = {m.name for m in AuthorizationDecision}
        self.assertEqual(names, expected)


# ============================================================
# NetworkDestination tests
# ============================================================

class TestNetworkDestination(unittest.TestCase):

    def test_valid_minimal(self) -> None:
        nd = NetworkDestination(canonical_host_id="example.com", port=443, protocol="tcp")
        self.assertEqual(nd.protocol, "tcp")

    def test_protocol_normalized(self) -> None:
        nd = NetworkDestination(canonical_host_id="example.com", port=80, protocol="TCP")
        self.assertEqual(nd.protocol, "tcp")

    def test_empty_host_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NetworkDestination(canonical_host_id="", port=443, protocol="tcp")

    def test_port_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NetworkDestination(canonical_host_id="host", port=0, protocol="tcp")

    def test_port_65536_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NetworkDestination(canonical_host_id="host", port=65536, protocol="tcp")

    def test_empty_protocol_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NetworkDestination(canonical_host_id="host", port=443, protocol="")

    def test_duplicate_address_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NetworkDestination(
                canonical_host_id="host",
                port=443,
                protocol="tcp",
                approved_address_set=("10.0.0.1", "10.0.0.1"),
            )

    def test_approved_addresses_tuple_type(self) -> None:
        with self.assertRaises(TypeError):
            NetworkDestination(
                canonical_host_id="host",
                port=443,
                protocol="tcp",
                approved_address_set=["not", "a", "tuple"],  # type: ignore[arg-type]
            )

    def test_frozen(self) -> None:
        nd = NetworkDestination(canonical_host_id="h", port=1, protocol="t")
        with self.assertRaises(AttributeError):
            nd.port = 8080  # type: ignore[misc]


# ============================================================
# TypedResourceScope tests
# ============================================================

class TestTypedResourceScope(unittest.TestCase):

    def test_valid_minimal(self) -> None:
        scope = TypedResourceScope(
            scope_type=ResourceScopeType.FILE_PATH,
            canonical_id="/home/aika/test.txt",
        )
        self.assertEqual(scope.scope_type, ResourceScopeType.FILE_PATH)

    def test_empty_canonical_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TypedResourceScope(
                scope_type=ResourceScopeType.FILE_PATH,
                canonical_id="",
            )

    def test_duplicate_attribute_key_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TypedResourceScope(
                scope_type=ResourceScopeType.GIT_REPOSITORY,
                canonical_id="repo",
                attributes=(("owner", "aika"), ("owner", "tao")),
            )

    def test_empty_attribute_key_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TypedResourceScope(
                scope_type=ResourceScopeType.GIT_REPOSITORY,
                canonical_id="repo",
                attributes=(("", "value"),),
            )

    def test_attributes_tuple_type(self) -> None:
        with self.assertRaises(TypeError):
            TypedResourceScope(
                scope_type=ResourceScopeType.GIT_REPOSITORY,
                canonical_id="repo",
                attributes=[("k", "v")],  # type: ignore[arg-type]
            )

    def test_canonical_resource_identity(self) -> None:
        scope = TypedResourceScope(
            scope_type=ResourceScopeType.FILE_PATH,
            canonical_id="/etc/hosts",
            attributes=(("checksum", "abc123"),),
        )
        ident = canonical_resource_identity(scope)
        self.assertEqual(ident, "file_path:/etc/hosts:checksum=abc123")

    def test_canonical_identity_no_attributes(self) -> None:
        scope = TypedResourceScope(
            scope_type=ResourceScopeType.GIT_REPOSITORY,
            canonical_id="goaa-ai-main",
        )
        self.assertEqual(
            canonical_resource_identity(scope),
            "git_repository:goaa-ai-main",
        )

    def test_frozen(self) -> None:
        scope = TypedResourceScope(
            scope_type=ResourceScopeType.FILE_PATH,
            canonical_id="/tmp/x",
        )
        with self.assertRaises(AttributeError):
            scope.canonical_id = "/tmp/y"  # type: ignore[misc]


# ============================================================
# CanonicalParameter tests
# ============================================================

class TestCanonicalParameter(unittest.TestCase):

    def test_valid(self) -> None:
        cp = CanonicalParameter(
            name="path", value="/tmp/test", value_type="file", resource_scope_indices=(0,)
        )
        self.assertEqual(cp.name, "path")

    def test_empty_name_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CanonicalParameter(name="", value="x", value_type="f", resource_scope_indices=(0,))

    def test_empty_value_type_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CanonicalParameter(name="n", value="x", value_type="", resource_scope_indices=(0,))

    def test_empty_indices_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CanonicalParameter(
                name="n", value="x", value_type="f", resource_scope_indices=()
            )

    def test_negative_index_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CanonicalParameter(
                name="n", value="x", value_type="f", resource_scope_indices=(-1,)
            )

    def test_duplicate_index_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CanonicalParameter(
                name="n", value="x", value_type="f", resource_scope_indices=(0, 0)
            )

    def test_frozen(self) -> None:
        cp = CanonicalParameter(name="n", value="x", value_type="f", resource_scope_indices=(0,))
        with self.assertRaises(AttributeError):
            cp.name = "new"  # type: ignore[misc]


# ============================================================
# ActionRequest tests
# ============================================================

class TestActionRequest(unittest.TestCase):

    def _make_scope(self, ident: str = "/tmp/test") -> TypedResourceScope:
        return TypedResourceScope(
            scope_type=ResourceScopeType.FILE_PATH,
            canonical_id=ident,
        )

    def _make_param(self, indices: tuple[int, ...] = (0,)) -> CanonicalParameter:
        return CanonicalParameter(
            name="path", value="/tmp/test", value_type="file",
            resource_scope_indices=indices,
        )

    def test_valid_minimal(self) -> None:
        req = ActionRequest(
            request_id="req-1",
            task_id="task-1",
            authorization_snapshot_id="snap-1",
            actor_id="agent-1",
            primary_effect=ActionEffect.READ,
            resource_scopes=(self._make_scope(),),
        )
        self.assertEqual(req.request_id, "req-1")

    def test_empty_request_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="", task_id="t", authorization_snapshot_id="s",
                actor_id="a", primary_effect=ActionEffect.READ,
                resource_scopes=(self._make_scope(),),
            )

    def test_empty_task_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="r", task_id="", authorization_snapshot_id="s",
                actor_id="a", primary_effect=ActionEffect.READ,
                resource_scopes=(self._make_scope(),),
            )

    def test_empty_snapshot_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="r", task_id="t", authorization_snapshot_id="",
                actor_id="a", primary_effect=ActionEffect.READ,
                resource_scopes=(self._make_scope(),),
            )

    def test_empty_actor_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="r", task_id="t", authorization_snapshot_id="s",
                actor_id="", primary_effect=ActionEffect.READ,
                resource_scopes=(self._make_scope(),),
            )

    def test_empty_resource_scopes_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="r", task_id="t", authorization_snapshot_id="s",
                actor_id="a", primary_effect=ActionEffect.READ,
                resource_scopes=(),
            )

    def test_duplicate_resource_identity_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="r", task_id="t", authorization_snapshot_id="s",
                actor_id="a", primary_effect=ActionEffect.READ,
                resource_scopes=(self._make_scope("/same"), self._make_scope("/same")),
            )

    def test_index_out_of_bounds_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="r", task_id="t", authorization_snapshot_id="s",
                actor_id="a", primary_effect=ActionEffect.READ,
                resource_scopes=(self._make_scope(),),
                normalized_parameters=(self._make_param(indices=(5,)),),
            )

    def test_primary_effect_in_secondary_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="r", task_id="t", authorization_snapshot_id="s",
                actor_id="a",
                primary_effect=ActionEffect.DELETE,
                secondary_effects=frozenset({ActionEffect.DELETE}),
                resource_scopes=(self._make_scope(),),
            )

    def test_empty_equivalent_group_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ActionRequest(
                request_id="r", task_id="t", authorization_snapshot_id="s",
                actor_id="a", primary_effect=ActionEffect.READ,
                resource_scopes=(self._make_scope(),),
                equivalent_action_groups=frozenset({""}),
            )

    def test_valid_with_all_fields(self) -> None:
        scope = self._make_scope()
        param = self._make_param()
        req = ActionRequest(
            request_id="req-1",
            task_id="task-1",
            authorization_snapshot_id="snap-1",
            actor_id="agent-1",
            primary_effect=ActionEffect.DEPLOY,
            secondary_effects=frozenset({ActionEffect.WRITE, ActionEffect.READ}),
            resource_scopes=(scope,),
            requested_tool="shell_execute",
            normalized_parameters=(param,),
            parameters_digest="abc123",
            equivalent_action_groups=frozenset({"GROUP_DEPLOY"}),
            classification_policy_version="v1.0",
        )
        self.assertEqual(req.primary_effect, ActionEffect.DEPLOY)
        self.assertIn(ActionEffect.WRITE, req.secondary_effects)

    def test_frozen(self) -> None:
        req = ActionRequest(
            request_id="r", task_id="t", authorization_snapshot_id="s",
            actor_id="a", primary_effect=ActionEffect.READ,
            resource_scopes=(self._make_scope(),),
        )
        with self.assertRaises(AttributeError):
            req.request_id = "new"  # type: ignore[misc]


# ============================================================
# AuthorizationSnapshot tests
# ============================================================

class TestAuthorizationSnapshot(unittest.TestCase):

    def _make_scope(self, ident: str = "/allowed/path") -> TypedResourceScope:
        return TypedResourceScope(
            scope_type=ResourceScopeType.FILE_PATH,
            canonical_id=ident,
        )

    def _make_snapshot(self, **overrides: Any) -> AuthorizationSnapshot:
        params: dict[str, Any] = {
            "snapshot_id": "snap-1",
            "task_id": "task-1",
            "policy_version": "v1.0",
            "created_at": datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        }
        params.update(overrides)
        return AuthorizationSnapshot(**params)

    def test_valid_minimal(self) -> None:
        snap = self._make_snapshot()
        self.assertEqual(snap.snapshot_id, "snap-1")

    def test_empty_snapshot_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_snapshot(snapshot_id="")

    def test_empty_task_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_snapshot(task_id="")

    def test_empty_policy_version_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_snapshot(policy_version="")

    def test_naive_created_at_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_snapshot(created_at=datetime(2026, 6, 15, 10, 0, 0))

    def test_naive_expires_at_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_snapshot(
                expires_at=datetime(2026, 6, 16, 10, 0, 0),
            )

    def test_expiry_before_created_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_snapshot(
                created_at=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                expires_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
            )

    def test_duplicate_resource_scope_rejected(self) -> None:
        scope = self._make_scope()
        with self.assertRaises(ValueError):
            AuthorizationSnapshot(
                snapshot_id="s", task_id="t", policy_version="v1",
                created_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
                allowed_resource_scopes=(scope, scope),
            )

    def test_invalid_hash_format_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_snapshot(snapshot_hash="not-a-sha256")

    def test_valid_hash_accepted(self) -> None:
        snap = self._make_snapshot(snapshot_hash="a" * 64)
        self.assertEqual(snap.snapshot_hash, "a" * 64)

    def test_frozen(self) -> None:
        snap = self._make_snapshot()
        with self.assertRaises(AttributeError):
            snap.task_id = "new"  # type: ignore[misc]


# ============================================================
# DenyEvent tests
# ============================================================

class TestDenyEvent(unittest.TestCase):

    def _make_scope(self, ident: str = "/denied/path") -> TypedResourceScope:
        return TypedResourceScope(
            scope_type=ResourceScopeType.FILE_PATH,
            canonical_id=ident,
        )

    def _make_event(self, **overrides: Any) -> DenyEvent:
        params: dict[str, Any] = {
            "event_id": "evt-1",
            "deny_id": "deny-1",
            "task_id": "task-1",
            "actor": "system",
            "resource_scopes": (self._make_scope(),),
            "occurred_at": datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        }
        params.update(overrides)
        return DenyEvent(**params)

    def test_valid_minimal(self) -> None:
        event = self._make_event()
        self.assertEqual(event.event_id, "evt-1")

    def test_empty_event_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(event_id="")

    def test_empty_deny_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(deny_id="")

    def test_empty_task_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(task_id="")

    def test_empty_actor_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(actor="")

    def test_empty_resource_scopes_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(resource_scopes=())

    def test_duplicate_resource_identity_rejected(self) -> None:
        scope = self._make_scope()
        with self.assertRaises(ValueError):
            self._make_event(resource_scopes=(scope, scope))

    def test_naive_occurred_at_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(
                occurred_at=datetime(2026, 6, 15, 10, 0, 0),
            )

    def test_expiry_before_occurred_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(
                occurred_at=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                expires_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
            )

    def test_invalid_event_hash_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(event_hash="too-short")

    def test_valid_event_hash_accepted(self) -> None:
        event = self._make_event(event_hash="a" * 64)
        self.assertEqual(event.event_hash, "a" * 64)

    def test_empty_previous_event_hash_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(previous_event_hash="")

    def test_invalid_previous_hash_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._make_event(previous_event_hash="bad")

    def test_previous_event_hash_none_allowed(self) -> None:
        event = self._make_event(previous_event_hash=None)
        self.assertIsNone(event.previous_event_hash)

    def test_frozen(self) -> None:
        event = self._make_event()
        with self.assertRaises(AttributeError):
            event.event_id = "new"  # type: ignore[misc]


# ============================================================
# ClassificationAttestation tests
# ============================================================

class TestClassificationAttestation(unittest.TestCase):

    def test_valid_minimal(self) -> None:
        att = ClassificationAttestation(
            classification_policy_version="v1.0",
            declared_primary_effect=ActionEffect.READ,
            recomputed_primary_effect=ActionEffect.READ,
        )
        self.assertEqual(att.classification_policy_version, "v1.0")

    def test_empty_policy_version_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ClassificationAttestation(
                classification_policy_version="",
                declared_primary_effect=ActionEffect.READ,
                recomputed_primary_effect=ActionEffect.READ,
            )

    def test_frozen(self) -> None:
        att = ClassificationAttestation(
            classification_policy_version="v1",
            declared_primary_effect=ActionEffect.READ,
            recomputed_primary_effect=ActionEffect.READ,
        )
        with self.assertRaises(AttributeError):
            att.classification_policy_version = "v2"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
