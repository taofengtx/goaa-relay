"""Tests for AK-5B2B ``capability_grant_lifecycle``.

Covers:
- ``GrantLifecycleState`` enum values
- ``RevocationEvent`` construction
- ``derive_revocation_event_id`` determinism and domain separation
- ``build_revocation_event`` (success, failure edge cases)
- ``evaluate_grant_lifecycle`` (PENDING, ACTIVE, EXPIRED, REVOKED, edge cases)
- ``check_revocation_conflict`` (idempotent, conflict)
- Immutability guarantees
- No implicit system clock
- Timezone constraints
- Unicode NFC stability
Note: B2A enforces ``not_before == issued_at``, so PENDING state can only
be tested by evaluating *before* ``issued_at``.
"""

import copy
import dataclasses
import hashlib
import unittest
from datetime import datetime, timezone, timedelta

from authorization_kernel.enums import ActionEffect, ResourceScopeType
from authorization_kernel.resource_scope import TypedResourceScope
from authorization_kernel.canonical_serialization import sha256_hex
from authorization_kernel.capability_grant_identity import (
    CapabilityGrantIdentityCandidate,
)
from authorization_kernel.capability_grant_lifecycle import (
    REVOCATION_EVENT_ID_DOMAIN,
    GrantLifecycleState,
    RevocationEvent,
    RevocationConflictPolicy,
    LifecycleEvaluationResult,
    derive_revocation_event_id,
    build_revocation_event,
    evaluate_grant_lifecycle,
    check_revocation_conflict,
)

_UTC = timezone.utc


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=_UTC)


def _gid(label: str) -> str:
    """Deterministic 64-char hex string for testing."""
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _make_identity(
    *,
    grant_id: str | None = None,
    issued_at: datetime | None = None,
    not_before: datetime | None = None,
    expires_at: datetime | None = None,
    now: datetime | None = None,
) -> CapabilityGrantIdentityCandidate:
    """Build a minimal B2A-valid grant identity for testing."""
    if now is None:
        now = _dt("2026-06-20T12:00:00")
    if issued_at is None:
        issued_at = now
    if not_before is None:
        not_before = issued_at  # B2A enforces not_before == issued_at
    if expires_at is None:
        expires_at = now + timedelta(hours=1)
    if grant_id is None:
        grant_id = _gid("default")
    return CapabilityGrantIdentityCandidate(
        grant_identity_digest="",
        grant_id=grant_id,
        envelope_candidate_digest="a" * 64,
        candidate_digest="b" * 64,
        evidence_digest="c" * 64,
        request_id="req",
        task_id="task",
        actor_id="actor",
        primary_effect=ActionEffect.READ,
        secondary_effects=frozenset(),
        resource_scopes=(
            TypedResourceScope(
                scope_type=ResourceScopeType.FILE_PATH,
                canonical_id="/tmp/x",
            ),
        ),
        equivalent_action_groups=frozenset(),
        requested_tool="tool",
        snapshot_id="snap",
        policy_version="v1",
        classification_attestation_hash="d" * 64,
        issued_at=issued_at,
        not_before=not_before,
        expires_at=expires_at,
        issuer_claim_id="iss",
        issuer_claim_version="v1",
        authority_proof_type="NONE",
    )


# ====== GrantLifecycleState enum ==========================================


class TestGrantLifecycleStateEnum(unittest.TestCase):
    """GrantLifecycleState has exactly four values."""

    def test_enum_values(self):
        self.assertCountEqual(
            [s.value for s in GrantLifecycleState],
            ["PENDING", "ACTIVE", "EXPIRED", "REVOKED"],
        )

    def test_enum_members(self):
        self.assertIs(GrantLifecycleState.PENDING, GrantLifecycleState("PENDING"))
        self.assertIs(GrantLifecycleState.ACTIVE, GrantLifecycleState("ACTIVE"))
        self.assertIs(GrantLifecycleState.EXPIRED, GrantLifecycleState("EXPIRED"))
        self.assertIs(GrantLifecycleState.REVOKED, GrantLifecycleState("REVOKED"))


