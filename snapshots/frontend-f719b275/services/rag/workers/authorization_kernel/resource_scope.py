"""
GOAA Authorization Kernel AK-1 — Resource Scope
=================================================
Defines TypedResourceScope and NetworkDestination — pure data models
that represent canonical resource identities without accessing any
external system (no filesystem, no DNS, no Git, no network).

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §6
"""

from __future__ import annotations

from dataclasses import dataclass, field

from authorization_kernel.enums import ResourceScopeType


@dataclass(frozen=True)
class NetworkDestination:
    """A network endpoint identified by its canonical host identity.

    All fields are pure data — no DNS resolution, no network I/O.
    """

    canonical_host_id: str
    port: int
    protocol: str
    approved_address_set: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.canonical_host_id:
            raise ValueError("canonical_host_id must not be empty")
        if not (1 <= self.port <= 65535):
            raise ValueError(f"port must be 1-65535, got {self.port}")
        if not self.protocol:
            raise ValueError("protocol must not be empty")
        # Normalize protocol to lowercase via object.__setattr__ for frozen
        normalized = self.protocol.lower()
        if normalized != self.protocol:
            object.__setattr__(self, "protocol", normalized)
        # Check approved_address_set is a tuple
        if not isinstance(self.approved_address_set, tuple):
            raise TypeError("approved_address_set must be a tuple")
        # Check for duplicate addresses
        seen: set[str] = set()
        for addr in self.approved_address_set:
            if addr in seen:
                raise ValueError(f"duplicate address in approved_address_set: {addr}")
            seen.add(addr)


@dataclass(frozen=True)
class TypedResourceScope:
    """A typed, canonicalized resource identity.

    scope_type: one of 9 ResourceScopeType values
    canonical_id: stable, unique identity string for this resource
    attributes: set-like key-value metadata pairs

    No filesystem, Git, systemd, or network access is performed.
    """

    scope_type: ResourceScopeType
    canonical_id: str
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.canonical_id:
            raise ValueError("canonical_id must not be empty")
        if not isinstance(self.attributes, tuple):
            raise TypeError("attributes must be a tuple")
        seen_keys: set[str] = set()
        for key, value in self.attributes:
            if not key:
                raise ValueError("attribute key must not be empty")
            if key in seen_keys:
                raise ValueError(f"duplicate attribute key: {key}")
            seen_keys.add(key)


def canonical_resource_identity(scope: TypedResourceScope) -> str:
    """Form a stable canonical identity from a TypedResourceScope.

    This function operates purely on object fields — no external access.
    """
    parts: list[str] = [scope.scope_type.value, scope.canonical_id]
    if scope.attributes:
        sorted_attrs = sorted(scope.attributes, key=lambda kv: kv[0])
        for key, value in sorted_attrs:
            parts.append(f"{key}={value}")
    return ":".join(parts)
