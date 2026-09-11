"""
GOAA Authorization Kernel AK-5A — CapabilityGrantCandidate Schema + Digest Tests
================================================================================
Framework: unittest (standard library). No pytest, no third-party deps.
All tests are pure — no file I/O, no network, no subprocess, no clock reads.

Covers: frozen dataclass, absence of mutable defaults, empty-ID rejection,
illegal / uppercase digest rejection, naive datetimes, tzinfo-present-but-
utcoffset-None, expires_at never None, not_before == issued_at, requested_tool
recorded and digest-bearing, absence of grant_id/status/runtime fields,
NFC/NFD digest equivalence, UTC-equivalent-time digest equivalence, set-like
order stability, per-field digest sensitivity, and the candidate_digest
exclusion from its own payload.
"""

from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timedelta, timezone, tzinfo

from authorization_kernel.enums import ActionEffect, ResourceScopeType
from authorization_kernel.resource_scope import TypedResourceScope
from authorization_kernel.canonical_serialization import SetLikeTuple
from authorization_kernel.capability_models import (
    CapabilityGrantCandidate,
    candidate_payload,
    compute_candidate_digest,
    verify_candidate_digest,
)


UTC = timezone.utc
T_ISSUED = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
T_EXPIRES = datetime(2026, 6, 15, 13, 0, 0, tzinfo=UTC)

# A real 64-char lowercase hex digest (sha256 of b"") for fixture use.
HEX_A = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
HEX_B = "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"


def _scope(cid: str = "file:/x") -> TypedResourceScope:
    return TypedResourceScope(scope_type=ResourceScopeType.FILE_PATH, canonical_id=cid)


def _candidate(**overrides) -> CapabilityGrantCandidate:
    """Build a valid CapabilityGrantCandidate with optional field overrides.

    candidate_digest defaults to "" (the transient pre-digest state); callers
    that need a sealed candidate compute and replace it.
    """
    base = dict(
        candidate_digest="",
        evidence_digest=HEX_A,
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
        classification_attestation_hash=HEX_B,
        issued_at=T_ISSUED,
        not_before=T_ISSUED,
        expires_at=T_EXPIRES,
    )
    base.update(overrides)
    return CapabilityGrantCandidate(**base)


def _sealed(**overrides) -> CapabilityGrantCandidate:
    """A candidate with its candidate_digest computed and set."""
    c = _candidate(**overrides)
    return dataclasses.replace(c, candidate_digest=compute_candidate_digest(c))


class _BadTZ(tzinfo):
    """A tzinfo that is present but returns None from utcoffset()."""

    def utcoffset(self, dt):  # noqa: D401
        return None

    def tzname(self, dt):
        return "BAD"

    def dst(self, dt):
        return None


# ============================================================
# Structure: frozen + no mutable defaults + boundary docstring
# ============================================================

class StructureTests(unittest.TestCase):
    def test_is_frozen(self):
        c = _candidate()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            c.request_id = "mutated"  # type: ignore[misc]

    def test_no_field_has_a_default_or_mutable_default(self):
        # Every field is required: no default and no default_factory. This
        # rules out a shared mutable default leaking across instances.
        for f in dataclasses.fields(CapabilityGrantCandidate):
            self.assertIs(
                f.default, dataclasses.MISSING, f"{f.name} must have no default"
            )
            self.assertIs(
                f.default_factory,  # type: ignore[comparison-overlap]
                dataclasses.MISSING,
                f"{f.name} must have no default_factory",
            )

    def test_docstring_declares_non_authority_markers(self):
        text = (CapabilityGrantCandidate.__doc__ or "") + (
            __import__("authorization_kernel.capability_models", fromlist=["x"]).__doc__
            or ""
        )
        for marker in (
            "NOT_REAL_EXECUTION_PERMISSION",
            "NOT_RUNTIME_ENFORCEABLE_TOKEN",
            "NOT_CAPABILITY_LEASE",
            "NOT_SIGNED_AUTHORITY",
        ):
            self.assertIn(marker, text)

    def test_happy_candidate_constructs(self):
        c = _candidate()
        self.assertEqual(c.request_id, "req-1")
        self.assertEqual(c.expires_at, T_EXPIRES)


# ============================================================
# Forbidden fields never exist
# ============================================================

