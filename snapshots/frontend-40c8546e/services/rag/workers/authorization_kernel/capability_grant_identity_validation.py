"""Validation helpers for the AK-5B2A capability grant identity candidate.

These helpers are split out of ``capability_grant_identity.py`` so the
dataclass module stays focused on the shape of the data while this module
owns the *fail-closed* field validation.

Every check uses an explicit ``if`` plus a raised exception. There are no
executable ``assert`` statements anywhere in this module, so running under
``python -O`` does not weaken any check.
"""

from __future__ import annotations

from datetime import datetime

from authorization_kernel.enums import ActionEffect
from authorization_kernel.resource_scope import TypedResourceScope, canonical_resource_identity


__all__ = [
    "validate_identity_candidate_fields",
]


_SHA256_HEX_CHARS = frozenset("0123456789abcdef")


def _is_strict_sha256_hex(value: object) -> bool:
    """Return ``True`` iff ``value`` is a 64-char lowercase hex string."""

    if not isinstance(value, str):
        return False
    if len(value) != 64:
        return False
    return all(c in _SHA256_HEX_CHARS for c in value)


def _require_strict_sha256_hex(value: object, label: str) -> None:
    """Raise ``ValueError`` unless ``value`` is strict SHA-256 hex."""

    if not _is_strict_sha256_hex(value):
        raise ValueError(f"{label} must be 64-char lowercase sha256 hex")


def validate_identity_candidate_fields(value: object) -> None:
    """Validate all identity-candidate fields, fail-closed."""

    _validate_digest_fields(value)
    _validate_identity_fields(value)
    _validate_effects(value)
    _validate_resource_scopes(value)
    _validate_equivalent_action_groups(value)
    _validate_time_fields(value)
    _validate_authority_proof_type(value)


def _validate_digest_fields(value: object) -> None:
    """Validate the self-digest, the derived identity, and digest columns."""

    # The self-digest may be empty for a transient (pre-seal) candidate.
    identity_digest = value.grant_identity_digest
    if not isinstance(identity_digest, str):
        raise TypeError("grant_identity_digest must be a str")
    if identity_digest != "" and not _is_strict_sha256_hex(identity_digest):
        raise ValueError(
            "grant_identity_digest must be sha256 hex or empty"
        )

    # The derived identity and the wrapped digests are always required.
    _require_strict_sha256_hex(value.grant_id, "grant_id")
    _require_strict_sha256_hex(
        value.envelope_candidate_digest, "envelope_candidate_digest"
    )
    _require_strict_sha256_hex(value.candidate_digest, "candidate_digest")
    _require_strict_sha256_hex(value.evidence_digest, "evidence_digest")
    _require_strict_sha256_hex(
        value.classification_attestation_hash,
        "classification_attestation_hash",
    )


def _validate_identity_fields(value: object) -> None:
    """Validate the identity string columns."""

    for name in (
        "request_id",
        "task_id",
        "actor_id",
        "snapshot_id",
        "policy_version",
        "issuer_claim_id",
        "issuer_claim_version",
    ):
        raw = getattr(value, name)
        if not isinstance(raw, str):
            raise TypeError(f"{name} must be a str")
        if not raw.strip():
            raise ValueError(f"{name} must be non-empty")

    requested_tool = value.requested_tool
    if not isinstance(requested_tool, str):
        raise TypeError("requested_tool must be a str")


def _validate_effects(value: object) -> None:
    """Validate the primary/secondary action effects."""

    if not isinstance(value.primary_effect, ActionEffect):
        raise TypeError("primary_effect must be an ActionEffect")

    secondary = value.secondary_effects
    if not isinstance(secondary, frozenset):
        raise TypeError("secondary_effects must be a frozenset")
    for effect in secondary:
        if not isinstance(effect, ActionEffect):
            raise TypeError("secondary_effects entries must be ActionEffect")

    if value.primary_effect in secondary:
        raise ValueError(
            "primary_effect must not also appear in secondary_effects"
        )


def _validate_resource_scopes(value: object) -> None:
    """Validate the typed resource scopes and reject duplicates."""

    scopes = value.resource_scopes
    if not isinstance(scopes, tuple):
        raise TypeError("resource_scopes must be a tuple")
    if not scopes:
        raise ValueError("resource_scopes must be non-empty")

    seen: set[str] = set()
    for scope in scopes:
        if not isinstance(scope, TypedResourceScope):
            raise TypeError(
                "resource_scopes entries must be TypedResourceScope"
            )
        identity = canonical_resource_identity(scope)
        if identity in seen:
            raise ValueError("resource_scopes must not contain duplicates")
        seen.add(identity)


def _validate_equivalent_action_groups(value: object) -> None:
    """Validate the equivalent-action-group labels."""

    groups = value.equivalent_action_groups
    if not isinstance(groups, frozenset):
        raise TypeError("equivalent_action_groups must be a frozenset")
    for group in groups:
        if not isinstance(group, str):
            raise TypeError("equivalent_action_groups entries must be str")
        if not group:
            raise ValueError(
                "equivalent_action_groups entries must be non-empty"
            )


def _validate_time_fields(value: object) -> None:
    """Validate the issued/not-before/expiry time bounds."""

    issued_at = value.issued_at
    not_before = value.not_before
    expires_at = value.expires_at

    for label, ts in (
        ("issued_at", issued_at),
        ("not_before", not_before),
        ("expires_at", expires_at),
    ):
        if not isinstance(ts, datetime):
            raise TypeError(f"{label} must be a datetime")
        if ts.tzinfo is None or ts.utcoffset() is None:
            raise ValueError(f"{label} must be timezone-aware")

    if not_before != issued_at:
        raise ValueError("not_before must equal issued_at")

    if expires_at < not_before:
        raise ValueError("expires_at must be at or after not_before")


def _validate_authority_proof_type(value: object) -> None:
    """Validate the authority proof type marker."""

    proof_type = value.authority_proof_type
    if not isinstance(proof_type, str):
        raise TypeError("authority_proof_type must be a str")
    if proof_type != "NONE":
        raise ValueError('authority_proof_type must be "NONE"')


# (end of module)