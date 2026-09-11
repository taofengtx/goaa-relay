"""Clerk subject -> local GOAA user mapping (just-in-time provisioning).

The mapping key is **only** ``(issuer, subject)``. An e-mail address or a phone
number is never used to find, merge or adopt an existing account: a shared
address is not proof of the same person, and Clerk's own documentation warns
against it. Anything that looks like "the same human" but arrives through a
different key fails closed and is recorded as ``identity.conflict``.

The created account is deliberately credential-less: ``password_hash`` stays
``NULL`` and ``email`` is only ever filled from the *verified* primary address
read back from the Clerk Backend API (or left ``NULL``). Roles are read from
the local database, never from a token claim, so a fresh identity starts with
exactly the same default role the legacy registration path grants.

A verified address is still **not** an identity key. When it already belongs to
another account the log-in is *refused* as ``identity.conflict``: the accounts
are never merged, the address is never re-bound, and no second account with a
NULL address is created as a workaround. The refusal is recorded, masked, in
its own transaction so it survives the rollback of the failed one.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable

import psycopg

from .db import connection, execute, fetch_all, fetch_one
from .security import mask_email

logger = logging.getLogger("goaa.c2.loop.clerk_identity")

#: The default role granted by the legacy ``/auth/register`` path. A
#: just-in-time Clerk identity gets exactly this and nothing more.
DEFAULT_ROLE = "user"

_EVENT_JIT_CREATE = "identity.jit_create"
_EVENT_CONFLICT = "identity.conflict"
_EVENT_SNAPSHOT = "identity.identifier_snapshot"

_USER_COLUMNS = "u.id, u.email, u.full_name, u.phone, u.email_verified_at, u.created_at"

#: Exact constraint names (migration 0001 / 0005), so a unique violation is
#: classified by what it actually violated instead of being lumped into
#: "probably the e-mail".
_UNIQUE_ISSUER_SUBJECT = "user_identities_issuer_subject_key"
_UNIQUE_USER_PROVIDER = "user_identities_user_provider_key"
_UNIQUE_USER_EMAIL = "users_email_lower_key"


class IdentityError(Exception):
    """Base class for identity-mapping failures."""


class IdentityConflict(IdentityError):
    """The identity or one of its identifiers is already owned elsewhere.

    The whole log-in is refused: nothing is merged, nothing is re-bound, and no
    replacement account is created either.
    """

    def __init__(self, message: str, *, email: str | None = None) -> None:
        super().__init__(message)
        self.email = email


class IdentityRace(IdentityError):
    """Another transaction created the same ``(issuer, subject)`` first."""


class _EmailCollision(Exception):
    """Internal: the verified e-mail snapshot belongs to another account."""

    def __init__(self, constraint: str) -> None:
        super().__init__(constraint)
        self.constraint = constraint

def _constraint_name(exc: Exception) -> str | None:
    """The violated constraint/index name, if the driver reported one."""

    diag = getattr(exc, "diag", None)
    name = getattr(diag, "constraint_name", None)
    if isinstance(name, str) and name:
        return name
    # psycopg only fills diag when the server sends the fields; fall back to
    # the message so a missing constraint name never silently becomes "e-mail".
    match = re.search(r'constraint "([^"]+)"', str(exc))
    return match.group(1) if match else None

def _read_verified_email(email_provider: Callable[[], str | None] | None) -> str | None:
    """Best-effort verified primary address for a *new* identity."""

    if email_provider is None:
        return None
    try:
        value = email_provider()
    except Exception as exc:  # noqa: BLE001 - a failed lookup keeps the column NULL
        logger.warning("could not read the verified primary e-mail: %s", type(exc).__name__)
        return None
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None

def _memoise_provider(
    email_provider: Callable[[], str | None] | None,
) -> Callable[[], str | None] | None:
    """At most one verified-address lookup per log-in, even across a retry."""

    if email_provider is None:
        return None
    cache: dict[str, Any] = {"done": False, "value": None}

    def once() -> str | None:
        if not cache["done"]:
            cache["done"] = True
            cache["value"] = email_provider()
        return cache["value"]

    return once


def _roles(conn: psycopg.Connection, user_id: str) -> list[str]:
    rows = fetch_all(conn, "select role from user_roles where user_id = %s order by role", (user_id,))
    return [row["role"] for row in rows]


def load_user(conn: psycopg.Connection, user_id: str) -> dict[str, Any] | None:
    row = fetch_one(conn, f"select {_USER_COLUMNS} from users u where u.id = %s", (user_id,))
    if row is None:
        return None
    user = dict(row)
    user["user_id"] = str(user["id"])
    user["roles"] = _roles(conn, user_id)
    return user


def _record(
    conn: psycopg.Connection,
    event_type: str,
    *,
    subject_user_id: str | None,
    issuer: str,
    subject: str | None,
    email: str | None,
    detail: dict[str, Any] | None = None,
) -> None:
    import json

    with conn.cursor() as cur:
        cur.execute(
            "insert into identity_events "
            "(event_type, subject_user_id, provider, issuer, subject, email_masked, detail) "
            "values (%s, %s, 'clerk', %s, %s, %s, %s::jsonb)",
            (
                event_type,
                subject_user_id,
                issuer,
                subject,
                mask_email(email) if email else None,
                json.dumps(detail or {}),
            ),
        )



def resolve_or_create(
    conn: psycopg.Connection,
    *,
    issuer: str,
    subject: str,
    email_provider: Callable[[], str | None] | None = None,
) -> dict[str, Any]:
    """Return the local user bound to ``(issuer, subject)``, creating it once.

    Runs inside the caller's transaction. ``email_provider`` is called **only**
    when a brand new identity has to be created, so an already-mapped caller
    never triggers a Clerk Backend API round trip.

    Raises :class:`IdentityRace` when a concurrent transaction created the same
    mapping first (the caller re-reads in a fresh transaction), and
    :class:`IdentityConflict` when the verified address already belongs to
    another account — in that case nothing at all is created.
    """

    if not issuer or not subject or not subject.strip():
        raise IdentityError("issuer and subject are required")
    subject = subject.strip()

    # Serialise first logins for this exact identity so that a double-submit
    # cannot produce two users. The lock is released with the transaction.
    fetch_one(
        conn,
        "select pg_advisory_xact_lock(hashtextextended(%s::text, 0::bigint))",
        (f"{issuer}|{subject}",),
    )

    existing = fetch_one(
        conn,
        "select user_id from user_identities where issuer = %s and subject = %s",
        (issuer, subject),
    )
    if existing is not None:
        # Already mapped: read the local mapping and the local roles. No token
        # claim, no browser claim and no per-request Clerk call is involved.
        user = load_user(conn, str(existing["user_id"]))
        if user is None:
            raise IdentityConflict("the mapped user no longer exists")
        return user

    # First log-in for this identity. This is the only place a verified address
    # is read, and a read failure just leaves the column NULL.
    snapshot_email = _read_verified_email(email_provider)

    try:
        user_id = _insert_new_identity(
            conn, issuer=issuer, subject=subject, snapshot_email=snapshot_email
        )
    except psycopg.errors.UniqueViolation as exc:
        try:
            _classify_unique_violation(exc)
        except _EmailCollision as collision:
            # Python does not route an exception raised inside a handler to the
            # sibling ``except`` clauses, so the address collision has to be
            # translated here as well as below.
            raise _email_conflict(collision, snapshot_email) from collision
    except IdentityRace:
        raise
    except _EmailCollision as exc:
        raise _email_conflict(exc, snapshot_email) from exc

    return load_user(conn, user_id)


def _email_conflict(collision: _EmailCollision, snapshot_email: str | None) -> IdentityConflict:
    """The public refusal for a verified address that another account holds."""

    return IdentityConflict(
        f"the verified e-mail is already bound to another account ({collision.constraint})",
        email=snapshot_email,
    )


def _insert_new_identity(
    conn: psycopg.Connection,
    *,
    issuer: str,
    subject: str,
    snapshot_email: str | None,
) -> str:
    """Create the credential-less user plus its Clerk mapping, or classify why not.

    The insert runs inside a savepoint so a unique violation leaves the caller's
    transaction usable for the audit read; the violation is then classified by
    the **exact** constraint it hit.
    """

    with conn.transaction():
        row = fetch_one(
            conn,
            "insert into users (email, password_hash, email_verified_at) "
            # the second parameter is only tested for NULL: without an explicit
            # cast PostgreSQL cannot infer its type and the insert fails with
            # IndeterminateDatatype ("could not determine data type of parameter $2")
            "values (%s, null, case when %s::text is null then null else now() end) returning id",
            (snapshot_email, snapshot_email),
        )
        user_id = str(row["id"])
        # "on conflict do nothing" has no RETURNING clause: the statement yields
        # no result set, so fetch_one() would raise "the last operation didn't
        # produce a result". The row is only required to exist, so use execute().
        execute(
            conn,
            "insert into user_roles (user_id, role) values (%s, %s) on conflict do nothing",
            (user_id, DEFAULT_ROLE),
        )
        fetch_one(
            conn,
            "insert into user_identities (user_id, provider, issuer, subject, email_snapshot, email_verified) "
            "values (%s, 'clerk', %s, %s, %s, %s) returning id",
            (user_id, issuer, subject, snapshot_email, snapshot_email is not None),
        )
        _record(
            conn,
            _EVENT_JIT_CREATE,
            subject_user_id=user_id,
            issuer=issuer,
            subject=subject,
            email=snapshot_email,
            detail={"role": DEFAULT_ROLE, "email": "verified" if snapshot_email else "absent"},
        )
    return user_id


def _classify_unique_violation(exc: psycopg.errors.UniqueViolation) -> None:
    """Turn a unique violation into the *precise* reason, or refuse outright.

    Never blanket-treats a unique violation as an e-mail clash, and never
    auto-retries: only the ``(issuer, subject)`` index means "another request
    won the race", and only ``users_email_lower_key`` means "address taken".
    """

    constraint = _constraint_name(exc)
    if constraint == _UNIQUE_ISSUER_SUBJECT:
        raise IdentityRace("this identity was created concurrently") from exc
    if constraint == _UNIQUE_USER_EMAIL:
        raise _EmailCollision(constraint) from exc
    raise IdentityConflict(
        f"unexpected unique violation on {constraint or 'an unnamed constraint'}"
    ) from exc



def _audit_conflict(
    settings: Any,
    *,
    issuer: str,
    subject: str,
    email: str | None = None,
    detail: dict[str, Any] | None = None,
    connect: Callable[[], Any] | None = None,
) -> None:
    """Record a refused log-in in its own transaction.

    The address is masked by ``_record``; the caller's transaction has already
    rolled back, so this must not share it. A failure here is logged and the
    log-in stays refused either way.
    """

    try:
        if connect is not None:
            with connect() as conn:
                _record(
                    conn,
                    _EVENT_CONFLICT,
                    subject_user_id=None,
                    issuer=issuer,
                    subject=subject,
                    email=email,
                    detail=detail or {},
                )
        else:
            with connection(settings, autocommit=True) as conn:
                _record(
                    conn,
                    _EVENT_CONFLICT,
                    subject_user_id=None,
                    issuer=issuer,
                    subject=subject,
                    email=email,
                    detail=detail or {},
                )
    except Exception as exc:  # noqa: BLE001 - the log-in is already refused
        logger.warning("could not record the identity conflict: %s", type(exc).__name__)


def resolve_clerk_user(
    settings: Any,
    *,
    issuer: str,
    subject: str,
    email_provider: Callable[[], str | None] | None = None,
    connect: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Map a *verified* ``(issuer, subject)`` to a local user.

    ``connect`` is injectable so the mapping rules can be unit-tested without a
    database. Every attempt runs in its own transaction, so a rolled back
    attempt can never leave a half-created account behind.
    """

    # Refuse obviously unusable input before a connection is even opened: a
    # blank subject can never be mapped, and it must not consume a connection.
    if not issuer or not subject or not subject.strip():
        raise IdentityError("issuer and subject are required")

    factory = connect or (lambda: connection(settings))
    provider = _memoise_provider(email_provider)

    try:
        with factory() as conn:
            return resolve_or_create(conn, issuer=issuer, subject=subject, email_provider=provider)
    except IdentityRace:
        # Only the exact (issuer, subject) unique index leads here. Re-read in a
        # *new* transaction instead of retrying blindly.
        logger.info("clerk identity was created concurrently; re-reading in a new transaction")
        with factory() as conn:
            return resolve_or_create(conn, issuer=issuer, subject=subject, email_provider=provider)
    except IdentityConflict as exc:
        _audit_conflict(
            settings,
            issuer=issuer,
            subject=subject,
            email=getattr(exc, "email", None),
            detail={"reason": str(exc)},
            connect=factory,
        )
        raise


