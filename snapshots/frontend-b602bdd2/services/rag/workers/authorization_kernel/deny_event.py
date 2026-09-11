"""
GOAA Authorization Kernel AK-1 — Deny Event
=============================================
Defines the DenyEvent dataclass — the core event record in the
append-only, event-sourced Deny Ledger model.

AK-1 defines only the data model. Ledger storage, querying,
and state folding are implemented in AK-2.

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §15
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from authorization_kernel.enums import (
    ActionEffect,
    DenyEventType,
    DenyOrigin,
    DenyScope,
)
from authorization_kernel.resource_scope import (
    TypedResourceScope,
    canonical_resource_identity,
)


@dataclass(frozen=True)
class DenyEvent:
    """An event record in the append-only Deny Ledger.

    event_hash: SHA-256 covering all fields except itself.
    previous_event_hash: SHA-256 of the preceding event in this deny chain.
        None for the first DENY_CREATED in a chain (no predecessor).
    """

    event_id: str
    deny_id: str
    task_id: str
    session_id: str | None = None

    event_type: DenyEventType = DenyEventType.DENY_CREATED
    deny_scope: DenyScope = DenyScope.CURRENT_ACTION
    deny_origin: DenyOrigin = DenyOrigin.AUTOMATIC_POLICY_BLOCK

    primary_effect: ActionEffect = ActionEffect.READ
    secondary_effects: frozenset[ActionEffect] = field(default_factory=frozenset)

    resource_scopes: tuple[TypedResourceScope, ...] = ()
    equivalent_action_groups: frozenset[str] = field(default_factory=frozenset)

    actor: str = ""
    occurred_at: datetime | None = None
    expires_at: datetime | None = None

    reason: str = ""
    approval_id: str | None = None

    previous_event_hash: str | None = None
    event_hash: str = ""

    def __post_init__(self) -> None:
        # Core ID fields
        if not self.event_id:
            raise ValueError("event_id must not be empty")
        if not self.deny_id:
            raise ValueError("deny_id must not be empty")
        if not self.task_id:
            raise ValueError("task_id must not be empty")

        # Timezone awareness
        if self.occurred_at is not None and self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")

        # Expiry ordering
        if (
            self.occurred_at is not None
            and self.expires_at is not None
            and self.expires_at < self.occurred_at
        ):
            raise ValueError("expires_at must not be earlier than occurred_at")

        # Resource scopes must not be empty
        if not self.resource_scopes:
            raise ValueError("resource_scopes must not be empty")

        # No duplicate canonical resource identities
        seen_identities: set[str] = set()
        for scope in self.resource_scopes:
            ident = canonical_resource_identity(scope)
            if ident in seen_identities:
                raise ValueError(
                    f"duplicate resource scope identity: {ident}"
                )
            seen_identities.add(ident)

        # Actor must not be empty
        if not self.actor:
            raise ValueError("actor must not be empty")

        # Event hash format validation
        if self.event_hash and not _is_valid_sha256_hex(self.event_hash):
            raise ValueError(
                f"event_hash must be 64-char lowercase hex, got '{self.event_hash}'"
            )

        # previous_event_hash format validation
        if self.previous_event_hash is not None:
            if not self.previous_event_hash:
                raise ValueError("previous_event_hash must not be empty")
            if not _is_valid_sha256_hex(self.previous_event_hash):
                raise ValueError(
                    f"previous_event_hash must be 64-char lowercase hex, "
                    f"got '{self.previous_event_hash}'"
                )


def _is_valid_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False
