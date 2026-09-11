"""
GOAA Authorization Kernel AK-1 — Action Request
=================================================
Defines CanonicalParameter and ActionRequest — the input data models
for the authorization decision pipeline.

These are pure data models: no I/O, no subprocess, no Snapshot lookup.
Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §7, §8, §9
"""

from __future__ import annotations

from dataclasses import dataclass, field

from authorization_kernel.enums import ActionEffect
from authorization_kernel.resource_scope import (
    TypedResourceScope,
    canonical_resource_identity,
)


@dataclass(frozen=True)
class CanonicalParameter:
    """A single canonicalized parameter for an action request.

    resource_scope_indices: indices into ActionRequest.resource_scopes.
    Must be non-empty, non-negative, and contain no duplicates.
    """

    name: str
    value: str
    value_type: str
    resource_scope_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must not be empty")
        if not self.value_type:
            raise ValueError("value_type must not be empty")
        if not self.resource_scope_indices:
            raise ValueError("resource_scope_indices must not be empty")
        seen: set[int] = set()
        for idx in self.resource_scope_indices:
            if idx < 0:
                raise ValueError(f"negative index: {idx}")
            if idx in seen:
                raise ValueError(f"duplicate index: {idx}")
            seen.add(idx)


@dataclass(frozen=True)
class ActionRequest:
    """An authorization request for a single action.

    All fields validated at construction time.
    No Snapshot binding or authorization decision is performed here.
    """

    request_id: str
    task_id: str
    authorization_snapshot_id: str
    actor_id: str

    primary_effect: ActionEffect
    secondary_effects: frozenset[ActionEffect] = field(default_factory=frozenset)
    resource_scopes: tuple[TypedResourceScope, ...] = ()

    requested_tool: str = ""
    normalized_parameters: tuple[CanonicalParameter, ...] = ()
    parameters_digest: str = ""
    equivalent_action_groups: frozenset[str] = field(default_factory=frozenset)
    classification_policy_version: str = ""

    def __post_init__(self) -> None:
        # Core ID fields
        if not self.request_id:
            raise ValueError("request_id must not be empty")
        if not self.task_id:
            raise ValueError("task_id must not be empty")
        if not self.authorization_snapshot_id:
            raise ValueError("authorization_snapshot_id must not be empty")
        if not self.actor_id:
            raise ValueError("actor_id must not be empty")

        # Resource scopes
        if not self.resource_scopes:
            raise ValueError("resource_scopes must not be empty")
        seen_identities: set[str] = set()
        for scope in self.resource_scopes:
            ident = canonical_resource_identity(scope)
            if ident in seen_identities:
                raise ValueError(f"duplicate resource scope identity: {ident}")
            seen_identities.add(ident)

        # Validate normalized_parameters indices against resource_scopes
        num_scopes = len(self.resource_scopes)
        for param in self.normalized_parameters:
            for idx in param.resource_scope_indices:
                if idx >= num_scopes:
                    raise ValueError(
                        f"resource_scope_indices index {idx} out of bounds "
                        f"(max {num_scopes - 1})"
                    )

        # Equivalent action groups
        for group in self.equivalent_action_groups:
            if not group:
                raise ValueError("equivalent_action_groups must not contain empty strings")

        # Primary effect must not appear in secondary effects
        if self.primary_effect in self.secondary_effects:
            raise ValueError(
                f"primary_effect {self.primary_effect} must not appear "
                f"in secondary_effects"
            )
