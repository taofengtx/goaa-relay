"""
GOAA Authorization Kernel AK-1 — Public API
=============================================

Re-exports the public API for AK-1 (Schema / Enum / Canonical Serialization).

No initialization logic, no file reads, no database connections,
no environment variable reads, no Worker/Router registration.
"""

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
from authorization_kernel.action_request import ActionRequest, CanonicalParameter
from authorization_kernel.authorization_snapshot import (
    AuthorizationSnapshot,
    compute_snapshot_hash,
    snapshot_payload,
    verify_snapshot_hash,
)
from authorization_kernel.deny_event import DenyEvent
from authorization_kernel.classification_attestation import (
    ClassificationAttestation,
    attestation_payload,
    classification_matches,
    compute_attestation_hash,
    verify_attestation_hash,
)
from authorization_kernel.canonical_serialization import (
    SetLikeTuple,
    canonical_json_bytes,
    canonicalize,
    canonicalize_set_like_tuple,
    format_utc_rfc3339,
    normalize_text,
    sha256_hex,
)

__all__ = [
    # Enums
    "ActionEffect",
    "AuthorizationDecision",
    "ControlPlaneEvent",
    "DenyEventType",
    "DenyOrigin",
    "DenyScope",
    "ResourceScopeType",
    # Dataclasses
    "ActionRequest",
    "AuthorizationSnapshot",
    "CanonicalParameter",
    "ClassificationAttestation",
    "DenyEvent",
    "NetworkDestination",
    "TypedResourceScope",
    # Functions
    "attestation_payload",
    "canonical_json_bytes",
    "canonical_resource_identity",
    "canonicalize",
    "canonicalize_set_like_tuple",
    "classification_matches",
    "compute_attestation_hash",
    "compute_snapshot_hash",
    "format_utc_rfc3339",
    "normalize_text",
    "sha256_hex",
    "snapshot_payload",
    "verify_attestation_hash",
    "verify_snapshot_hash",
    # Types
    "SetLikeTuple",
]