# ====== build_revocation_event ============================================


class TestBuildRevocationEvent(unittest.TestCase):
    """build_revocation_event validation."""

    def test_success_with_all_fields(self):
        result = build_revocation_event(
            grant_id=_gid("g-001"),
            revoked_by_actor_id="actor-X",
            revocation_reason_code="POLICY_VIOLATION",
            revocation_note_digest="abc123",
            revoked_at=_dt("2026-06-20T13:00:00"),
        )
        self.assertTrue(result.ok)
        ev = result.revocation_event
        self.assertEqual(ev.grant_id, _gid("g-001"))
        self.assertEqual(ev.revoked_by_actor_id, "actor-X")
        self.assertEqual(ev.revocation_reason_code, "POLICY_VIOLATION")
        self.assertEqual(ev.revocation_note_digest, "abc123")
        self.assertEqual(ev.revoked_at, _dt("2026-06-20T13:00:00"))
        self.assertIsInstance(ev.event_id, str)
        self.assertEqual(len(ev.event_id), 64)

    def test_success_minimal_fields(self):
        result = build_revocation_event(
            grant_id=_gid("g-001"),
            revoked_by_actor_id="actor-X",
            revocation_reason_code="MANUAL_REVOKE",
            revoked_at=_dt("2026-06-20T13:00:00"),
        )
        self.assertTrue(result.ok)
        ev = result.revocation_event
        self.assertEqual(ev.revocation_note_digest, "")
        self.assertEqual(ev.revoked_at, _dt("2026-06-20T13:00:00"))

    def test_fail_empty_grant_id(self):
        for bad in ["", "  ", "\t"]:
            with self.subTest(bad=repr(bad)):
                r = build_revocation_event(grant_id=bad, revoked_by_actor_id="X", revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00"))
                self.assertFalse(r.ok)
                self.assertIsNone(r.revocation_event)

    def test_fail_empty_revoked_by(self):
        for bad in ["", "  "]:
            with self.subTest(bad=repr(bad)):
                r = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id=bad, revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00"))
                self.assertFalse(r.ok)

    def test_fail_empty_reason_code(self):
        for bad in ["", "  "]:
            with self.subTest(bad=repr(bad)):
                r = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code=bad, revoked_at=_dt("2026-06-20T13:00:00"))
                self.assertFalse(r.ok)

    def test_fail_non_string_note_digest(self):
        r = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revocation_note_digest=123, revoked_at=_dt("2026-06-20T13:00:00"))
        self.assertFalse(r.ok)

    def test_fail_naive_revoked_at(self):
        r = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revoked_at=datetime(2026, 6, 20, 13, 0, 0))
        self.assertFalse(r.ok)


# ====== derive_revocation_event_id ========================================


class TestDeriveRevocationEventId(unittest.TestCase):

    def test_deterministic(self):
        args = dict(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revocation_note_digest="", revoked_at=_dt("2026-06-20T13:00:00"))
        self.assertEqual(derive_revocation_event_id(**args), derive_revocation_event_id(**args))

    def test_changing_input_changes_id(self):
        base = dict(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revocation_note_digest="", revoked_at=_dt("2026-06-20T13:00:00"))
        base_id = derive_revocation_event_id(**base)
        for key, val in [("grant_id", _gid("g2")), ("revoked_by_actor_id", "Y"), ("revocation_reason_code", "O"), ("revocation_note_digest", "n")]:
            v = dict(base, **{key: val})
            self.assertNotEqual(derive_revocation_event_id(**v), base_id)

    def test_domain_separated(self):
        args = dict(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revocation_note_digest="", revoked_at=_dt("2026-06-20T13:00:00"))
        eid = derive_revocation_event_id(**args)
        alt = sha256_hex({"domain": "ALTERNATE_DOMAIN", **{k: v.isoformat() if isinstance(v, datetime) else v for k, v in args.items()}})
        self.assertNotEqual(eid, alt)

    def test_event_id_not_grant_id(self):
        ev = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        self.assertNotEqual(ev.event_id, ev.grant_id)

    def test_hex_length(self):
        eid = derive_revocation_event_id(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revocation_note_digest="", revoked_at=_dt("2026-06-20T13:00:00"))
        self.assertEqual(len(eid), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in eid))

    def test_unicode_nfc_stability(self):
        import unicodedata
        nfc = unicodedata.normalize("NFC", "caf\u00e9")
        nfd = unicodedata.normalize("NFD", "caf\u00e9")
        args = dict(grant_id=_gid("g"), revoked_by_actor_id=nfc, revocation_reason_code=nfc, revocation_note_digest="", revoked_at=_dt("2026-06-20T13:00:00"))
        args_nfd = dict(args, revoked_by_actor_id=nfd, revocation_reason_code=nfd)
        self.assertEqual(derive_revocation_event_id(**args), derive_revocation_event_id(**args_nfd))