class ForbiddenFieldTests(unittest.TestCase):
    def test_no_lifecycle_or_runtime_fields(self):
        c = _candidate()
        for forbidden in (
            "grant_id",
            "status",
            "real_execution_permission",
            "runtime_enforced",
            "consumed_at",
            "revoked_at",
        ):
            self.assertFalse(
                hasattr(c, forbidden), f"candidate must not have {forbidden}"
            )

    def test_field_set_is_exactly_the_declared_schema(self):
        names = {f.name for f in dataclasses.fields(CapabilityGrantCandidate)}
        self.assertEqual(
            names,
            {
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
            },
        )


# ============================================================
# Identity-string validation
# ============================================================

class IdentityStringTests(unittest.TestCase):
    def test_empty_request_id_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(request_id="")

    def test_whitespace_request_id_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(request_id="   ")

    def test_empty_task_id_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(task_id="")

    def test_empty_actor_id_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(actor_id="")

    def test_empty_snapshot_id_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(snapshot_id="")

    def test_empty_policy_version_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(policy_version="")

    def test_non_str_request_id_rejected(self):
        with self.assertRaises(TypeError):
            _candidate(request_id=123)

    def test_requested_tool_may_be_empty(self):
        c = _candidate(requested_tool="")
        self.assertEqual(c.requested_tool, "")

    def test_requested_tool_non_str_rejected(self):
        with self.assertRaises(TypeError):
            _candidate(requested_tool=None)


# ============================================================
# Digest-format validation
# ============================================================

class DigestFormatTests(unittest.TestCase):
    def test_evidence_digest_too_short_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(evidence_digest="abc")

    def test_evidence_digest_uppercase_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(evidence_digest=HEX_A.upper())

    def test_evidence_digest_non_hex_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(evidence_digest="z" * 64)

    def test_evidence_digest_empty_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(evidence_digest="")

    def test_classification_attestation_hash_uppercase_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(classification_attestation_hash=HEX_B.upper())

    def test_classification_attestation_hash_empty_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(classification_attestation_hash="")

    def test_candidate_digest_empty_allowed_as_pre_digest_state(self):
        c = _candidate(candidate_digest="")
        self.assertEqual(c.candidate_digest, "")

    def test_candidate_digest_uppercase_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(candidate_digest=HEX_A.upper())

    def test_candidate_digest_bad_length_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(candidate_digest="deadbeef")


# ============================================================
# Effect / scope / group validation
# ============================================================

class EffectScopeGroupTests(unittest.TestCase):
    def test_primary_effect_must_be_action_effect(self):
        with self.assertRaises(TypeError):
            _candidate(primary_effect="write")

    def test_secondary_effects_must_be_frozenset(self):
        with self.assertRaises(TypeError):
            _candidate(secondary_effects=[ActionEffect.READ])

    def test_secondary_effects_elements_must_be_action_effect(self):
        with self.assertRaises(TypeError):
            _candidate(secondary_effects=frozenset({"read"}))

    def test_primary_in_secondary_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(
                primary_effect=ActionEffect.WRITE,
                secondary_effects=frozenset({ActionEffect.WRITE}),
            )

    def test_resource_scopes_empty_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(resource_scopes=())

    def test_resource_scopes_non_tuple_rejected(self):
        with self.assertRaises(TypeError):
            _candidate(resource_scopes=[_scope()])

    def test_resource_scopes_element_type_rejected(self):
        with self.assertRaises(TypeError):
            _candidate(resource_scopes=("file:/x",))

    def test_resource_scopes_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(resource_scopes=(_scope("file:/x"), _scope("file:/x")))

    def test_equivalent_groups_non_frozenset_rejected(self):
        with self.assertRaises(TypeError):
            _candidate(equivalent_action_groups=["g1"])

    def test_equivalent_groups_empty_string_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(equivalent_action_groups=frozenset({""}))

    def test_equivalent_groups_non_str_rejected(self):
        with self.assertRaises(TypeError):
            _candidate(equivalent_action_groups=frozenset({1}))


# ============================================================
# Temporal-window validation
# ============================================================

