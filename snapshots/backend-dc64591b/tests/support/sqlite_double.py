"""A tiny SQLite double for the PostgreSQL shapes the bridge uses.

Honest label: this is **not** PostgreSQL and proves nothing about PostgreSQL.
What it does prove is that the bridge's *logic* — link once, rotate, revoke,
refuse — holds row by row, with the same unique constraints, the same
``CHECK`` lists, the same append-only trigger and the same one-to-one links as
the real schema. The real migration (0006) is the file delivered for the
database; this double only lets the lifecycle be exercised with **zero**
database and **zero** network access.

Design notes:
  * rows come back as dicts (``fetch_one``/``fetch_all`` expect that);
  * ``conn.transaction()`` maps onto SQLite savepoints, so a failed inner
    block leaves the outer transaction usable — the same behaviour the real
    savepoint-based code relies on;
  * ``gen_random_uuid()`` is replaced by a fresh uuid4 literal, because SQLite
    cannot put a function call in a column default;
  * timestamps round-trip as aware ``datetime`` objects.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

sqlite3.register_adapter(datetime, lambda value: value.isoformat())
sqlite3.register_converter("timestamptz", lambda raw: datetime.fromisoformat(raw.decode()))


#: SQLite's stand-in for ``default gen_random_uuid()``: the classic
#: ``hex(randomblob(...))`` uuid4 expression (SQLite allows a function call in a
#: column default, PostgreSQL gets the real thing).
UUID_DEFAULT = (
    "default (lower("
    "hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || "
    "substr(hex(randomblob(2)), 2) || '-' || substr('89ab', abs(random()) % 4 + 1, 1) || "
    "substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6))))"
)


SCHEMA_TEMPLATE = """
pragma foreign_keys = on;

-- mirrors 0005 (identity side) ---------------------------------------------
create table users (
    id                text primary key @UUID_DEFAULT@,
    email             text,
    full_name         text,
    phone             text,
    address           text,
    password_hash     text,
    email_verified_at timestamptz,
    created_at        timestamptz not null,
    updated_at        timestamptz not null
);

-- mirrors 0005: `users_email_lower_key` unique (lower(email)); multiple NULLs
-- are allowed, two identical addresses are not.
create unique index users_email_lower_key on users (lower(email));

create table user_roles (
    user_id text not null references users (id) on delete cascade,
    role    text not null,
    primary key (user_id, role)
);

create table user_identities (
    id             text primary key @UUID_DEFAULT@,
    user_id        text not null references users (id) on delete cascade,
    provider       text not null default 'clerk',
    issuer         text not null,
    subject        text not null,
    email_snapshot text,
    email_verified integer not null default 0,
    created_at     timestamptz not null,
    updated_at     timestamptz not null,
    constraint user_identities_issuer_subject_key unique (issuer, subject),
    constraint user_identities_user_provider_key unique (user_id, provider)
);

