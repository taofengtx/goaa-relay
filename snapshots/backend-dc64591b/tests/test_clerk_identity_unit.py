"""Pure unit tests for the Clerk -> GOAA identity mapping rules.

These tests are deliberately database-free and network-free: the connection
factory is injected, so nothing here opens a socket. They pin the rules that
the candidate claims:

* an already-mapped ``(issuer, subject)`` is served from the local tables
  alone — never a per-request Clerk Backend API call;
* a *new* identity reads at most one verified address, and a failed read just
  leaves the column NULL;
* a verified address owned by somebody else refuses the log-in outright:
  no merge, no re-bind, and no second NULL-address account;
* a unique violation is classified by its *exact* constraint — only the
  ``(issuer, subject)`` index means "lost a race" (re-read in a new
  transaction), and an unrecognised one is neither an e-mail clash nor a retry;
* the refusal is audited, masked, in its own transaction, and a failing audit
  still refuses.

They must be run with ``--noconftest`` so the repository's ``conftest.py``
(session-scoped ``prepared_database`` autouse fixture, which drops and rebuilds
``schema public``) can never run.
"""

from __future__ import annotations

import pytest

import psycopg

from app import clerk_identity


# --------------------------------------------------------------------------- #
# A scripted stand-in for a psycopg connection: no server, no socket.
# --------------------------------------------------------------------------- #


class UniqueViolation(psycopg.errors.UniqueViolation):
    """A unique violation that reports its constraint the way the server does."""

    def __init__(self, constraint: str) -> None:
        super().__init__(f'duplicate key value violates unique constraint "{constraint}"')


class _Cursor:
    def __init__(self, conn: "_Conn") -> None:
        self._conn = conn

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._conn.execute(sql, params)

    def fetchone(self):
        return self._conn.last_row

    def fetchall(self):
        return self._conn.last_rows

    @property
    def rowcount(self) -> int:
        return self._conn.rowcount


class _Conn:
    """Answers exactly the statements ``clerk_identity`` issues."""

    def __init__(self, *, mapped: dict | None = None, user: dict | None = None,
                 roles: list[str] | None = None, fail_on: dict[str, Exception] | None = None,
                 label: str = "conn") -> None:
        self.mapped = mapped
        self.user = user
        self.roles = list(roles or [])
        self.fail_on = dict(fail_on or {})
        self.label = label
        self.calls: list[tuple[str, tuple]] = []
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.savedpoints = 0
        self.last_rows: list = []
        self.rowcount = 1
        self.created_user_id = "created-user-1"

    # -- helpers ----------------------------------------------------------- #
    @property
    def last_row(self):
        sql = self._current
        if "from user_identities where issuer" in sql:
            return self.mapped
        if "from users u where" in sql:
            return self.user
        if "insert into users" in sql:
            return {"id": self.created_user_id}
        return None

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._current = sql
        self.calls.append((sql, params))
        for needle, error in self.fail_on.items():
            if needle in sql:
                raise error
        if "select role from user_roles" in sql:
            self.last_rows = [{"role": r} for r in self.roles]
        else:
            self.last_rows = []

    def cursor(self) -> _Cursor:
        return _Cursor(self)

    def transaction(self):
        conn = self

        class _Savepoint:
            def __enter__(self_inner):
                conn.savedpoints += 1
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        return _Savepoint()

    # -- assertions helpers ------------------------------------------------ #
    def sql_seen(self, needle: str) -> list[tuple]:
        return [c for c in self.calls if needle in c[0]]


class _Factory:
    """Mimics ``db.connection()``: commits on success, rolls back on error."""

    def __init__(self, *conns: _Conn) -> None:
        self.queue = list(conns)
        self.opened: list[_Conn] = []

    def __call__(self):
        conn = self.queue.pop(0) if self.queue else _Conn(label=f"extra-{len(self.opened)}")
        self.opened.append(conn)
        factory = self

        class _Ctx:
            def __enter__(self_inner) -> _Conn:
                return conn

            def __exit__(self_inner, exc_type, exc, tb) -> bool:
                if exc_type is None:
                    conn.committed = True
                else:
                    conn.rolled_back = True
                conn.closed = True
                factory.queue.append(conn)
                return False

        return _Ctx()


def factory_for(*conns: _Conn) -> _Factory:
    return _Factory(*conns)


def provider(value):
    """A verified-address provider that counts how often it is called."""

    calls: list[int] = []

    def _provider():
        calls.append(1)
        if isinstance(value, Exception):
            raise value
        return value

    _provider.calls = calls  # type: ignore[attr-defined]
    return _provider


SETTINGS = object()


