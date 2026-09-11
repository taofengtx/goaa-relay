"""
GOAA Authorization Kernel AK-1 — Enums
========================================
Defines the 7 core enums for the Authorization Kernel.

These enums are pure data definitions — no I/O, no subprocess,
no external dependencies. All values use lowercase snake_case.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §4, §5, §13.2
"""

from __future__ import annotations

import enum


class ActionEffect(enum.Enum):
    """14 execution action effects — the factual semantic effect of an action."""

    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"
    RENAME = "rename"
    MOVE_OUT_OF_DISCOVERY = "move_out_of_discovery"
    EXECUTE = "execute"
    COMMIT = "commit"
    PUSH = "push"
    DEPLOY = "deploy"
    SERVICE_RESTART = "service_restart"
    SECRET_READ = "secret_read"
    NETWORK_EGRESS = "network_egress"
    PERMISSION_CHANGE = "permission_change"


class ControlPlaneEvent(enum.Enum):
    """4 control plane events — meta-events in the authorization lifecycle."""

    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    APPROVAL_EXPIRED = "approval_expired"
    APPROVAL_REVOKED = "approval_revoked"


class ResourceScopeType(enum.Enum):
    """9 typed resource scope categories."""

    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    GIT_REPOSITORY = "git_repository"
    GIT_REF = "git_ref"
    SERVICE_UNIT = "service_unit"
    REMOTE_NODE = "remote_node"
    API_RESOURCE = "api_resource"
    NETWORK_DESTINATION = "network_destination"
    SECRET_RESOURCE = "secret_resource"


class DenyEventType(enum.Enum):
    """4 deny event lifecycle types (event-sourced model)."""

    DENY_CREATED = "deny_created"
    DENY_REVOKED = "deny_revoked"
    DENY_SUPERSEDED = "deny_superseded"
    DENY_EXPIRED = "deny_expired"


class DenyScope(enum.Enum):
    """Scoping level for a denial event."""

    CURRENT_ACTION = "current_action"
    CURRENT_TASK = "current_task"
    CURRENT_SESSION = "current_session"
    PERSISTENT_POLICY = "persistent_policy"


class DenyOrigin(enum.Enum):
    """Origin source of a denial event."""

    USER_DENIAL = "user_denial"
    APPROVER_DENIAL = "approver_denial"
    PERSISTENT_POLICY = "persistent_policy"
    AUTOMATIC_POLICY_BLOCK = "automatic_policy_block"


class AuthorizationDecision(enum.Enum):
    """5 possible authorization outcomes from authorize_action()."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRES_APPROVAL = "requires_approval"
    OUT_OF_SCOPE = "out_of_scope"
    POLICY_CONFLICT = "policy_conflict"