create table identity_events (
    id              text primary key @UUID_DEFAULT@,
    occurred_at     timestamptz not null default (strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')),
    event_type      text not null,
    actor_user_id   text,
    subject_user_id text references users (id) on delete set null,
    provider        text,
    issuer          text,
    subject         text,
    email_masked    text,
    detail          text not null default '{}',
    constraint identity_events_type_known check (
        event_type in (
            'identity.jit_create',
            'identity.bind',
            'identity.unbind',
            'identity.conflict',
            'identity.identifier_snapshot',
            'identity.recovery',
            'business.subject_linked',
            'business.token_issued',
            'business.token_revoked',
            'business.token_rejected'
        )
    ),
    constraint identity_events_detail_is_object check (json_valid(detail))
);

-- mirrors 0005: append-only, enforced by the database (SQLite allows one
-- event per trigger, hence the two triggers for the single PostgreSQL one)
create trigger trg_identity_events_append_only_upd
    before update on identity_events
    begin
        select raise(abort, 'identity_events is append-only');
    end;

create trigger trg_identity_events_append_only_del
    before delete on identity_events
    begin
        select raise(abort, 'identity_events is append-only');
    end;

-- mirrors 0006 (business side) ---------------------------------------------
create table business_subjects (
    id         text primary key @UUID_DEFAULT@,
    kind       text not null default 'customer',
    created_at timestamptz not null default (strftime('%Y-%m-%dT%H:%M:%f+00:00','now')),
    updated_at timestamptz not null default (strftime('%Y-%m-%dT%H:%M:%f+00:00','now')),
    constraint business_subjects_kind_known check (kind in ('customer'))
);

create table business_subject_links (
    user_id    text primary key references users (id) on delete cascade,
    subject_id text not null unique references business_subjects (id) on delete cascade,
    linked_via text not null default 'clerk_issuer_subject',
    issuer     text not null,
    subject    text not null,
    created_at timestamptz not null default (strftime('%Y-%m-%dT%H:%M:%f+00:00','now')),
    constraint business_subject_links_via_known check (linked_via in ('clerk_issuer_subject'))
);

create table business_tokens (
    id           text primary key @UUID_DEFAULT@,
    user_id      text not null references business_subjects (id) on delete cascade,
    token        text not null unique,
    role         text not null,
    created_at   timestamptz not null default (strftime('%Y-%m-%dT%H:%M:%f+00:00','now')),
    issued_at    timestamptz not null default (strftime('%Y-%m-%dT%H:%M:%f+00:00','now')),
    last_used_at timestamptz,
    revoked_at   timestamptz,
    constraint business_tokens_role_known check (role in ('customer')),
    constraint business_tokens_user_token_key unique (user_id, token)
);
"""

SCHEMA = SCHEMA_TEMPLATE.replace("@UUID_DEFAULT@", UUID_DEFAULT)


class DoubleCursor:
    """psycopg-shaped cursor over a SQLite cursor."""

    def __init__(self, connection: "DoubleConnection") -> None:
        self._connection = connection
        self._cursor = connection.raw.cursor()
        self.rowcount = -1

    # -- psycopg surface ----------------------------------------------------
    def execute(self, sql: str, params: Iterable[Any] = ()) -> "DoubleCursor":
        statement = translate(sql)
        self.rowcount = -1
        if "pg_advisory_xact_lock" in statement:
            # The real statement takes a transaction-scoped lock. Serialising
            # concurrent writers is a PostgreSQL concern; the double has one
            # writer, so the lock is a documented no-op here.
            self._cursor.execute("select 1 where 0")
            self.rowcount = 1
            return self
        if "gen_random_uuid()" in statement:
            statement = statement.replace("gen_random_uuid()", f"'{uuid.uuid4()}'")
        self._cursor.execute(statement, tuple(params))
        self.rowcount = self._cursor.rowcount
        return self

    def fetchone(self) -> dict[str, Any] | None:
        row = self._cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._cursor.fetchall()]

    def close(self) -> None:
        self._cursor.close()

    def __enter__(self) -> "DoubleCursor":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class _Transaction:
    """``with conn.transaction():`` -> a savepoint that can be undone alone."""

    def __init__(self, connection: "DoubleConnection") -> None:
        self._connection = connection
        self._name = f"sp_{uuid.uuid4().hex[:12]}"

    def __enter__(self) -> "_Transaction":
        self._connection.raw.execute(f"savepoint {self._name}")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if exc_type is None:
            self._connection.raw.execute(f"release {self._name}")
        else:
            self._connection.raw.execute(f"rollback to {self._name}")
            self._connection.raw.execute(f"release {self._name}")
        return False


class DoubleConnection:
    """psycopg-shaped connection, backed by SQLite."""

    def __init__(self, raw: sqlite3.Connection) -> None:
        self.raw = raw

    def cursor(self) -> DoubleCursor:
        return DoubleCursor(self)

    def transaction(self) -> _Transaction:
        return _Transaction(self)

    def commit(self) -> None:
        self.raw.commit()

    def rollback(self) -> None:
        self.raw.rollback()

    def close(self) -> None:
        self.raw.close()

    def __enter__(self) -> "DoubleConnection":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def translate(sql: str) -> str:
    """``%s`` (and the casts used with it) -> SQLite's ``?``.

    SQL that already speaks ``?`` (the test helpers) passes through untouched;
    a statement that mixes both styles is rejected instead of guessed at.
    """

    if "%s" not in sql:
        return sql
    out = sql.replace("%s::jsonb", "?").replace("%s::text", "?").replace("%s", "?")
    if out.count("?") != sql.count("%s"):
        raise AssertionError("placeholder translation mismatch")
    return out


def connect() -> DoubleConnection:
    """A fresh in-memory database with the mirrored schema applied."""

    raw = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
    raw.row_factory = lambda cursor, row: {
        column[0]: row[index] for index, column in enumerate(cursor.description)
    }
    raw.executescript(SCHEMA)
    return DoubleConnection(raw)


def seed_identity(
    conn: DoubleConnection,
    *,
    user_id: str,
    subject: str,
    issuer: str = "https://clerk.example.dev",
    email: str | None = "someone@example.com",
) -> str:
    """Seed a ``users`` row plus its Clerk mapping — what 0005 leaves behind."""

    now = datetime(2026, 9, 11, 1, 0, 0, tzinfo=timezone.utc)
    with DoubleCursor(conn) as cur:
        cur.execute(
            "insert into users (id, email, created_at, updated_at) values (?, ?, ?, ?)",
            (user_id, email, now, now),
        )
        cur.execute("insert into user_roles (user_id, role) values (?, 'user')", (user_id,))
        cur.execute(
            "insert into user_identities "
            "(id, user_id, provider, issuer, subject, email_snapshot, email_verified, created_at, updated_at) "
            "values (?, ?, 'clerk', ?, ?, ?, 1, ?, ?)",
            (str(uuid.uuid4()), user_id, issuer, subject, email, now, now),
        )
    conn.commit()
    return user_id


def count(conn: DoubleConnection, table: str, where: str = "", params: tuple[Any, ...] = ()) -> int:
    with DoubleCursor(conn) as cur:
        cur.execute(f"select count(*) as n from {table} {where}", params)
        return int(cur.fetchone()["n"])