class TemporalTests(unittest.TestCase):
    def test_naive_issued_at_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(issued_at=datetime(2026, 6, 15, 12, 0, 0))

    def test_naive_not_before_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(not_before=datetime(2026, 6, 15, 12, 0, 0))

    def test_naive_expires_at_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(expires_at=datetime(2026, 6, 15, 13, 0, 0))

    def test_tzinfo_present_but_utcoffset_none_rejected(self):
        bad = datetime(2026, 6, 15, 12, 0, 0, tzinfo=_BadTZ())
        with self.assertRaises(ValueError):
            _candidate(issued_at=bad, not_before=bad)

    def test_expires_at_none_rejected(self):
        with self.assertRaises(TypeError):
            _candidate(expires_at=None)

    def test_not_before_equals_issued_at_accepted(self):
        # not_before MUST equal issued_at exactly; equality is the only accept.
        c = _candidate(issued_at=T_ISSUED, not_before=T_ISSUED)
        self.assertEqual(c.not_before, c.issued_at)

    def test_not_before_before_issued_at_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(
                issued_at=T_ISSUED,
                not_before=T_ISSUED - timedelta(hours=1),
            )

    def test_not_before_after_issued_at_rejected(self):
        # Strict equality: a not_before LATER than issued_at is also rejected.
        with self.assertRaises(ValueError):
            _candidate(
                issued_at=T_ISSUED,
                not_before=T_ISSUED + timedelta(hours=1),
            )

    def test_expires_at_before_not_before_rejected(self):
        with self.assertRaises(ValueError):
            _candidate(expires_at=T_ISSUED - timedelta(hours=1))

    def test_expires_at_equal_not_before_accepted(self):
        c = _candidate(expires_at=T_ISSUED)
        self.assertEqual(c.expires_at, c.not_before)


# ============================================================
# candidate_payload / digest behaviour
# ============================================================

class DigestBehaviourTests(unittest.TestCase):
    def test_payload_excludes_candidate_digest(self):
        self.assertNotIn("candidate_digest", candidate_payload(_candidate()))

    def test_digest_is_64_lowercase_hex(self):
        d = compute_candidate_digest(_candidate())
        self.assertEqual(len(d), 64)
        self.assertEqual(d, d.lower())
        int(d, 16)

    def test_candidate_digest_does_not_affect_computed_digest(self):
        c1 = _candidate(candidate_digest="")
        c2 = dataclasses.replace(c1, candidate_digest=HEX_A)
        self.assertEqual(compute_candidate_digest(c1), compute_candidate_digest(c2))

    def test_verify_true_for_sealed(self):
        self.assertTrue(verify_candidate_digest(_sealed()))

    def test_verify_false_for_unsealed(self):
        self.assertFalse(verify_candidate_digest(_candidate(candidate_digest="")))

    def test_verify_false_for_wrong_digest(self):
        c = dataclasses.replace(_candidate(), candidate_digest=HEX_A)
        self.assertFalse(verify_candidate_digest(c))

    def test_requested_tool_enters_digest(self):
        a = compute_candidate_digest(_candidate(requested_tool="editor"))
        b = compute_candidate_digest(_candidate(requested_tool="shell"))
        self.assertNotEqual(a, b)

    def test_nfc_nfd_canonical_id_digest_equal(self):
        # U+00E9 (composed, NFC) vs "e"+U+0301 (combining acute, NFD).
        # The two strings differ code-point-for-code-point but
        # canonicalize to the same NFC form, so their digests must match.
        import unicodedata

        nfc_str = "file:/" + unicodedata.normalize("NFC", "\u00e9")
        nfd_str = "file:/" + unicodedata.normalize("NFD", "\u00e9")
        self.assertNotEqual(nfc_str, nfd_str)
        nfc = compute_candidate_digest(_candidate(resource_scopes=(_scope(nfc_str),)))
        nfd = compute_candidate_digest(_candidate(resource_scopes=(_scope(nfd_str),)))
        self.assertEqual(nfc, nfd)

    def test_utc_equivalent_times_digest_equal(self):
        # Same instant, expressed in UTC vs a +01:00 zone.
        plus_one = timezone(timedelta(hours=1))
        utc_time = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
        other = datetime(2026, 6, 15, 13, 0, 0, tzinfo=plus_one)
        a = compute_candidate_digest(_candidate(issued_at=utc_time, not_before=utc_time))
        b = compute_candidate_digest(_candidate(issued_at=other, not_before=other))
        self.assertEqual(a, b)

    def test_set_like_resource_scope_order_stable(self):
        s1 = (_scope("file:/a"), _scope("file:/b"))
        s2 = (_scope("file:/b"), _scope("file:/a"))
        self.assertEqual(
            compute_candidate_digest(_candidate(resource_scopes=s1)),
            compute_candidate_digest(_candidate(resource_scopes=s2)),
        )

    def test_set_like_secondary_effects_order_stable(self):
        # frozenset is inherently unordered; confirm digest is independent of
        # construction order.
        a = compute_candidate_digest(
            _candidate(secondary_effects=frozenset({ActionEffect.READ, ActionEffect.CREATE}))
        )
        b = compute_candidate_digest(
            _candidate(secondary_effects=frozenset({ActionEffect.CREATE, ActionEffect.READ}))
        )
        self.assertEqual(a, b)

    def test_set_like_groups_order_stable(self):
        a = compute_candidate_digest(
            _candidate(equivalent_action_groups=frozenset({"g1", "g2"}))
        )
        b = compute_candidate_digest(
            _candidate(equivalent_action_groups=frozenset({"g2", "g1"}))
        )
        self.assertEqual(a, b)


