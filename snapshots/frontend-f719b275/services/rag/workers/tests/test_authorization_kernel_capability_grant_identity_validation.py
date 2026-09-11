"""Tests for AK-5B2A identity-candidate field validation."""

from __future__ import annotations

import ast
import inspect
import unittest
from datetime import datetime, timedelta, timezone

from authorization_kernel import (
    capability_grant_identity_validation as validation_mod,
)
from authorization_kernel.canonical_serialization import (
    sha256_hex,
)
from authorization_kernel.capability_grant_identity import (
    CapabilityGrantIdentityCandidate,
)
from authorization_kernel.capability_grant_identity_validation import (
    validate_identity_candidate_fields,
)
from authorization_kernel.enums import (
    ActionEffect,
    ResourceScopeType,
)
from authorization_kernel.resource_scope import (
    TypedResourceScope,
)


UTC = timezone.utc
_HEX = sha256_hex("seed")


def _valid_kwargs(**overrides):
    """Return constructor kwargs for a valid (transient) identity candidate."""

    issued_at = overrides.pop("issued_at", datetime(2026, 1, 1, tzinfo=UTC))
    not_before = overrides.pop("not_before", issued_at)
    expires_at = overrides.pop("expires_at", issued_at + timedelta(hours=1))
    params = dict(
        grant_identity_digest="",
        grant_id=sha256_hex("grant"),
        envelope_candidate_digest=sha256_hex("env"),
        candidate_digest=sha256_hex("cand"),
        evidence_digest=sha256_hex("evid"),
        request_id="req-1",
        task_id="task-1",
        actor_id="actor-1",
        primary_effect=ActionEffect.READ,
        secondary_effects=frozenset(),
        resource_scopes=(
            TypedResourceScope(ResourceScopeType.FILE_PATH, "/tmp/x"),
        ),
        equivalent_action_groups=frozenset({"grp-1"}),
        requested_tool="tool-1",
        snapshot_id="snap-1",
        policy_version="pol-1",
        classification_attestation_hash=sha256_hex("cls"),
        issued_at=issued_at,
        not_before=not_before,
        expires_at=expires_at,
        issuer_claim_id="issuer-1",
        issuer_claim_version="v1",
        authority_proof_type="NONE",
    )
    params.update(overrides)
    return params


def _make(**overrides):
    return CapabilityGrantIdentityCandidate(**_valid_kwargs(**overrides))


class DigestFieldValidationTests(unittest.TestCase):
    def test_valid_passes(self):
        self.assertIsInstance(_make(), CapabilityGrantIdentityCandidate)

    def test_grant_identity_digest_empty_ok(self):
        self.assertIsInstance(
            _make(grant_identity_digest=""),
            CapabilityGrantIdentityCandidate,
        )

    def test_grant_identity_digest_valid_hex_ok(self):
        self.assertIsInstance(
            _make(grant_identity_digest=sha256_hex("z")),
            CapabilityGrantIdentityCandidate,
        )

    def test_grant_identity_digest_uppercase_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_identity_digest=sha256_hex("z").upper())

    def test_grant_identity_digest_short_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_identity_digest="abc")

    def test_grant_identity_digest_non_hex_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_identity_digest="g" * 64)

    def test_grant_identity_digest_non_str_rejected(self):
        with self.assertRaises(TypeError):
            _make(grant_identity_digest=123)

    def test_grant_id_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_id="")

    def test_grant_id_uppercase_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_id=sha256_hex("a").upper())

    def test_grant_id_non_str_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_id=None)

    def test_grant_id_wrong_length_63_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_id="a" * 63)

    def test_grant_id_wrong_length_65_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_id="a" * 65)

    def test_grant_id_unicode_wide_rejected(self):
        with self.assertRaises(ValueError):
            _make(grant_id="Ａ" * 64)

    def test_envelope_candidate_digest_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(envelope_candidate_digest="")

    def test_envelope_candidate_digest_bad_rejected(self):
        with self.assertRaises(ValueError):
            _make(envelope_candidate_digest="xyz")

    def test_candidate_digest_bad_rejected(self):
        with self.assertRaises(ValueError):
            _make(candidate_digest="zz")

    def test_evidence_digest_bad_rejected(self):
        with self.assertRaises(ValueError):
            _make(evidence_digest="zz")

    def test_classification_hash_bad_rejected(self):
        with self.assertRaises(ValueError):
            _make(classification_attestation_hash="zz")


class IdentityStringValidationTests(unittest.TestCase):
    def test_request_id_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(request_id="   ")

    def test_request_id_non_str_rejected(self):
        with self.assertRaises(TypeError):
            _make(request_id=1)

    def test_task_id_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(task_id="")

    def test_actor_id_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(actor_id="")

    def test_snapshot_id_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(snapshot_id="")

    def test_policy_version_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(policy_version="")

    def test_issuer_claim_id_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(issuer_claim_id="")

    def test_issuer_claim_version_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(issuer_claim_version="")

    def test_requested_tool_empty_allowed(self):
        self.assertIsInstance(
            _make(requested_tool=""), CapabilityGrantIdentityCandidate
        )

    def test_requested_tool_non_str_rejected(self):
        with self.assertRaises(TypeError):
            _make(requested_tool=5)

    def test_authority_proof_type_not_none_rejected(self):
        with self.assertRaises(ValueError):
            _make(authority_proof_type="SIGNED")

    def test_authority_proof_type_lowercase_rejected(self):
        with self.assertRaises(ValueError):
            _make(authority_proof_type="none")

    def test_authority_proof_type_non_str_rejected(self):
        with self.assertRaises(TypeError):
            _make(authority_proof_type=None)


