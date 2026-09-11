"""
GOAA Authorization Kernel AK-5B — CapabilityGrantEnvelopeCandidate Model Tests
==============================================================================
Framework: unittest (standard library). No pytest, no third-party deps.
All tests are pure — no file I/O, no network, no subprocess, no clock reads.

Covers: frozen dataclass, the nine class-level boundary markers (including
BOTH NOT_AUTHORITY_PROOF and NOT_ISSUED_GRANT), 20 required no-default
instance fields, empty-ID rejection, illegal / uppercase / non-hex digest
rejection, naive datetimes, tzinfo-present-but-utcoffset-None, not_before ==
issued_at, expires_at >= not_before, primary/secondary effect disjointness,
authority_proof_type == "NONE" enforcement, the candidate_digest exclusion
from the payload, per-field digest sensitivity, and set-like order stability.

BLOCKER 8 additions:
  A. Optimized/assert safety — the source must contain NO assert statements,
     so validation behaves identically under `python3 -O`.
  B. Verify tests — transient empty=False, wrong type=False, malformed=False,
     correct sealed=True, tampered=False.
  C. Canonical tests — UTC-equivalent datetime equality, NFC/NFD issuer claim
     equality, resource-scope / secondary-effect / equivalent-group order
     independence, primary_effect preserved as Enum, payload datetimes remain
     datetime, payload resource_scopes/secondary_effects as SetLikeTuple.
  D. Model type-invariant tests — every BLOCKER-2 type rejection scenario.

BLOCKER 1 (revision R2) additions:
  - verify_envelope_candidate_digest is a TOTAL predicate over object():
    object(), None, and int all return False without raising.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import unittest
from datetime import datetime, timedelta, timezone, tzinfo

from authorization_kernel.enums import ActionEffect, ResourceScopeType
from authorization_kernel.resource_scope import TypedResourceScope
from authorization_kernel.canonical_serialization import SetLikeTuple
import authorization_kernel.capability_grant_envelope as envelope_module
from authorization_kernel.capability_grant_envelope import (
    CapabilityGrantEnvelopeCandidate,
    compute_envelope_candidate_digest,
    envelope_candidate_payload,
    verify_envelope_candidate_digest,
)


UTC = timezone.utc
T_ISSUED = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
T_EXPIRES = datetime(2026, 6, 15, 13, 0, 0, tzinfo=UTC)

# Real 64-char lowercase hex digests (sha256 of b"" and b"0") for fixtures.
HEX_A = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
HEX_B = "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"
HEX_C = "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"

_REJECT = (AssertionError, ValueError, TypeError)

_MARKER_NAMES = (
    "NOT_REAL_EXECUTION_PERMISSION",
    "NOT_RUNTIME_ENFORCEABLE_TOKEN",
    "NOT_CAPABILITY_LEASE",
    "NOT_SIGNED_AUTHORITY",
    "NOT_AUTHORITY_PROOF",
    "NOT_REPLAY_PROTECTED",
    "NOT_PERSISTED",
    "NOT_AUTHORITATIVE_GRANT",
    "NOT_ISSUED_GRANT",
)


def _scope(cid: str = "file:/x") -> TypedResourceScope:
    return TypedResourceScope(scope_type=ResourceScopeType.FILE_PATH, canonical_id=cid)


def _envelope(**overrides) -> CapabilityGrantEnvelopeCandidate:
    base = dict(
        envelope_candidate_digest="",
        candidate_digest=HEX_A,
        evidence_digest=HEX_B,
        request_id="req-1",
        task_id="task-1",
        actor_id="actor-1",
        primary_effect=ActionEffect.WRITE,
        secondary_effects=frozenset(),
        resource_scopes=(_scope(),),
        equivalent_action_groups=frozenset(),
        requested_tool="editor",
        snapshot_id="snap-1",
        policy_version="v1",
        classification_attestation_hash=HEX_C,
        issued_at=T_ISSUED,
        not_before=T_ISSUED,
        expires_at=T_EXPIRES,
        issuer_claim_id="issuer-1",
        issuer_claim_version="iv1",
        authority_proof_type="NONE",
    )
    base.update(overrides)
    return CapabilityGrantEnvelopeCandidate(**base)


def _sealed(**overrides) -> CapabilityGrantEnvelopeCandidate:
    e = _envelope(**overrides)
    return dataclasses.replace(
        e, envelope_candidate_digest=compute_envelope_candidate_digest(e)
    )


def _bypass(base: CapabilityGrantEnvelopeCandidate, **overrides):
    """Build an instance bypassing __post_init__ (for verify-path tests).

    object.__new__ never runs validation, so a malformed / wrong-type
    envelope_candidate_digest can exist purely to exercise the verify guard.
    """
    obj = object.__new__(CapabilityGrantEnvelopeCandidate)
    for f in dataclasses.fields(base):
        object.__setattr__(obj, f.name, getattr(base, f.name))
    for k, v in overrides.items():
        object.__setattr__(obj, k, v)
    return obj


class _BadTZ(tzinfo):
    """A tzinfo that is present but returns None from utcoffset()."""

    def utcoffset(self, dt):
        return None

    def tzname(self, dt):
        return "BAD"

    def dst(self, dt):
        return None


# ============================================================
# Structure & boundary markers
# ============================================================

class StructureTests(unittest.TestCase):
    def test_valid_construction(self):
        self.assertIsInstance(_envelope(), CapabilityGrantEnvelopeCandidate)

    def test_is_frozen(self):
        e = _envelope()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            e.request_id = "mutated"  # type: ignore[misc]

    def test_twenty_required_instance_fields_no_defaults(self):
        fields = dataclasses.fields(CapabilityGrantEnvelopeCandidate)
        self.assertEqual(len(fields), 20)
        for f in fields:
            self.assertIs(f.default, dataclasses.MISSING, f"{f.name} must have no default")
            self.assertIs(
                f.default_factory,  # type: ignore[comparison-overlap]
                dataclasses.MISSING,
                f"{f.name} must have no default_factory",
            )

    def test_nine_boundary_markers_all_true(self):
        for name in _MARKER_NAMES:
            self.assertTrue(
                getattr(CapabilityGrantEnvelopeCandidate, name),
                f"{name} must be True",
            )

    def test_both_authority_proof_and_issued_grant_markers_present(self):
        self.assertTrue(CapabilityGrantEnvelopeCandidate.NOT_AUTHORITY_PROOF)
        self.assertTrue(CapabilityGrantEnvelopeCandidate.NOT_ISSUED_GRANT)
        self.assertTrue(CapabilityGrantEnvelopeCandidate.NOT_AUTHORITATIVE_GRANT)

    def test_markers_are_class_level_not_instance_fields(self):
        field_names = {f.name for f in dataclasses.fields(CapabilityGrantEnvelopeCandidate)}
        for name in _MARKER_NAMES:
            self.assertNotIn(name, field_names)


# ============================================================
# BLOCKER 8A — Optimized / assert-safety
# ============================================================

class OptimizedAssertSafetyTests(unittest.TestCase):
    def test_model_source_has_no_assert_statements(self):
        # Security validation must NOT depend on `assert` (stripped under -O).
        tree = ast.parse(inspect.getsource(envelope_module))
        asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
        self.assertEqual(asserts, [], "no assert statements allowed for validation")

    def test_validation_uses_explicit_raises(self):
        # A representative invariant still rejects even though no assert is used.
        with self.assertRaises((ValueError, TypeError)):
            _envelope(authority_proof_type="SIGNED")


# ============================================================
# Digest field validation
# ============================================================

class DigestFieldTests(unittest.TestCase):
    def test_empty_envelope_digest_allowed_transient(self):
        self.assertEqual(_envelope(envelope_candidate_digest="").envelope_candidate_digest, "")

    def test_short_envelope_digest_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(envelope_candidate_digest="a" * 63)

    def test_uppercase_envelope_digest_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(envelope_candidate_digest="A" * 64)

    def test_nonhex_envelope_digest_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(envelope_candidate_digest="z" * 64)

    def test_short_candidate_digest_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(candidate_digest="a" * 10)

    def test_uppercase_candidate_digest_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(candidate_digest=HEX_A.upper())

    def test_short_evidence_digest_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(evidence_digest="b" * 5)

    def test_uppercase_evidence_digest_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(evidence_digest=HEX_B.upper())

    def test_bad_attestation_hash_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(classification_attestation_hash="nope")

    def test_uppercase_attestation_hash_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(classification_attestation_hash=HEX_C.upper())


# ============================================================
# Identity-string validation
# ============================================================

class IdentityStringTests(unittest.TestCase):
    def test_empty_request_id_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(request_id="")

    def test_empty_task_id_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(task_id="")

    def test_empty_actor_id_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(actor_id="")

    def test_empty_snapshot_id_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(snapshot_id="")

    def test_empty_policy_version_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(policy_version="")

    def test_empty_issuer_claim_id_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(issuer_claim_id="")

    def test_empty_issuer_claim_version_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(issuer_claim_version="")

    def test_nonstr_request_id_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(request_id=123)


# ============================================================
# BLOCKER 8D — Model type-invariant rejection scenarios
# ============================================================

class TypeInvariantTests(unittest.TestCase):
    def test_requested_tool_nonstr_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(requested_tool=123)

    def test_requested_tool_empty_allowed(self):
        self.assertEqual(_envelope(requested_tool="").requested_tool, "")

    def test_primary_effect_nonenum_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(primary_effect="write")

    def test_secondary_effects_nonfrozenset_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(secondary_effects=[ActionEffect.READ])

    def test_secondary_effects_bad_item_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(secondary_effects=frozenset({"read"}))

    def test_resource_scopes_nontuple_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(resource_scopes=[_scope()])

    def test_resource_scopes_empty_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(resource_scopes=())

    def test_resource_scopes_bad_item_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(resource_scopes=("file:/x",))

    def test_resource_scopes_duplicate_identity_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(resource_scopes=(_scope("file:/x"), _scope("file:/x")))

    def test_equivalent_groups_nonfrozenset_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(equivalent_action_groups=["g1"])

    def test_equivalent_groups_bad_item_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(equivalent_action_groups=frozenset({1}))

    def test_equivalent_groups_empty_string_item_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(equivalent_action_groups=frozenset({""}))


# ============================================================
# Temporal validation
# ============================================================

class TemporalTests(unittest.TestCase):
    def test_naive_issued_at_rejected(self):
        naive = datetime(2026, 6, 15, 12, 0, 0)
        with self.assertRaises(_REJECT):
            _envelope(issued_at=naive, not_before=naive)

    def test_naive_not_before_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(not_before=datetime(2026, 6, 15, 12, 0, 0))

    def test_naive_expires_at_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(expires_at=datetime(2026, 6, 15, 13, 0, 0))

    def test_tzinfo_present_but_utcoffset_none_rejected(self):
        bad = datetime(2026, 6, 15, 12, 0, 0, tzinfo=_BadTZ())
        with self.assertRaises(_REJECT):
            _envelope(issued_at=bad, not_before=bad)

    def test_not_before_must_equal_issued_at(self):
        with self.assertRaises(_REJECT):
            _envelope(not_before=T_ISSUED + timedelta(seconds=1))

    def test_expires_before_not_before_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(expires_at=T_ISSUED - timedelta(seconds=1))

    def test_expires_equal_not_before_ok(self):
        e = _envelope(expires_at=T_ISSUED)
        self.assertEqual(e.expires_at, e.not_before)


# ============================================================
# Effects & authority_proof_type
# ============================================================

class EffectAndProofTests(unittest.TestCase):
    def test_primary_in_secondary_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(
                primary_effect=ActionEffect.WRITE,
                secondary_effects=frozenset({ActionEffect.WRITE}),
            )

    def test_disjoint_secondary_ok(self):
        e = _envelope(
            primary_effect=ActionEffect.WRITE,
            secondary_effects=frozenset({ActionEffect.READ}),
        )
        self.assertIn(ActionEffect.READ, e.secondary_effects)

    def test_authority_proof_type_none_ok(self):
        self.assertEqual(_envelope(authority_proof_type="NONE").authority_proof_type, "NONE")

    def test_authority_proof_type_signed_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(authority_proof_type="SIGNED")

    def test_authority_proof_type_empty_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(authority_proof_type="")

    def test_authority_proof_type_lowercase_none_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(authority_proof_type="none")

    def test_authority_proof_type_nonstr_rejected(self):
        with self.assertRaises(_REJECT):
            _envelope(authority_proof_type=None)


# ============================================================
# Payload & digest
# ============================================================

class PayloadDigestTests(unittest.TestCase):
    def test_payload_excludes_envelope_candidate_digest(self):
        payload = envelope_candidate_payload(_sealed())
        self.assertNotIn("envelope_candidate_digest", payload)

    def test_payload_contains_expected_keys(self):
        payload = envelope_candidate_payload(_envelope())
        for key in (
            "candidate_digest",
            "evidence_digest",
            "request_id",
            "task_id",
            "actor_id",
            "primary_effect",
            "secondary_effects",
            "resource_scopes",
            "equivalent_action_groups",
            "requested_tool",
            "snapshot_id",
            "policy_version",
            "classification_attestation_hash",
            "issued_at",
            "not_before",
            "expires_at",
            "issuer_claim_id",
            "issuer_claim_version",
            "authority_proof_type",
        ):
            self.assertIn(key, payload)

    def test_payload_returns_plain_dict_not_string(self):
        # BLOCKER 3: payload is a plain dict, not a pre-serialized string.
        p = envelope_candidate_payload(_envelope())
        self.assertIsInstance(p, dict)

    def test_payload_primary_effect_preserved_as_enum(self):
        # BLOCKER 3: enum kept as Enum (NOT .value); AK-1 serializer extracts it.
        p = envelope_candidate_payload(_envelope())
        self.assertIs(p["primary_effect"], ActionEffect.WRITE)
        self.assertIsInstance(p["primary_effect"], ActionEffect)

    def test_payload_datetimes_remain_datetime(self):
        # BLOCKER 3: datetimes kept aware (NOT isoformat()).
        p = envelope_candidate_payload(_envelope())
        self.assertIsInstance(p["issued_at"], datetime)
        self.assertIsInstance(p["not_before"], datetime)
        self.assertIsInstance(p["expires_at"], datetime)

    def test_payload_resource_scopes_is_setliketuple(self):
        p = envelope_candidate_payload(_envelope())
        self.assertIsInstance(p["resource_scopes"], SetLikeTuple)

    def test_payload_secondary_effects_is_setliketuple(self):
        p = envelope_candidate_payload(_envelope())
        self.assertIsInstance(p["secondary_effects"], SetLikeTuple)

    def test_payload_equivalent_groups_is_setliketuple(self):
        p = envelope_candidate_payload(_envelope())
        self.assertIsInstance(p["equivalent_action_groups"], SetLikeTuple)

    def test_payload_authority_proof_type_is_none_string(self):
        self.assertEqual(envelope_candidate_payload(_envelope())["authority_proof_type"], "NONE")

    def test_digest_is_64_lowercase_hex(self):
        d = compute_envelope_candidate_digest(_envelope())
        self.assertEqual(len(d), 64)
        self.assertEqual(d, d.lower())
        int(d, 16)

    def test_digest_is_deterministic(self):
        self.assertEqual(
            compute_envelope_candidate_digest(_envelope()),
            compute_envelope_candidate_digest(_envelope()),
        )

    def test_digest_sensitive_to_actor_id(self):
        self.assertNotEqual(
            compute_envelope_candidate_digest(_envelope(actor_id="actor-1")),
            compute_envelope_candidate_digest(_envelope(actor_id="actor-2")),
        )

    def test_digest_sensitive_to_issuer_claim(self):
        self.assertNotEqual(
            compute_envelope_candidate_digest(_envelope(issuer_claim_id="issuer-1")),
            compute_envelope_candidate_digest(_envelope(issuer_claim_id="issuer-9")),
        )

    def test_digest_sensitive_to_candidate_digest(self):
        self.assertNotEqual(
            compute_envelope_candidate_digest(_envelope(candidate_digest=HEX_A)),
            compute_envelope_candidate_digest(_envelope(candidate_digest=HEX_C)),
        )


# ============================================================
# BLOCKER 8B / BLOCKER 1 (R2) — verify_envelope_candidate_digest
# ============================================================

class VerifyTests(unittest.TestCase):
    def test_verify_true_for_correct_sealed(self):
        self.assertTrue(verify_envelope_candidate_digest(_sealed()))

    def test_verify_false_for_transient_empty(self):
        # BLOCKER 4: an empty/transient digest is NOT a verified digest.
        self.assertFalse(verify_envelope_candidate_digest(_envelope(envelope_candidate_digest="")))

    def test_verify_false_for_wrong_sealed_digest(self):
        e = dataclasses.replace(_envelope(), envelope_candidate_digest=HEX_A)
        self.assertFalse(verify_envelope_candidate_digest(e))

    def test_verify_false_for_malformed_digest(self):
        # Non-hex digest can only exist via __post_init__ bypass.
        obj = _bypass(_envelope(), envelope_candidate_digest="z" * 64)
        self.assertFalse(verify_envelope_candidate_digest(obj))

    def test_verify_false_for_wrong_type_digest(self):
        obj = _bypass(_envelope(), envelope_candidate_digest=123)
        self.assertFalse(verify_envelope_candidate_digest(obj))

    def test_verify_false_for_tampered(self):
        # Correctly sealed, then a field is mutated while the digest is kept.
        sealed = _sealed()
        obj = _bypass(sealed, actor_id="actor-EVIL")
        self.assertFalse(verify_envelope_candidate_digest(obj))

    # ---- BLOCKER 1 (R2): total over object(), None, int — never raises ----
    def test_verify_false_for_plain_object(self):
        self.assertFalse(verify_envelope_candidate_digest(object()))

    def test_verify_false_for_none(self):
        self.assertFalse(verify_envelope_candidate_digest(None))

    def test_verify_false_for_int(self):
        self.assertFalse(verify_envelope_candidate_digest(123))

    def test_verify_false_for_str(self):
        self.assertFalse(verify_envelope_candidate_digest("not-an-envelope"))

    def test_verify_returns_bool_for_every_input(self):
        for value in (object(), None, 123, "x", _sealed(), _envelope()):
            self.assertIsInstance(verify_envelope_candidate_digest(value), bool)


# ============================================================
# BLOCKER 8C — Canonical equivalence / order independence
# ============================================================

class CanonicalEquivalenceTests(unittest.TestCase):
    def test_utc_equivalent_datetime_same_digest(self):
        # 12:00+00:00 and 05:00-07:00 are the same instant -> same digest.
        utc_dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
        off_dt = datetime(2026, 6, 15, 5, 0, 0, tzinfo=timezone(timedelta(hours=-7)))
        exp = datetime(2026, 6, 15, 13, 0, 0, tzinfo=UTC)
        a = _envelope(issued_at=utc_dt, not_before=utc_dt, expires_at=exp)
        b = _envelope(issued_at=off_dt, not_before=off_dt, expires_at=exp)
        self.assertEqual(
            compute_envelope_candidate_digest(a),
            compute_envelope_candidate_digest(b),
        )

    def test_nfc_nfd_issuer_claim_id_equal_digest(self):
        # "é" composed (NFC) vs "e" + combining acute (NFD) -> NFC-normalized.
        nfc = "issuer-\u00e9"
        nfd = "issuer-e\u0301"
        self.assertNotEqual(nfc, nfd)  # distinct code points pre-normalization
        a = _envelope(issuer_claim_id=nfc)
        b = _envelope(issuer_claim_id=nfd)
        self.assertEqual(
            compute_envelope_candidate_digest(a),
            compute_envelope_candidate_digest(b),
        )

    def test_resource_scopes_order_independent(self):
        a = _envelope(resource_scopes=(_scope("file:/a"), _scope("file:/b")))
        b = _envelope(resource_scopes=(_scope("file:/b"), _scope("file:/a")))
        self.assertEqual(
            compute_envelope_candidate_digest(a),
            compute_envelope_candidate_digest(b),
        )

    def test_secondary_effects_order_independent(self):
        a = _envelope(
            primary_effect=ActionEffect.WRITE,
            secondary_effects=frozenset({ActionEffect.READ, ActionEffect.EXECUTE}),
        )
        b = _envelope(
            primary_effect=ActionEffect.WRITE,
            secondary_effects=frozenset({ActionEffect.EXECUTE, ActionEffect.READ}),
        )
        self.assertEqual(
            compute_envelope_candidate_digest(a),
            compute_envelope_candidate_digest(b),
        )

    def test_equivalent_groups_order_independent(self):
        a = _envelope(equivalent_action_groups=frozenset({"g1", "g2"}))
        b = _envelope(equivalent_action_groups=frozenset({"g2", "g1"}))
        self.assertEqual(
            compute_envelope_candidate_digest(a),
            compute_envelope_candidate_digest(b),
        )


if __name__ == "__main__":
    unittest.main()