# ====== RevocationEvent determinism & immutability ========================


class TestBuildRevocationEventDeterminism(unittest.TestCase):
    def test_deterministic_build(self):
        kwargs = dict(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="P", revocation_note_digest="n", revoked_at=_dt("2026-06-20T13:00:00"))
        r1 = build_revocation_event(**kwargs)
        r2 = build_revocation_event(**kwargs)
        self.assertTrue(r1.ok)
        self.assertTrue(r2.ok)
        self.assertEqual(r1.revocation_event, r2.revocation_event)
        self.assertEqual(r1.revocation_event.event_id, r2.revocation_event.event_id)


class TestRevocationEventImmutability(unittest.TestCase):
    def test_cannot_mutate(self):
        ev = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        with self.assertRaises(dataclasses.FrozenInstanceError):
            ev.grant_id = "changed"  # type: ignore[misc]

    def test_deep_copy_preserves(self):
        ev = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        self.assertEqual(ev, copy.deepcopy(ev))


# ====== evaluate_grant_lifecycle — state computation ======================


class TestEvaluateGrantLifecycle(unittest.TestCase):
    """evaluate_grant_lifecycle state computation."""

    def setUp(self):
        self.now = _dt("2026-06-20T12:00:00")

    # --- ACTIVE -----------------------------------------------------------

    def test_active_basic(self):
        identity = _make_identity(now=self.now)
        result = evaluate_grant_lifecycle(identity, self.now + timedelta(minutes=30))
        self.assertIs(result.state, GrantLifecycleState.ACTIVE)

    def test_active_no_expiry(self):
        identity = _make_identity(now=self.now, expires_at=_dt("9999-12-31T23:59:59"))
        result = evaluate_grant_lifecycle(identity, self.now + timedelta(days=365))
        self.assertIs(result.state, GrantLifecycleState.ACTIVE)

    def test_active_exactly_at_not_before(self):
        identity = _make_identity(now=self.now)
        result = evaluate_grant_lifecycle(identity, self.now)
        self.assertIs(result.state, GrantLifecycleState.ACTIVE)

    # --- PENDING (B2A enforces not_before == issued_at) -------------------

    def test_pending_before_issued_at(self):
        identity = _make_identity(now=self.now)
        result = evaluate_grant_lifecycle(identity, self.now - timedelta(seconds=1))
        self.assertIs(result.state, GrantLifecycleState.PENDING)

    def test_pending_one_second_before_issued_at(self):
        identity = _make_identity(now=self.now)
        result = evaluate_grant_lifecycle(identity, self.now - timedelta(seconds=1))
        self.assertIs(result.state, GrantLifecycleState.PENDING)

    # --- EXPIRED ----------------------------------------------------------

    def test_expired_after_expires_at(self):
        identity = _make_identity(now=self.now)
        result = evaluate_grant_lifecycle(identity, self.now + timedelta(hours=2))
        self.assertIs(result.state, GrantLifecycleState.EXPIRED)

    def test_expired_exactly_at_expires_at(self):
        identity = _make_identity(now=self.now)
        result = evaluate_grant_lifecycle(identity, self.now + timedelta(hours=1))
        self.assertIs(result.state, GrantLifecycleState.EXPIRED)

    def test_expired_edge_midnight(self):
        now = _dt("2026-06-20T00:00:00")
        identity = _make_identity(issued_at=now, not_before=now, expires_at=_dt("2026-06-21T00:00:00"), now=now)
        result = evaluate_grant_lifecycle(identity, _dt("2026-06-21T00:00:00"))
        self.assertIs(result.state, GrantLifecycleState.EXPIRED)

    # --- REVOKED (highest priority) ---------------------------------------

    def test_revoked_overrides_active(self):
        identity = _make_identity(now=self.now)
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="MISUSE", revoked_at=self.now + timedelta(minutes=10)).revocation_event
        result = evaluate_grant_lifecycle(identity, self.now + timedelta(minutes=15), revocation=rev)
        self.assertIs(result.state, GrantLifecycleState.REVOKED)

    def test_revoked_overrides_expired(self):
        identity = _make_identity(now=self.now)
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="COMPLIANCE", revoked_at=self.now + timedelta(hours=2)).revocation_event
        result = evaluate_grant_lifecycle(identity, self.now + timedelta(hours=3), revocation=rev)
        self.assertIs(result.state, GrantLifecycleState.REVOKED)

    def test_revoked_overrides_pending(self):
        identity = _make_identity(now=self.now)
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="CANCELLED", revoked_at=self.now + timedelta(minutes=5)).revocation_event
        result = evaluate_grant_lifecycle(identity, self.now + timedelta(hours=1), revocation=rev)
        self.assertIs(result.state, GrantLifecycleState.REVOKED)

    def test_revoked_at_before_eval_time(self):
        identity = _make_identity(now=self.now)
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=_dt("2026-06-01T00:00:00")).revocation_event
        result = evaluate_grant_lifecycle(identity, self.now, revocation=rev)
        self.assertIs(result.state, GrantLifecycleState.REVOKED)

    def test_revocation_grant_id_mismatch_raises(self):
        identity = _make_identity(grant_id=_gid("grant-A"), now=self.now)
        rev = build_revocation_event(grant_id=_gid("grant-B"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=self.now + timedelta(minutes=30)).revocation_event
        with self.assertRaises(ValueError):
            evaluate_grant_lifecycle(identity, self.now, revocation=rev)

    # --- Evaluation result metadata ---------------------------------------

    def test_evaluation_result_metadata(self):
        identity = _make_identity(now=self.now)
        result = evaluate_grant_lifecycle(identity, self.now + timedelta(minutes=30))
        self.assertEqual(result.grant_id, _gid("default"))
        self.assertEqual(result.evaluation_time, self.now + timedelta(minutes=30))
        self.assertEqual(result.issued_at, identity.issued_at)
        self.assertEqual(result.not_before, identity.not_before)
        self.assertEqual(result.expires_at, identity.expires_at)
        self.assertIsNone(result.revoked_at)

    def test_evaluation_result_revoked_revoked_at_populated(self):
        identity = _make_identity(now=self.now)
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=self.now + timedelta(minutes=5)).revocation_event
        result = evaluate_grant_lifecycle(identity, self.now, revocation=rev)
        self.assertEqual(result.revoked_at, self.now + timedelta(minutes=5))


