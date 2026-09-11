"""
GOAA Authorization Kernel AK-3 — Deny State Unit Tests
========================================================
Tests: validation, creation, lifecycle, ledger integrity, fold.

Framework: unittest (standard library). No pytest dependency.
All tests are pure — no I/O, no subprocess, no network.
No file I/O, no Git commands, no workdir dependencies.

Plan: AK-3 V27.1 FINAL FREEZE
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from typing import Any

from authorization_kernel.enums import (
    ActionEffect,
    DenyEventType,
    DenyOrigin,
    DenyScope,
    ResourceScopeType,
)
from authorization_kernel.deny_event import DenyEvent
from authorization_kernel.resource_scope import (
    TypedResourceScope,
    canonical_resource_identity,
)
from authorization_kernel.canonical_serialization import (
    format_utc_rfc3339,
    sha256_hex,
)
from authorization_kernel.deny_event_validation import (
    HASH_PLACEHOLDER,
    LOCKED_FIELDS,
    TERMINAL_EVENT_TYPES,
    LIFECYCLE_EVENT_TYPES,
    DENY_ORIGIN_SCOPE_MATRIX,
    DenyCreationRequest,
    DenyCreationValidation,
    DenyLifecycleRequest,
    DenyLifecycleValidation,
    DenyMatchContext,
    MatchProofContext,
    NormalizedMatchFailure,
    require_aware_datetime,
    validate_deny_creation,
    validate_deny_lifecycle_request,
    validate_origin_scope_matrix,
    canonical_effective_deny_identity,
)
from authorization_kernel.deny_ledger_state import (
    DenyLedger,
    DenyLedgerEntry,
    DenyAppendResult,
    DenyFoldResult,
    EffectiveDeny,
    create_deny_entry,
    append_lifecycle_entry,
    fold_effective_denies,
    verify_ledger_integrity,
    compute_deny_event_hash,
    compute_deny_ledger_entry_hash,
    deny_event_payload,
    deny_ledger_entry_payload,
)


# ============================================================
# Helpers
# ============================================================

TZ_UTC = timezone.utc

def utc(year: int, month: int, day: int,
        hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=TZ_UTC)

def utc_now() -> datetime:
    return datetime.now(TZ_UTC)

def make_scope(scope_type: str = "file_path", canonical_id: str = "/tmp/test",
               **attrs: str) -> TypedResourceScope:
    st = ResourceScopeType(scope_type)
    attr_tuple: tuple[tuple[str, str], ...] = tuple((k, v) for k, v in attrs.items())
    return TypedResourceScope(scope_type=st, canonical_id=canonical_id,
                              attributes=attr_tuple)

SCOPE_A = make_scope(canonical_id="/tmp/a")
SCOPE_B = make_scope(canonical_id="/tmp/b")

def make_event(
    *,
    event_id: str = "evt-1",
    deny_id: str = "deny-1",
    task_id: str = "task-1",
    session_id: str | None = "session-1",
    event_type: DenyEventType = DenyEventType.DENY_CREATED,
    deny_scope: DenyScope = DenyScope.CURRENT_TASK,
    deny_origin: DenyOrigin = DenyOrigin.USER_DENIAL,
    primary_effect: ActionEffect | None = ActionEffect.DELETE,
    secondary_effects: frozenset[ActionEffect] | None = None,
    resource_scopes: tuple[TypedResourceScope, ...] | None = None,
    groups: frozenset[str] | None = None,
    actor: str = "user",
    occurred_at: datetime | None = None,
    expires_at: datetime | None = None,
    reason: str = "test",
    approval_id: str | None = "apr-1",
    previous_event_hash: str | None = None,
    event_hash: str = "",
) -> DenyEvent:
    if secondary_effects is None:
        secondary_effects = frozenset()
    if resource_scopes is None:
        resource_scopes = (SCOPE_A,)
    if groups is None:
        groups = frozenset({"write"})
    if occurred_at is None:
        occurred_at = utc_now()
    return DenyEvent(
        event_id=event_id,
        deny_id=deny_id,
        task_id=task_id,
        session_id=session_id,
        event_type=event_type,
        deny_scope=deny_scope,
        deny_origin=deny_origin,
        primary_effect=primary_effect if primary_effect is not None else ActionEffect.READ,
        secondary_effects=secondary_effects,
        resource_scopes=resource_scopes,
        equivalent_action_groups=groups,
        actor=actor,
        occurred_at=occurred_at,
        expires_at=expires_at,
        reason=reason,
        approval_id=approval_id,
        previous_event_hash=previous_event_hash,
        event_hash=event_hash,
    )


def make_creation_request(
    event: DenyEvent | None = None,
    persistent: bool = False,
    request_id: str | None = None,
) -> DenyCreationRequest:
    if event is None:
        event = make_event()
    return DenyCreationRequest(event=event, persistent=persistent,
                               request_id=request_id)


def make_ledger_with_entry(
    event: DenyEvent | None = None,
    request_id: str | None = None,
    persistent: bool = False,
) -> DenyLedger:
    if event is None:
        event = make_event()
    # Build entry with proper hash
    entry = _make_ledger_entry(event, request_id=request_id, persistent=persistent)
    return DenyLedger(entries=(entry,))


def _make_ledger_entry(
    event: DenyEvent,
    previous_entry_hash: str | None = None,
    request_id: str | None = None,
    persistent: bool = False,
) -> DenyLedgerEntry:
    # Two-phase hash
    provisional_event = event
    if not provisional_event.event_hash or provisional_event.event_hash == "":
        # Need to compute hash
        dummy = DenyEvent(
            event_id=provisional_event.event_id,
            deny_id=provisional_event.deny_id,
            task_id=provisional_event.task_id,
            session_id=provisional_event.session_id,
            event_type=provisional_event.event_type,
            deny_scope=provisional_event.deny_scope,
            deny_origin=provisional_event.deny_origin,
            primary_effect=provisional_event.primary_effect,
            secondary_effects=provisional_event.secondary_effects,
            resource_scopes=provisional_event.resource_scopes,
            equivalent_action_groups=provisional_event.equivalent_action_groups,
            actor=provisional_event.actor,
            occurred_at=provisional_event.occurred_at,
            expires_at=provisional_event.expires_at,
            reason=provisional_event.reason,
            approval_id=provisional_event.approval_id,
            previous_event_hash=provisional_event.previous_event_hash,
            event_hash=HASH_PLACEHOLDER,
        )
        event_hash = compute_deny_event_hash(dummy)
        provisional_event = dummy

    # Now finalize
    payload = deny_event_payload(provisional_event)
    final_event_hash = sha256_hex(payload)
    final_event = DenyEvent(
        event_id=provisional_event.event_id,
        deny_id=provisional_event.deny_id,
        task_id=provisional_event.task_id,
        session_id=provisional_event.session_id,
        event_type=provisional_event.event_type,
        deny_scope=provisional_event.deny_scope,
        deny_origin=provisional_event.deny_origin,
        primary_effect=provisional_event.primary_effect,
        secondary_effects=provisional_event.secondary_effects,
        resource_scopes=provisional_event.resource_scopes,
        equivalent_action_groups=provisional_event.equivalent_action_groups,
        actor=provisional_event.actor,
        occurred_at=provisional_event.occurred_at,
        expires_at=provisional_event.expires_at,
        reason=provisional_event.reason,
        approval_id=provisional_event.approval_id,
        previous_event_hash=provisional_event.previous_event_hash,
        event_hash=final_event_hash,
    )

    # Build entry
    entry_payload = deny_ledger_entry_payload(
        type('_Entry', (), {
            'event': final_event,
            'previous_entry_hash': previous_entry_hash,
            'request_id': request_id,
            'persistent': persistent,
            'entry_hash': HASH_PLACEHOLDER,
        })()
    )
    entry_hash = sha256_hex(entry_payload)

    return DenyLedgerEntry(
        event=final_event,
        previous_entry_hash=previous_entry_hash,
        entry_hash=entry_hash,
        request_id=request_id,
        persistent=persistent,
    )


def make_lifecycle_request(
    deny_id: str = "deny-1",
    event_id: str = "evt-life-1",
    event_type: DenyEventType = DenyEventType.DENY_REVOKED,
    actor: str = "user",
    occurred_at: datetime | None = None,
    reason: str = "revoke",
    approval_id: str | None = "apr-life",
) -> DenyLifecycleRequest:
    if occurred_at is None:
        occurred_at = utc_now()
    return DenyLifecycleRequest(
        deny_id=deny_id,
        event_id=event_id,
        event_type=event_type,
        actor=actor,
        occurred_at=occurred_at,
        reason=reason,
        approval_id=approval_id,
    )


class _TzOnly(datetime):
    """A datetime subclass whose instances have tzinfo but utcoffset returns None."""
    pass

def _make_tz_only_naive_dt(year=2026, month=1, day=1):
    """Make a datetime-like object with tzinfo set but utcoffset()=None."""
    return _TzOnly(year, month, day, tzinfo=TZ_UTC)


# ============================================================
# Raw constructors (bypass __post_init__ for error tests)
# ============================================================

def _raw_event(**overrides: Any) -> DenyEvent:
    """Create a DenyEvent bypassing __post_init__ validation.

    Used by error tests that need to exercise validate_deny_creation
    on structurally invalid events that DenyEvent.__post_init__ would
    normally reject (e.g. naive datetimes, empty deny_id)."""
    defaults: dict[str, Any] = {
        "event_id": "evt-raw",
        "deny_id": "deny-raw",
        "task_id": "task-1",
        "session_id": "session-1",
        "event_type": DenyEventType.DENY_CREATED,
        "deny_scope": DenyScope.CURRENT_TASK,
        "deny_origin": DenyOrigin.USER_DENIAL,
        "primary_effect": ActionEffect.DELETE,
        "secondary_effects": frozenset(),
        "resource_scopes": (SCOPE_A,),
        "equivalent_action_groups": frozenset({"write"}),
        "actor": "user",
        "occurred_at": utc_now(),
        "expires_at": None,
        "reason": "test",
        "approval_id": None,
        "previous_event_hash": None,
        "event_hash": "",
    }
    merged = {**defaults, **overrides}
    ev = object.__new__(DenyEvent)
    for k, v in merged.items():
        object.__setattr__(ev, k, v)
    return ev


def _raw_creation_request(**overrides: Any) -> DenyCreationRequest:
    """Create a DenyCreationRequest bypassing __post_init__."""
    merged: dict[str, Any] = {
        "event": _raw_event(),
        "persistent": False,
        "request_id": None,
    }
    merged.update(overrides)
    req = object.__new__(DenyCreationRequest)
    for k, v in merged.items():
        object.__setattr__(req, k, v)
    return req


def _raw_lifecycle_request(**overrides: Any) -> DenyLifecycleRequest:
    """Create a DenyLifecycleRequest bypassing __post_init__."""
    merged: dict[str, Any] = {
        "deny_id": "deny-life",
        "event_id": "evt-life",
        "event_type": DenyEventType.DENY_REVOKED,
        "actor": "user",
        "occurred_at": utc_now(),
        "reason": "test",
        "approval_id": None,
    }
    merged.update(overrides)
    req = object.__new__(DenyLifecycleRequest)
    for k, v in merged.items():
        object.__setattr__(req, k, v)
    return req


# ============================================================
# Test: require_aware_datetime
# ============================================================

class TestRequireAwareDatetime(unittest.TestCase):

    def test_naive_datetime_raises(self):
        """naive datetime → ValueError."""
        dt = datetime(2026, 1, 1)  # No tzinfo
        with self.assertRaises(ValueError):
            require_aware_datetime(dt, "test")

    def test_aware_datetime_passes(self):
        """aware datetime → no exception."""
        dt = utc(2026, 1, 1)
        require_aware_datetime(dt, "test")

    def test_not_datetime_raises(self):
        """Non-datetime → ValueError."""
        with self.assertRaises(ValueError):
            require_aware_datetime("not a datetime", "test")

    def test_none_raises(self):
        """None → ValueError."""
        with self.assertRaises(ValueError):
            require_aware_datetime(None, "test")


# ============================================================
# Test: DenyCreationRequest validation
# ============================================================

class TestDenyCreationRequest(unittest.TestCase):

    def test_valid_creation_allowed(self):
        """Valid creation request → validation passes."""
        event = make_event(
            deny_origin=DenyOrigin.USER_DENIAL,
            deny_scope=DenyScope.CURRENT_TASK,
            primary_effect=ActionEffect.DELETE,
        )
        request = make_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertTrue(result.valid)

    def test_auto_policy_persistent_policy_all_conditions(self):
        """AUTOMATIC_POLICY_BLOCK + PERSISTENT_POLICY + 5 conditions → allowed."""
        event = make_event(
            deny_origin=DenyOrigin.AUTOMATIC_POLICY_BLOCK,
            deny_scope=DenyScope.PERSISTENT_POLICY,
            primary_effect=ActionEffect.DELETE,
            expires_at=utc_now() + timedelta(hours=1),
            groups=frozenset({"write"}),
            resource_scopes=(SCOPE_A, SCOPE_B),
        )
        request = DenyCreationRequest(event=event, persistent=True)
        result = validate_deny_creation(request)
        self.assertTrue(result.valid)

    def test_auto_policy_current_task_persistent_rejected(self):
        """AUTO + CURRENT_TASK + persistent=False → rejected (AUTO needs PERSISTENT_POLICY)."""
        now = utc_now()
        event = make_event(
            occurred_at=now,
            deny_origin=DenyOrigin.AUTOMATIC_POLICY_BLOCK,
            deny_scope=DenyScope.CURRENT_TASK,
            expires_at=now + timedelta(hours=1),
            groups=frozenset({"write"}),
            resource_scopes=(SCOPE_A,),
        )
        request = DenyCreationRequest(event=event, persistent=False)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)
        self.assertIn("deny_origin_scope_invalid", result.failed_checks)

    def test_event_type_not_created_rejected(self):
        """event_type not DENY_CREATED → rejected."""
        event = make_event(event_type=DenyEventType.DENY_REVOKED)
        request = make_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)
        self.assertIn("deny_event_type_not_created", result.failed_checks)

    def test_group_member_non_string_rejected(self):
        """groups member not string → rejected."""
        event = make_event(groups=frozenset({42}))
        request = make_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)
        self.assertIn("deny_group_member_invalid", result.failed_checks)

    def test_group_empty_string_rejected(self):
        """group empty string → rejected."""
        event = make_event(groups=frozenset({"write", ""}))
        request = make_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)

    def test_resource_member_wrong_type_rejected(self):
        """resource scope member wrong type → rejected."""
        event = _raw_event(resource_scopes=("not_a_scope",))
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)

    def test_resource_identity_duplicate_rejected(self):
        """resource canonical identity duplicate → rejected."""
        same = make_scope(canonical_id="/tmp/dup")
        event = _raw_event(resource_scopes=(same, same))
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)
        self.assertIn("deny_scope_identity_duplicate", result.failed_checks)

    def test_secondary_effect_member_wrong_type_rejected(self):
        """secondary effect member not ActionEffect → rejected."""
        event = _raw_event(secondary_effects=frozenset({"not_an_effect"}))
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)

    def test_naive_occurred_at_rejected(self):
        """naive occurred_at → rejected."""
        naive = datetime(2026, 1, 1)
        event = _raw_event(occurred_at=naive)
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)

    def test_naive_expires_at_rejected(self):
        """naive expires_at → rejected."""
        event = _raw_event(expires_at=datetime(2026, 1, 1))
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)

    def test_empty_deny_id_rejected(self):
        """empty deny_id → rejected."""
        event = _raw_event(deny_id="")
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)

    def test_primary_effect_none_no_groups_rejected(self):
        """primary_effect=None + empty groups → rejected."""
        event = _raw_event(primary_effect=None, equivalent_action_groups=frozenset())
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)

    def test_persistent_not_bool_rejected(self):
        """persistent not bool → rejected."""
        request = _raw_creation_request(persistent="yes")  # type: ignore
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)

    def test_event_type_deny_created_passes(self):
        """event_type=DENY_CREATED passes type check."""
        event = make_event(event_type=DenyEventType.DENY_CREATED)
        request = make_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertTrue(result.valid)


# ============================================================
# Test: Origin/Scope matrix
# ============================================================

class TestOriginScopeMatrix(unittest.TestCase):

    def _make_matrix_request(self, origin: DenyOrigin, scope: DenyScope):
        """Build a request that satisfies all invariants for the given origin/scope."""
        now = utc_now()
        kwargs = dict(deny_origin=origin, deny_scope=scope, occurred_at=now)
        req_kwargs = dict()
        if scope == DenyScope.CURRENT_ACTION:
            req_kwargs["request_id"] = "req-1"
        if scope == DenyScope.PERSISTENT_POLICY or origin == DenyOrigin.AUTOMATIC_POLICY_BLOCK:
            req_kwargs["persistent"] = True
        if origin == DenyOrigin.AUTOMATIC_POLICY_BLOCK:
            kwargs["expires_at"] = now + timedelta(hours=1)
            kwargs["groups"] = frozenset({"write"})
            kwargs["resource_scopes"] = (SCOPE_A, SCOPE_B)
        event = make_event(**kwargs)
        return make_creation_request(event=event, **req_kwargs)

    def test_all_allowed_combinations(self):
        """Each allowed combination in frozen matrix passes."""
        for origin, scopes in DENY_ORIGIN_SCOPE_MATRIX.items():
            for scope in scopes:
                request = self._make_matrix_request(origin, scope)
                result = validate_deny_creation(request)
                self.assertTrue(
                    result.valid,
                    f"Matrix allows {origin}×{scope} but validation rejected: {result.failed_checks}",
                )

    def test_all_forbidden_combinations(self):
        """Each forbidden combination fails."""
        for origin in DenyOrigin:
            allowed = DENY_ORIGIN_SCOPE_MATRIX[origin]
            for scope in DenyScope:
                if scope in allowed:
                    continue
                request = self._make_matrix_request(origin, scope)
                result = validate_deny_creation(request)
                self.assertFalse(
                    result.valid,
                    f"Matrix forbids {origin}×{scope} but validation passed",
                )

    def test_all_origins_covered(self):
        """All DenyOrigin members are covered by matrix."""
        for origin in DenyOrigin:
            self.assertIn(origin, DENY_ORIGIN_SCOPE_MATRIX)

    def test_persistent_origin_only_persistent_scope(self):
        """PERSISTENT_POLICY origin only allows PERSISTENT_POLICY scope."""
        allowed = DENY_ORIGIN_SCOPE_MATRIX[DenyOrigin.PERSISTENT_POLICY]
        self.assertEqual(allowed, frozenset({DenyScope.PERSISTENT_POLICY}))

    def test_auto_policy_only_persistent_scope(self):
        """AUTOMATIC_POLICY_BLOCK only allows PERSISTENT_POLICY scope."""
        allowed = DENY_ORIGIN_SCOPE_MATRIX[DenyOrigin.AUTOMATIC_POLICY_BLOCK]
        self.assertEqual(allowed, frozenset({DenyScope.PERSISTENT_POLICY}))


# ============================================================
# Test: require_aware_datetime (three-layer)
# ============================================================

class TestStrictAwareDatetime(unittest.TestCase):

    def test_tzinfo_with_utcoffset_none_raises(self):
        """tzinfo present but utcoffset=None → ValueError."""
        class _FixedNoOffset(datetime):
            @property
            def tzinfo(self):
                return TZ_UTC  # type: ignore  # lies about tzinfo
            def utcoffset(self):
                return None
        dt = _FixedNoOffset(2026, 1, 1)
        with self.assertRaises(ValueError):
            require_aware_datetime(dt, "test")


# ============================================================
# Test: create_deny_entry
# ============================================================

class TestCreateDenyEntry(unittest.TestCase):

    def test_create_on_empty_ledger_succeeds(self):
        """Creating deny on empty ledger succeeds."""
        ledger = DenyLedger()
        event = make_event(
            deny_origin=DenyOrigin.USER_DENIAL,
            deny_scope=DenyScope.CURRENT_TASK,
        )
        request = make_creation_request(event=event)
        result = create_deny_entry(ledger, request)
        self.assertTrue(result.appended)
        self.assertIsNotNone(result.entry)

    def test_create_duplicate_deny_id_rejected(self):
        """Duplicate deny_id → rejected."""
        event = make_event(deny_id="dup-1")
        request = make_creation_request(event=event)
        result1 = create_deny_entry(DenyLedger(), request)
        self.assertTrue(result1.appended)

        event2 = make_event(
            deny_id="dup-1",
            event_id="evt-2",
        )
        request2 = make_creation_request(event=event2)
        result2 = create_deny_entry(result1.ledger, request2)
        self.assertFalse(result2.appended)
        self.assertEqual(result2.reason_code, "duplicate_deny_created")

    def test_invalid_request_rejected(self):
        """Invalid creation request → rejected, original ledger returned."""
        ledger = DenyLedger()
        event = make_event(event_type=DenyEventType.DENY_REVOKED)  # wrong type
        request = make_creation_request(event=event)
        result = create_deny_entry(ledger, request)
        self.assertFalse(result.appended)
        self.assertIs(result.ledger, ledger)

    def test_candidate_ledger_verified(self):
        """Candidate ledger integrity verified before returning success."""
        ledger = DenyLedger()
        event = make_event()
        request = make_creation_request(event=event)
        result = create_deny_entry(ledger, request)
        self.assertTrue(result.appended)
        # Verify the result ledger integrity
        integrity = verify_ledger_integrity(result.ledger)
        self.assertTrue(integrity.valid)

    def test_reason_code_stable(self):
        """Error reason codes are stable strings."""
        ledger = DenyLedger()
        event = make_event(event_type=DenyEventType.DENY_EXPIRED)
        request = make_creation_request(event=event)
        result = create_deny_entry(ledger, request)
        self.assertFalse(result.appended)
        # No raw exception text
        self.assertNotIn("TypeError", result.reason_code)
        self.assertNotIn("ValueError", result.reason_code)


# ============================================================
# Test: append_lifecycle_entry
# ============================================================

class TestAppendLifecycleEntry(unittest.TestCase):

    def test_created_to_revoked_succeeds(self):
        """CREATED → REVOKED succeeds."""
        event = make_event(deny_id="deny-life-1")
        request = make_creation_request(event=event)
        result = create_deny_entry(DenyLedger(), request)
        self.assertTrue(result.appended)

        life_req = make_lifecycle_request(
            deny_id="deny-life-1",
            event_type=DenyEventType.DENY_REVOKED,
        )
        life_result = append_lifecycle_entry(result.ledger, life_req)
        self.assertTrue(life_result.appended)

    def test_created_to_superseded_succeeds(self):
        """CREATED → SUPERSEDED succeeds."""
        event = make_event(deny_id="deny-sup-1")
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(deny_id="deny-sup-1", event_type=DenyEventType.DENY_SUPERSEDED)
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertTrue(r2.appended)

    def test_created_to_expired_succeeds(self):
        """CREATED → EXPIRED succeeds (with valid expires_at)."""
        now = utc_now()
        event = make_event(
            occurred_at=now,
            deny_id="deny-exp-1",
            expires_at=now,
        )
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(
            deny_id="deny-exp-1",
            event_type=DenyEventType.DENY_EXPIRED,
            occurred_at=now,
        )
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertTrue(r2.appended)

    def test_terminal_after_terminal_rejected(self):
        """REVOKED → any lifecycle rejected."""
        event = make_event(deny_id="term-1")
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life1 = make_lifecycle_request(deny_id="term-1", event_type=DenyEventType.DENY_REVOKED)
        r2 = append_lifecycle_entry(r1.ledger, life1)
        self.assertTrue(r2.appended)
        life2 = make_lifecycle_request(
            deny_id="term-1",
            event_id="evt-after-terminal",
            event_type=DenyEventType.DENY_REVOKED,
        )
        r3 = append_lifecycle_entry(r2.ledger, life2)
        self.assertFalse(r3.appended)
        self.assertEqual(r3.reason_code, "lifecycle_terminal_state")

    def test_deny_not_found_rejected(self):
        """Non-existent deny_id → rejected."""
        ledger = DenyLedger()
        life = make_lifecycle_request(deny_id="nonexistent")
        result = append_lifecycle_entry(ledger, life)
        self.assertFalse(result.appended)
        self.assertEqual(result.reason_code, "lifecycle_deny_not_found")

    def test_event_id_duplicate_rejected(self):
        """Duplicate event_id → rejected."""
        event = make_event(deny_id="dup-eid-1")
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(
            deny_id="dup-eid-1",
            event_id=event.event_id,  # same as the creation event_id
        )
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertFalse(r2.appended)
        self.assertEqual(r2.reason_code, "lifecycle_event_id_duplicate")

    def test_time_reversal_rejected(self):
        """occurred_at before CREATED → rejected."""
        event = make_event(
            deny_id="time-rev-1",
            occurred_at=utc(2026, 6, 1, 12, 0, 0),
        )
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(
            deny_id="time-rev-1",
            occurred_at=utc(2026, 6, 1, 11, 0, 0),  # earlier
        )
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertFalse(r2.appended)
        self.assertEqual(r2.reason_code, "lifecycle_time_reversal")

    def test_expired_no_expiry_rejected(self):
        """DENY_EXPIRED with no expires_at → rejected."""
        event = make_event(
            deny_id="exp-noexp-1",
            expires_at=None,
        )
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(
            deny_id="exp-noexp-1",
            event_type=DenyEventType.DENY_EXPIRED,
        )
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertFalse(r2.appended)
        self.assertEqual(r2.reason_code, "lifecycle_expiry_not_defined")

    def test_expired_before_expiry_rejected(self):
        """DENY_EXPIRED before expires_at → rejected."""
        future = utc_now() + timedelta(days=1)
        event = make_event(
            deny_id="exp-early-1",
            expires_at=future,
        )
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(
            deny_id="exp-early-1",
            event_type=DenyEventType.DENY_EXPIRED,
            occurred_at=utc_now(),  # now < future
        )
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertFalse(r2.appended)
        self.assertEqual(r2.reason_code, "lifecycle_expired_before_expiry")

    def test_expired_at_expiry_allowed(self):
        """DENY_EXPIRED at expires_at → allowed."""
        now = utc_now()
        event = make_event(
            occurred_at=now,
            deny_id="exp-at-1",
            expires_at=now,
        )
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(
            deny_id="exp-at-1",
            event_type=DenyEventType.DENY_EXPIRED,
            occurred_at=now,
        )
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertTrue(r2.appended)

    def test_revoked_does_not_require_expiry(self):
        """REVOKED does not require expires_at."""
        event = make_event(deny_id="rev-noexp-1", expires_at=None)
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(deny_id="rev-noexp-1")
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertTrue(r2.appended)

    def test_approval_id_from_request(self):
        """lifecycle approval_id uses request value, not CREATED."""
        event = make_event(deny_id="apr-from-req-1", approval_id="apr-orig")
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(
            deny_id="apr-from-req-1",
            approval_id="apr-lifecycle",
        )
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertTrue(r2.appended)
        # Lifecycle entry should have the request's approval_id
        self.assertEqual(r2.entry.event.approval_id, "apr-lifecycle")
        self.assertNotEqual(r2.entry.event.approval_id, "apr-orig")


# ============================================================
# Test: Lifecycle locked fields
# ============================================================

class TestLifecycleLockedFields(unittest.TestCase):

    def test_locked_fields_from_created(self):
        """Locked fields in lifecycle event match CREATED entry."""
        event = make_event(
            deny_id="locked-1",
            deny_scope=DenyScope.CURRENT_TASK,
            deny_origin=DenyOrigin.USER_DENIAL,
            primary_effect=ActionEffect.DELETE,
        )
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(deny_id="locked-1")
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertTrue(r2.appended)
        created_ev = r1.entry.event
        lifecycle_ev = r2.entry.event
        for field in ("deny_scope", "deny_origin", "task_id", "session_id",
                       "primary_effect", "secondary_effects", "resource_scopes",
                       "equivalent_action_groups", "expires_at"):
            self.assertEqual(
                getattr(lifecycle_ev, field),
                getattr(created_ev, field),
                f"Locked field {field} drifted",
            )

    def test_approval_id_not_locked(self):
        """approval_id is NOT locked — can differ from CREATED."""
        event = make_event(deny_id="apr-not-locked-1", approval_id="orig")
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(
            deny_id="apr-not-locked-1",
            approval_id="new-apr",
        )
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertTrue(r2.appended)
        self.assertEqual(r2.entry.event.approval_id, "new-apr")


# ============================================================
# Test: Interleaved deny dual chain
# ============================================================

class TestInterleavedDualChain(unittest.TestCase):

    def test_interleaved_event_chain(self):
        """Interleaved denies maintain correct per-deny event chain."""
        # d1 CREATED, d2 CREATED, d1 REVOKED
        e1 = make_event(deny_id="d1", event_id="e1")
        ledger = create_deny_entry(DenyLedger(), make_creation_request(event=e1)).ledger
        e2 = make_event(deny_id="d2", event_id="e2")
        ledger = create_deny_entry(ledger, make_creation_request(event=e2)).ledger
        life = make_lifecycle_request(deny_id="d1", event_id="e3")
        result = append_lifecycle_entry(ledger, life)
        self.assertTrue(result.appended)
        # d1 REVOKED previous_event_hash should be d1 CREATED event_hash
        d1_created_hash = result.ledger.entries[0].event.event_hash
        self.assertEqual(
            result.ledger.entries[2].event.previous_event_hash,
            d1_created_hash,
        )

    def test_interleaved_entry_chain(self):
        """Interleaved denies maintain correct global entry chain."""
        e1 = make_event(deny_id="d1", event_id="e1")
        ledger = create_deny_entry(DenyLedger(), make_creation_request(event=e1)).ledger
        e2 = make_event(deny_id="d2", event_id="e2")
        ledger = create_deny_entry(ledger, make_creation_request(event=e2)).ledger
        life = make_lifecycle_request(deny_id="d1", event_id="e3")
        result = append_lifecycle_entry(ledger, life)
        self.assertTrue(result.appended)
        # d1 REVOKED previous_entry_hash should be d2 CREATED entry_hash
        d2_created_hash = result.ledger.entries[1].entry_hash
        self.assertEqual(
            result.ledger.entries[2].previous_entry_hash,
            d2_created_hash,
        )


# ============================================================
# Test: verify_ledger_integrity
# ============================================================

class TestVerifyLedgerIntegrity(unittest.TestCase):

    def test_empty_ledger_valid(self):
        """Empty ledger is integrity-valid (no structural problems)."""
        ledger = DenyLedger()
        result = verify_ledger_integrity(ledger)
        self.assertTrue(result.valid)
        self.assertEqual(result.code, "integrity_ok")
        self.assertEqual(result.entry_count, 0)
        self.assertIsNone(result.ledger_tip_hash)

    def test_single_entry_valid(self):
        """Single CREATED entry → valid."""
        event = make_event()
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        result = verify_ledger_integrity(r1.ledger)
        self.assertTrue(result.valid)

    def test_corrupted_entry_hash_detected(self):
        """Corrupted entry hash → invalid."""
        event = make_event()
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        # Corrupt the entry hash
        bad_entry = DenyLedgerEntry(
            event=r1.ledger.entries[0].event,
            previous_entry_hash=r1.ledger.entries[0].previous_entry_hash,
            entry_hash="0000000000000000000000000000000000000000000000000000000000000000",
            request_id=r1.ledger.entries[0].request_id,
            persistent=r1.ledger.entries[0].persistent,
        )
        bad_ledger = DenyLedger(entries=(bad_entry,))
        result = verify_ledger_integrity(bad_ledger)
        self.assertFalse(result.valid)


# ============================================================
# Test: fold_effective_denies
# ============================================================

class TestFoldEffectiveDenies(unittest.TestCase):

    def test_fold_valid_ledger(self):
        """Fold on valid ledger returns active denies."""
        event = make_event(deny_id="fold-1")
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        result = fold_effective_denies(r1.ledger)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.active_denies), 1)

    def test_fold_invalid_ledger(self):
        """Fold on invalid ledger returns invalid result."""
        bad_ledger = DenyLedger(entries=(
            DenyLedgerEntry(
                event=make_event(event_type=DenyEventType.DENY_REVOKED),
                previous_entry_hash=None,
                entry_hash="",
            ),
        ))
        result = fold_effective_denies(bad_ledger)
        self.assertFalse(result.valid)
        self.assertEqual(len(result.active_denies), 0)

    def test_fold_expired_deny_inactive(self):
        """Fold marks expired deny as inactive."""
        past = utc_now() - timedelta(hours=1)
        event = make_event(
            occurred_at=past,
            deny_id="exp-fold-1",
            expires_at=past,
        )
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        # Fold with decision_time after expires_at
        result = fold_effective_denies(r1.ledger, decision_time=utc_now())
        self.assertTrue(result.valid)
        self.assertEqual(len(result.active_denies), 0)

    def test_fold_active_deny_included(self):
        """Fold includes non-expired deny."""
        future = utc_now() + timedelta(hours=1)
        event = make_event(
            deny_id="active-fold-1",
            expires_at=future,
        )
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        result = fold_effective_denies(r1.ledger, decision_time=utc_now())
        self.assertTrue(result.valid)
        self.assertEqual(len(result.active_denies), 1)

    def test_fold_terminal_deny_not_active(self):
        """Terminal deny is not in active denies."""
        event = make_event(deny_id="term-fold-1")
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        self.assertTrue(r1.appended)
        life = make_lifecycle_request(deny_id="term-fold-1")
        r2 = append_lifecycle_entry(r1.ledger, life)
        self.assertTrue(r2.appended)
        result = fold_effective_denies(r2.ledger)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.active_denies), 0)


# ============================================================
# Test: Hash and payload
# ============================================================

class TestHashBuilding(unittest.TestCase):

    def test_event_hash_placeholder_to_final(self):
        """Event hash transitions from placeholder to final."""
        event = make_event(event_hash=HASH_PLACEHOLDER)
        payload = deny_event_payload(event)
        final_hash = sha256_hex(payload)
        self.assertNotEqual(final_hash, HASH_PLACEHOLDER)
        self.assertEqual(len(final_hash), 64)

    def test_entry_hash_covers_event_hash(self):
        """Entry hash covers event_hash transitively."""
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=make_event()))
        self.assertTrue(r1.appended)
        entry = r1.entry
        entry_payload = deny_ledger_entry_payload(entry)
        self.assertIn(entry.event.event_hash, str(entry_payload))

    def test_empty_hash_not_used(self):
        """Empty string hash placeholder not used in final result."""
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=make_event()))
        self.assertTrue(r1.appended)
        self.assertNotEqual(r1.entry.event.event_hash, "")
        self.assertNotEqual(r1.entry.entry_hash, "")

    def test_persistent_from_policy_created(self):
        """Entry persistent flag from CREATED request (PERSISTENT_POLICY scope)."""
        r1 = create_deny_entry(
            DenyLedger(),
            make_creation_request(event=make_event(deny_scope=DenyScope.PERSISTENT_POLICY), persistent=True),
        )
        self.assertTrue(r1.appended)
        self.assertTrue(r1.entry.persistent)
        # request_id only expected with CURRENT_ACTION scope
        self.assertIsNone(r1.entry.request_id)

    def test_request_id_from_action_created(self):
        """Entry request_id from CREATED request (CURRENT_ACTION scope)."""
        r1 = create_deny_entry(
            DenyLedger(),
            make_creation_request(event=make_event(deny_scope=DenyScope.CURRENT_ACTION), request_id="req-42"),
        )
        self.assertTrue(r1.appended)
        self.assertEqual(r1.entry.request_id, "req-42")


# ============================================================
# Test: validate_deny_lifecycle_request
# ============================================================

class TestValidateDenyLifecycleRequest(unittest.TestCase):

    def test_lifecycle_deny_created_rejected(self):
        """DENY_CREATED as lifecycle event → rejected by DenyLifecycleRequest."""
        with self.assertRaises(ValueError):
            make_lifecycle_request(
                deny_id="vlc-1",
                event_type=DenyEventType.DENY_CREATED,
            )

    def test_approval_id_empty_string_rejected(self):
        """Empty approval_id string → rejected by DenyLifecycleRequest."""
        with self.assertRaises(ValueError):
            make_lifecycle_request(
                deny_id="vla-1",
                approval_id="",
            )

    def test_approval_id_none_allowed(self):
        """approval_id=None → allowed."""
        event = make_event(deny_id="vlan-1")
        r1 = create_deny_entry(DenyLedger(), make_creation_request(event=event))
        life = make_lifecycle_request(
            deny_id="vlan-1",
            approval_id=None,
        )
        result = validate_deny_lifecycle_request(
            r1.ledger.entries[0], r1.ledger.entries[0],
            r1.ledger.entries, life,
        )
        self.assertTrue(result.valid)

    def test_naive_occurred_at_rejected(self):
        """Naive occurred_at → rejected by DenyLifecycleRequest."""
        with self.assertRaises(ValueError):
            make_lifecycle_request(
                deny_id="vlna-1",
                occurred_at=datetime(2026, 1, 1),
            )


# ============================================================
# Test: require_aware_datetime in common paths
# ============================================================

class TestRequireAwareDatetimeCommon(unittest.TestCase):

    def test_creation_occurred_at_naive_rejected(self):
        """validate_deny_creation rejects naive occurred_at."""
        event = _raw_event(occurred_at=datetime(2026, 1, 1))
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)
        self.assertIn("deny_occurred_at_naive", result.failed_checks)

    def test_creation_expires_at_naive_rejected(self):
        """validate_deny_creation rejects naive expires_at."""
        event = _raw_event(expires_at=datetime(2026, 1, 1))
        request = _raw_creation_request(event=event)
        result = validate_deny_creation(request)
        self.assertFalse(result.valid)
        self.assertIn("deny_expires_at_naive", result.failed_checks)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    unittest.main()