class EffectsValidationTests(unittest.TestCase):
    def test_primary_not_effect_rejected(self):
        with self.assertRaises(TypeError):
            _make(primary_effect="read")

    def test_secondary_not_frozenset_rejected(self):
        with self.assertRaises(TypeError):
            _make(secondary_effects={ActionEffect.WRITE})

    def test_secondary_entry_not_effect_rejected(self):
        with self.assertRaises(TypeError):
            _make(secondary_effects=frozenset({"write"}))

    def test_primary_in_secondary_rejected(self):
        with self.assertRaises(ValueError):
            _make(
                primary_effect=ActionEffect.READ,
                secondary_effects=frozenset({ActionEffect.READ}),
            )

    def test_disjoint_effects_pass(self):
        self.assertIsInstance(
            _make(
                primary_effect=ActionEffect.READ,
                secondary_effects=frozenset({ActionEffect.WRITE}),
            ),
            CapabilityGrantIdentityCandidate,
        )


class ResourceScopeValidationTests(unittest.TestCase):
    def test_not_tuple_rejected(self):
        with self.assertRaises(TypeError):
            _make(resource_scopes=[
                TypedResourceScope(ResourceScopeType.FILE_PATH, "/a")
            ])

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            _make(resource_scopes=())

    def test_entry_not_scope_rejected(self):
        with self.assertRaises(TypeError):
            _make(resource_scopes=("/a",))

    def test_duplicate_canonical_rejected(self):
        scope = TypedResourceScope(ResourceScopeType.FILE_PATH, "/a")
        with self.assertRaises(ValueError):
            _make(resource_scopes=(scope, scope))

    def test_distinct_scopes_pass(self):
        scopes = (
            TypedResourceScope(ResourceScopeType.FILE_PATH, "/a"),
            TypedResourceScope(ResourceScopeType.FILE_PATH, "/b"),
        )
        self.assertIsInstance(
            _make(resource_scopes=scopes), CapabilityGrantIdentityCandidate
        )


class EquivalentActionGroupValidationTests(unittest.TestCase):
    def test_not_frozenset_rejected(self):
        with self.assertRaises(TypeError):
            _make(equivalent_action_groups={"grp"})

    def test_entry_not_str_rejected(self):
        with self.assertRaises(TypeError):
            _make(equivalent_action_groups=frozenset({1}))

    def test_empty_str_entry_rejected(self):
        with self.assertRaises(ValueError):
            _make(equivalent_action_groups=frozenset({""}))

    def test_empty_set_allowed(self):
        self.assertIsInstance(
            _make(equivalent_action_groups=frozenset()),
            CapabilityGrantIdentityCandidate,
        )


class TimeFieldValidationTests(unittest.TestCase):
    def test_naive_issued_at_rejected(self):
        naive = datetime(2026, 1, 1)
        with self.assertRaises(ValueError):
            _make(issued_at=naive, not_before=naive)

    def test_naive_expires_at_rejected(self):
        with self.assertRaises(ValueError):
            _make(expires_at=datetime(2026, 1, 2))

    def test_not_before_must_equal_issued_at(self):
        issued = datetime(2026, 1, 1, tzinfo=UTC)
        with self.assertRaises(ValueError):
            _make(
                issued_at=issued,
                not_before=issued + timedelta(seconds=1),
                expires_at=issued + timedelta(hours=1),
            )

    def test_expires_before_not_before_rejected(self):
        issued = datetime(2026, 1, 1, tzinfo=UTC)
        with self.assertRaises(ValueError):
            _make(
                issued_at=issued,
                not_before=issued,
                expires_at=issued - timedelta(hours=1),
            )

    def test_expires_at_none_rejected(self):
        with self.assertRaises(TypeError):
            _make(expires_at=None)

    def test_issued_at_non_datetime_rejected(self):
        with self.assertRaises(TypeError):
            _make(issued_at="2026-01-01", not_before="2026-01-01")

    def test_valid_times_pass(self):
        self.assertIsInstance(_make(), CapabilityGrantIdentityCandidate)


class ValidationDirectCallTests(unittest.TestCase):
    def test_validate_returns_none_on_valid(self):
        candidate = _make()
        self.assertIsNone(validate_identity_candidate_fields(candidate))


class ValidationNoAssertTests(unittest.TestCase):
    def test_no_assert_in_validation_module(self):
        source = inspect.getsource(validation_mod)
        tree = ast.parse(source)
        asserts = [
            node for node in ast.walk(tree) if isinstance(node, ast.Assert)
        ]
        self.assertEqual(asserts, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()