# ============================================================
# Per-field digest sensitivity
# ============================================================

class DigestSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.base_digest = compute_candidate_digest(_candidate())

    def _assert_changes(self, **override):
        self.assertNotEqual(self.base_digest, compute_candidate_digest(_candidate(**override)))

    def test_evidence_digest_change(self):
        self._assert_changes(evidence_digest=HEX_B)

    def test_request_id_change(self):
        self._assert_changes(request_id="req-2")

    def test_task_id_change(self):
        self._assert_changes(task_id="task-2")

    def test_actor_id_change(self):
        self._assert_changes(actor_id="actor-2")

    def test_primary_effect_change(self):
        self._assert_changes(primary_effect=ActionEffect.READ)

    def test_secondary_effects_change(self):
        self._assert_changes(secondary_effects=frozenset({ActionEffect.READ}))

    def test_resource_scopes_change(self):
        self._assert_changes(resource_scopes=(_scope("file:/y"),))

    def test_equivalent_groups_change(self):
        self._assert_changes(equivalent_action_groups=frozenset({"g1"}))

    def test_requested_tool_change(self):
        self._assert_changes(requested_tool="shell")

    def test_snapshot_id_change(self):
        self._assert_changes(snapshot_id="snap-2")

    def test_policy_version_change(self):
        self._assert_changes(policy_version="v2")

    def test_classification_attestation_hash_change(self):
        self._assert_changes(classification_attestation_hash=HEX_A)

    def test_issued_at_change(self):
        self._assert_changes(
            issued_at=T_ISSUED - timedelta(hours=2),
            not_before=T_ISSUED - timedelta(hours=2),
        )

    def test_not_before_change(self):
        # not_before is digest-bearing, but the schema now requires it to equal
        # issued_at, so it can only move in lockstep with issued_at. Shifting
        # the (issued_at, not_before) pair to a new equal instant must change
        # the digest. (A not_before that diverges from issued_at is rejected at
        # construction — see TemporalTests, not exercised here.)
        new_t = T_ISSUED + timedelta(minutes=5)
        self._assert_changes(issued_at=new_t, not_before=new_t)

    def test_expires_at_change(self):
        self._assert_changes(expires_at=T_EXPIRES + timedelta(hours=1))


# ============================================================
# Malformed (post_init-bypassing) object handling
# ============================================================

class MalformedObjectTests(unittest.TestCase):
    def test_object_new_bypasses_post_init_but_digest_fails_loudly(self):
        # An object built via object.__new__ skips __post_init__ and has no
        # fields. candidate_payload must raise rather than silently hash junk.
        malformed = object.__new__(CapabilityGrantCandidate)
        with self.assertRaises(Exception):
            candidate_payload(malformed)

    def test_payload_is_setliketuple_for_set_fields(self):
        payload = candidate_payload(_candidate())
        self.assertIsInstance(payload["secondary_effects"], SetLikeTuple)
        self.assertIsInstance(payload["resource_scopes"], SetLikeTuple)
        self.assertIsInstance(payload["equivalent_action_groups"], SetLikeTuple)


if __name__ == "__main__":
    unittest.main()