# ====== No implicit system clock ==========================================


class TestEvaluateGrantLifecycleNoSystemClock(unittest.TestCase):
    def test_must_pass_explicit_time(self):
        identity = _make_identity(now=_dt("2026-06-20T12:00:00"))
        result = evaluate_grant_lifecycle(identity, _dt("2026-06-20T12:30:00"))
        self.assertIs(result.state, GrantLifecycleState.ACTIVE)


# ====== check_revocation_conflict =========================================


class TestCheckRevocationConflict(unittest.TestCase):

    def test_idempotent_identical(self):
        kwargs = dict(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="M", revocation_note_digest="n", revoked_at=_dt("2026-06-20T13:00:00"))
        r1 = build_revocation_event(**kwargs).revocation_event
        r2 = build_revocation_event(**kwargs).revocation_event
        self.assertIs(check_revocation_conflict(r1, r2), RevocationConflictPolicy.IDEMPOTENT_ACCEPT)

    def test_idempotent_different_timestamp_same_semantics(self):
        r1 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="M", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r2 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="M", revoked_at=_dt("2026-06-20T14:00:00")).revocation_event
        self.assertIs(check_revocation_conflict(r1, r2), RevocationConflictPolicy.IDEMPOTENT_ACCEPT)

    def test_conflict_different_actor(self):
        r1 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="M", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r2 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="other", revocation_reason_code="M", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        self.assertIs(check_revocation_conflict(r1, r2), RevocationConflictPolicy.CONFLICT_REJECT)

    def test_conflict_different_reason(self):
        r1 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="M", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r2 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="C", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        self.assertIs(check_revocation_conflict(r1, r2), RevocationConflictPolicy.CONFLICT_REJECT)

    def test_conflict_different_note(self):
        r1 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="M", revocation_note_digest="n1", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r2 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="M", revocation_note_digest="n2", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        self.assertIs(check_revocation_conflict(r1, r2), RevocationConflictPolicy.CONFLICT_REJECT)

    def test_diff_grant_raises(self):
        r1 = build_revocation_event(grant_id=_gid("g1"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r2 = build_revocation_event(grant_id=_gid("g2"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        with self.assertRaises(ValueError):
            check_revocation_conflict(r1, r2)


# ====== Idempotency chain =================================================


class TestRevocationIdempotencyChain(unittest.TestCase):

    def test_first_revocation_valid(self):
        identity = _make_identity(now=_dt("2026-06-20T12:00:00"))
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="M", revoked_at=_dt("2026-06-20T12:30:00")).revocation_event
        result = evaluate_grant_lifecycle(identity, _dt("2026-06-20T13:00:00"), revocation=rev)
        self.assertIs(result.state, GrantLifecycleState.REVOKED)


# ====== Identity immutable across lifecycle ===============================


class TestGrantIdentityImmutableAcrossLifecycle(unittest.TestCase):
    def test_grant_id_unchanged_by_revocation(self):
        identity = _make_identity(grant_id=_gid("immutable"), now=_dt("2026-06-20T12:00:00"))
        gid = identity.grant_id
        rev = build_revocation_event(grant_id=_gid("immutable"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=_dt("2026-06-20T12:30:00")).revocation_event
        result = evaluate_grant_lifecycle(identity, _dt("2026-06-20T13:00:00"), revocation=rev)
        self.assertEqual(result.grant_id, gid)
        self.assertNotEqual(result.grant_id, rev.event_id)

    def test_event_id_is_not_grant_id(self):
        rev = build_revocation_event(grant_id=_gid("my"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=_dt("2026-06-20T12:30:00")).revocation_event
        self.assertNotEqual(rev.event_id, rev.grant_id)


# ====== Timezone awareness ================================================


class TestTimezoneAwareness(unittest.TestCase):
    def test_evaluate_raises_on_naive_time(self):
        identity = _make_identity(now=_dt("2026-06-20T12:00:00"))
        with self.assertRaises(ValueError):
            evaluate_grant_lifecycle(identity, datetime(2026, 6, 20, 13, 0, 0))

    def test_build_revocation_rejects_naive(self):
        r = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=datetime(2026, 6, 20, 13, 0, 0))
        self.assertFalse(r.ok)

    def test_non_utc_rejected(self):
        tz2 = timezone(timedelta(hours=2))
        identity = _make_identity(now=_dt("2026-06-20T12:00:00"))
        with self.assertRaises(ValueError):
            evaluate_grant_lifecycle(identity, datetime(2026, 6, 20, 14, 0, 0, tzinfo=tz2))


# ====== Boundary moments ==================================================


class TestBoundaryMoments(unittest.TestCase):
    def test_midnight_transition(self):
        now = _dt("2026-06-20T23:59:59")
        identity = _make_identity(issued_at=_dt("2026-06-20T00:00:00"), not_before=_dt("2026-06-20T00:00:00"), expires_at=_dt("2026-06-21T00:00:00"), now=now)
        r1 = evaluate_grant_lifecycle(identity, _dt("2026-06-20T23:59:59"))
        self.assertIs(r1.state, GrantLifecycleState.ACTIVE)
        r2 = evaluate_grant_lifecycle(identity, _dt("2026-06-21T00:00:00"))
        self.assertIs(r2.state, GrantLifecycleState.EXPIRED)

    def test_year_boundary_leap_year(self):
        now = _dt("2028-02-28T12:00:00")
        identity = _make_identity(issued_at=now, not_before=now, expires_at=_dt("2028-02-29T12:00:00"), now=now)
        r1 = evaluate_grant_lifecycle(identity, _dt("2028-02-28T12:30:00"))
        self.assertIs(r1.state, GrantLifecycleState.ACTIVE)
        r2 = evaluate_grant_lifecycle(identity, _dt("2028-02-29T12:00:00"))
        self.assertIs(r2.state, GrantLifecycleState.EXPIRED)


# ====== Deterministic event hash stability ================================


class TestDeterministicEventHashStability(unittest.TestCase):
    def test_known_input_format(self):
        eid = derive_revocation_event_id(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="M", revocation_note_digest="", revoked_at=_dt("2026-06-20T13:00:00"))
        self.assertEqual(len(eid), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in eid))

    def test_consistent_with_build(self):
        args = dict(grant_id=_gid("g"), revoked_by_actor_id="X", revocation_reason_code="R", revocation_note_digest="n", revoked_at=_dt("2026-06-20T13:00:00"))
        expected = derive_revocation_event_id(**args)
        result = build_revocation_event(**args)
        self.assertTrue(result.ok)
        self.assertEqual(result.revocation_event.event_id, expected)


# ====== Permanent grant and empty note ====================================


class TestPermanentGrant(unittest.TestCase):
    def test_permanent_grant_never_expires(self):
        now = _dt("2026-06-20T12:00:00")
        identity = _make_identity(issued_at=now, not_before=now, expires_at=_dt("9999-12-31T23:59:59"), now=now)
        result = evaluate_grant_lifecycle(identity, _dt("2099-01-01T00:00:00"))
        self.assertIs(result.state, GrantLifecycleState.ACTIVE)


class TestEmptyNoteDigest(unittest.TestCase):
    def test_empty_note_accepted(self):
        r = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="R", revocation_note_digest="", revoked_at=_dt("2026-06-20T13:00:00"))
        self.assertTrue(r.ok)
        self.assertEqual(r.revocation_event.revocation_note_digest, "")


class TestBuildResultFailClosed(unittest.TestCase):
    def test_fail_closed(self):
        r = build_revocation_event(grant_id="", revoked_by_actor_id="", revocation_reason_code="", revoked_at=_dt("2026-06-20T13:00:00"))
        self.assertFalse(r.ok)
        self.assertIsNone(r.revocation_event)
        self.assertTrue(len(r.failed_checks) > 0)


# ====== Revocation priority ===============================================


class TestRevocationPriority(unittest.TestCase):
    def test_revoked_wins_over_expired(self):
        now = _dt("2026-06-20T12:00:00")
        identity = _make_identity(now=now)
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=now + timedelta(minutes=30)).revocation_event
        result = evaluate_grant_lifecycle(identity, now + timedelta(hours=2), revocation=rev)
        self.assertIs(result.state, GrantLifecycleState.REVOKED)


# ====== LifecycleEvaluationResult frozen ==================================


class TestLifecycleEvaluationResultType(unittest.TestCase):
    def test_frozen(self):
        identity = _make_identity(now=_dt("2026-06-20T12:00:00"))
        result = evaluate_grant_lifecycle(identity, _dt("2026-06-20T12:30:00"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.state = GrantLifecycleState.PENDING  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