# --------------------------------------------------------------------------- #
# Already mapped: local tables only.
# --------------------------------------------------------------------------- #


def test_existing_mapping_is_served_from_the_local_tables():
    conn = _Conn(mapped={"user_id": "u-1"},
                 user={"id": "u-1", "email": "a@b.test", "full_name": None,
                       "phone": None, "email_verified_at": None, "created_at": None},
                 roles=["user", "agent"])
    provider_ = provider(AssertionError("must not be consulted"))
    factory = factory_for(conn)

    user = clerk_identity.resolve_clerk_user(
        SETTINGS, issuer="https://iss.test", subject="sub-1",
        email_provider=provider_, connect=factory,
    )

    assert user["user_id"] == "u-1"
    assert user["roles"] == ["user", "agent"]
    assert provider_.calls == [], "an existing mapping must not call Clerk again"
    assert conn.sql_seen("insert into") == [], "an existing mapping must not write"
    assert conn.committed is True
    assert len(factory.opened) == 1


def test_roles_are_never_taken_from_the_token_claim():
    conn = _Conn(mapped={"user_id": "u-1"},
                 user={"id": "u-1", "email": None, "full_name": None, "phone": None,
                       "email_verified_at": None, "created_at": None},
                 roles=["user"])
    user = clerk_identity.resolve_clerk_user(
        SETTINGS, issuer="https://iss.test", subject="sub-1", connect=factory_for(conn),
    )
    assert user["roles"] == ["user"], "roles come from user_roles only"


# --------------------------------------------------------------------------- #
# First log-in: just-in-time creation.
# --------------------------------------------------------------------------- #


def test_first_login_creates_a_credential_less_user_with_the_default_role():
    conn = _Conn(user={"id": "created-1", "email": None, "full_name": None, "phone": None,
                       "email_verified_at": None, "created_at": None}, roles=["user"])
    provider_ = provider("new@example.test")

    user = clerk_identity.resolve_clerk_user(
        SETTINGS, issuer="https://iss.test", subject="sub-new",
        email_provider=provider_, connect=factory_for(conn),
    )

    assert provider_.calls == [1], "the verified address is read once, on creation only"
    users_insert = conn.sql_seen("insert into users")
    assert len(users_insert) == 1
    assert "password_hash" in users_insert[0][0]
    assert users_insert[0][1] == ("new@example.test", "new@example.test")
    assert conn.sql_seen("insert into user_roles")[0][1] == (conn.created_user_id, "user")
    identity_insert = conn.sql_seen("insert into user_identities")
    assert identity_insert[0][1] == (
        conn.created_user_id, "https://iss.test", "sub-new", "new@example.test", True,
    )
    assert user["roles"] == ["user"]
    assert conn.committed is True
    assert conn.rolled_back is False


def test_first_login_tolerate_a_failed_verified_email_read():
    conn = _Conn(user={"id": "created-1", "email": None, "full_name": None, "phone": None,
                       "email_verified_at": None, "created_at": None}, roles=["user"])
    provider_ = provider(RuntimeError("clerk backend unreachable"))

    clerk_identity.resolve_clerk_user(
        SETTINGS, issuer="https://iss.test", subject="sub-new",
        email_provider=provider_, connect=factory_for(conn),
    )

    assert conn.sql_seen("insert into users")[0][1] == (None, None)
    assert conn.sql_seen("insert into user_identities")[0][1][3] is None
    assert conn.committed is True


def test_blank_subject_is_refused_without_touching_anything():
    provider_ = provider("x@example.test")
    factory = factory_for()
    with pytest.raises(clerk_identity.IdentityError):
        clerk_identity.resolve_clerk_user(
            SETTINGS, issuer="https://iss.test", subject="   ",
            email_provider=provider_, connect=factory,
        )
    assert factory.opened == []
    assert provider_.calls == []


# --------------------------------------------------------------------------- #
# Verified address already owned: refuse, never merge, never a NULL account.
# --------------------------------------------------------------------------- #


def test_verified_email_owned_elsewhere_refuses_the_login():
    create = _Conn(fail_on={"insert into users": UniqueViolation("users_email_lower_key")})
    audit = _Conn()
    factory = factory_for(create, audit)
    provider_ = provider("shared@example.test")

    with pytest.raises(clerk_identity.IdentityConflict) as excinfo:
        clerk_identity.resolve_clerk_user(
            SETTINGS, issuer="https://iss.test", subject="sub-x",
            email_provider=provider_, connect=factory,
        )

    assert "already bound" in str(excinfo.value)
    assert create.rolled_back is True, "the failed creation must roll back"
    assert create.sql_seen("insert into user_identities") == [], (
        "no second account may be created after the address clash"
    )
    assert create.sql_seen("insert into users")[0][1][0] == "shared@example.test", (
        "the address is never silently downgraded to NULL"
    )


