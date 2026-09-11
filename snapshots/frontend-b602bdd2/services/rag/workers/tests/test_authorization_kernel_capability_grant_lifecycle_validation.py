"""Tests for AK-5B2B ``capability_grant_lifecycle_validation``.

Note: B2A enforces ``not_before == issued_at``. All identity construction
must satisfy this constraint.
"""

import hashlib
import unittest
from datetime import datetime, timezone, timedelta

from authorization_kernel.enums import ActionEffect, ResourceScopeType
from authorization_kernel.resource_scope import TypedResourceScope
from authorization_kernel.capability_grant_identity import (
    CapabilityGrantIdentityCandidate,
)
from authorization_kernel.capability_grant_lifecycle import (
    build_revocation_event,
)
from authorization_kernel.capability_grant_lifecycle_validation import (
    LifecycleValidationResult,
    validate_revocation_event_fields,
    validate_lifecycle_consistency,
    validate_revocation_idempotency,
)

_UTC = timezone.utc


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=_UTC)


def _gid(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _make_identity(
    grant_id: str | None = None,
    issued_at: datetime | None = None,
    not_before: datetime | None = None,
    expires_at: datetime | None = None,
) -> CapabilityGrantIdentityCandidate:
    now = _dt("2026-06-20T12:00:00")
    if issued_at is None:
        issued_at = now
    if not_before is None:
        not_before = issued_at
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
        resource_scopes=(TypedResourceScope(scope_type=ResourceScopeType.FILE_PATH, canonical_id="/tmp/x"),),
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


class TestValidateRevocationEventFields(unittest.TestCase):
    def test_valid_fields(self):
        r = validate_revocation_event_fields(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="C", revocation_note_digest="abc", revoked_at=_dt("2026-06-20T13:00:00"))
        self.assertTrue(r.ok)
        self.assertIsNotNone(r.revocation_event)

    def test_invalid_grant_id(self):
        r = validate_revocation_event_fields(grant_id="", revoked_by_actor_id="admin", revocation_reason_code="C", revoked_at=_dt("2026-06-20T13:00:00"))
        self.assertFalse(r.ok)

    def test_naive_revoked_at_rejected(self):
        r = validate_revocation_event_fields(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=datetime(2026, 6, 20, 13, 0, 0))
        self.assertFalse(r.ok)


class TestValidateLifecycleConsistency(unittest.TestCase):

    def setUp(self):
        self.now = _dt("2026-06-20T12:00:00")

    def test_valid_no_revocation(self):
        self.assertTrue(validate_lifecycle_consistency(_make_identity(), self.now).ok)

    def test_valid_with_revocation(self):
        identity = _make_identity()
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=self.now + timedelta(minutes=30)).revocation_event
        self.assertTrue(validate_lifecycle_consistency(identity, self.now + timedelta(hours=1), revocation=rev).ok)

    def test_none_identity_rejected(self):
        r = validate_lifecycle_consistency(None, self.now)  # type: ignore[arg-type]
        self.assertFalse(r.ok)

    def test_naive_eval_time_rejected(self):
        r = validate_lifecycle_consistency(_make_identity(), datetime(2026, 6, 20, 13, 0, 0))
        self.assertFalse(r.ok)

    def test_revoked_at_before_issued_at_rejected(self):
        identity = _make_identity(issued_at=_dt("2026-06-20T12:00:00"))
        rev = build_revocation_event(grant_id=_gid("default"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=_dt("2026-06-19T12:00:00")).revocation_event
        r = validate_lifecycle_consistency(identity, _dt("2026-06-20T13:00:00"), revocation=rev)
        self.assertFalse(r.ok)

    def test_grant_id_mismatch_rejected(self):
        identity = _make_identity(grant_id=_gid("grant-A"))
        rev = build_revocation_event(grant_id=_gid("grant-B"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r = validate_lifecycle_consistency(identity, _dt("2026-06-20T13:00:00"), revocation=rev)
        self.assertFalse(r.ok)

    def test_non_utc_eval_time_rejected(self):
        tz2 = timezone(timedelta(hours=2))
        r = validate_lifecycle_consistency(_make_identity(), datetime(2026, 6, 20, 14, 0, 0, tzinfo=tz2))
        self.assertFalse(r.ok)


class TestValidateRevocationIdempotency(unittest.TestCase):

    def test_first_revocation_valid(self):
        rev = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="R", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        self.assertTrue(validate_revocation_idempotency(None, rev).ok)

    def test_duplicate_idempotent(self):
        kwargs = dict(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="P", revoked_at=_dt("2026-06-20T13:00:00"))
        r1 = build_revocation_event(**kwargs).revocation_event
        r2 = build_revocation_event(**kwargs).revocation_event
        self.assertTrue(validate_revocation_idempotency(r1, r2).ok)

    def test_conflict_rejected(self):
        r1 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="P", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r2 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="other", revocation_reason_code="P", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r = validate_revocation_idempotency(r1, r2)
        self.assertFalse(r.ok)
        self.assertIn("conflict", " ".join(r.failed_checks).lower())

    def test_conflict_reason_code(self):
        r1 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="P", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r2 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="C", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        self.assertFalse(validate_revocation_idempotency(r1, r2).ok)

    def test_conflict_note_digest(self):
        r1 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="P", revocation_note_digest="n1", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        r2 = build_revocation_event(grant_id=_gid("g"), revoked_by_actor_id="admin", revocation_reason_code="P", revocation_note_digest="n2", revoked_at=_dt("2026-06-20T13:00:00")).revocation_event
        self.assertFalse(validate_revocation_idempotency(r1, r2).ok)


class TestLifecycleValidationResultType(unittest.TestCase):

    def test_frozen(self):
        r = LifecycleValidationResult(ok=True, failed_checks=())
        with self.assertRaises(Exception):
            r.ok = False  # type: ignore[misc]

    def test_fail_closed(self):
        r = LifecycleValidationResult(ok=False, failed_checks=("x",))
        self.assertFalse(r.ok)
        self.assertEqual(len(r.failed_checks), 1)


if __name__ == "__main__":
    unittest.main()