def test_the_refusal_is_audited_in_its_own_transaction_and_masked():
    create = _Conn(fail_on={"insert into users": UniqueViolation("users_email_lower_key")})
    audit = _Conn()
    factory = factory_for(create, audit)

    with pytest.raises(clerk_identity.IdentityConflict):
        clerk_identity.resolve_clerk_user(
            SETTINGS, issuer="https://iss.test", subject="sub-x",
            email_provider=provider("shared@example.test"), connect=factory,
        )

    assert len(factory.opened) == 2, "the audit must not share the rolled back transaction"
    assert audit is factory.opened[1]
    events = audit.sql_seen("insert into identity_events")
    assert len(events) == 1
    params = events[0][1]
    assert params[0] == "identity.conflict"
    assert params[4] == "s****d@example.test", f"expected a masked address, got {params[4]!r}"
    assert "shared@example.test" not in str(params)
    assert audit.committed is True


def test_a_failing_audit_still_refuses_the_login():
    create = _Conn(fail_on={"insert into users": UniqueViolation("users_email_lower_key")})
    audit = _Conn(fail_on={"insert into identity_events": RuntimeError("audit table gone")})
    factory = factory_for(create, audit)

    with pytest.raises(clerk_identity.IdentityConflict):
        clerk_identity.resolve_clerk_user(
            SETTINGS, issuer="https://iss.test", subject="sub-x",
            email_provider=provider("shared@example.test"), connect=factory,
        )
    assert audit.rolled_back is True


# --------------------------------------------------------------------------- #
# Unique violations: classified precisely, never blanket-retried.
# --------------------------------------------------------------------------- #


def test_issuer_subject_race_re_reads_in_a_new_transaction():
    first = _Conn(fail_on={"insert into user_identities":
                           UniqueViolation("user_identities_issuer_subject_key")})
    second = _Conn(mapped={"user_id": "u-9"},
                   user={"id": "u-9", "email": None, "full_name": None, "phone": None,
                         "email_verified_at": None, "created_at": None}, roles=["user"])
    factory = factory_for(first, second)
    provider_ = provider("race@example.test")

    user = clerk_identity.resolve_clerk_user(
        SETTINGS, issuer="https://iss.test", subject="sub-race",
        email_provider=provider_, connect=factory,
    )

    assert user["user_id"] == "u-9"
    assert first.rolled_back is True
    assert len(factory.opened) == 2, "exactly one re-read, no loop"
    assert provider_.calls == [1], "the address lookup is memoised across the retry"


def test_an_unknown_unique_violation_is_not_an_email_conflict_and_is_not_retried():
    create = _Conn(fail_on={"insert into users": UniqueViolation("some_other_unique_index")})
    audit = _Conn()
    factory = factory_for(create, audit)

    with pytest.raises(clerk_identity.IdentityConflict) as excinfo:
        clerk_identity.resolve_clerk_user(
            SETTINGS, issuer="https://iss.test", subject="sub-y",
            email_provider=provider("plain@example.test"), connect=factory,
        )

    assert "unexpected unique violation" in str(excinfo.value)
    assert "already bound" not in str(excinfo.value)
    assert len(factory.opened) == 2, "only the refused transaction plus its audit"
    assert create.rolled_back is True
    assert create.sql_seen("insert into user_identities") == []


def test_constraint_name_is_read_from_the_diagnostic_when_present():
    class Diag:
        constraint_name = "user_identities_issuer_subject_key"

    class DiagError(psycopg.errors.UniqueViolation):
        diag = Diag()

    error = DiagError("no constraint name in this message")
    assert clerk_identity._constraint_name(error) == "user_identities_issuer_subject_key"
    assert clerk_identity._constraint_name(UniqueViolation("users_email_lower_key")) == "users_email_lower_key"
    assert clerk_identity._constraint_name(RuntimeError("nothing to see")) is None


def test_unknown_constraint_is_refused_rather_than_retried_forever():
    class Diag:
        constraint_name = None

    create = _Conn(fail_on={"insert into user_identities":
                            UniqueViolation("user_identities_user_provider_key")})
    audit = _Conn()
    with pytest.raises(clerk_identity.IdentityConflict):
        clerk_identity.resolve_clerk_user(
            SETTINGS, issuer="https://iss.test", subject="sub-z",
            email_provider=provider(None), connect=factory_for(create, audit),
        )
    assert create.rolled_back is True
