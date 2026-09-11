"""PostgreSQL access layer (psycopg 3).

Design notes
------------
* One short-lived connection per request/unit of work. The dedicated cluster
  runs with ``max_connections = 30`` and this service is low-traffic; avoiding a
  pool keeps the failure modes trivial to reason about.
* Every statement runs with an explicit ``statement_timeout`` so a stuck query
  can never wedge the service.
* The password is never carried in the connection string as plain text: it is
  read by libpq from a ``0600`` ``pgpass`` file that only the service user can
  read.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from .config import Settings

logger = logging.getLogger("goaa.c2.loop.db")


@contextmanager
def connection(settings: Settings, *, autocommit: bool = False) -> Iterator[psycopg.Connection]:
    """Open a transaction-scoped connection and commit/rollback on exit."""
    conn = psycopg.connect(
        settings.conninfo(),
        row_factory=dict_row,
        autocommit=autocommit,
        options=f"-c statement_timeout={settings.db_statement_timeout_ms}",
    )
    try:
        yield conn
        if not autocommit:
            conn.commit()
    except Exception:
        if not autocommit:
            try:
                conn.rollback()
            except Exception:  # pragma: no cover - connection already gone
                logger.warning("rollback failed", exc_info=True)
        raise
    finally:
        conn.close()


def fetch_one(conn: psycopg.Connection, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetch_all(conn: psycopg.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def execute(conn: psycopg.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def server_facts(settings: Settings) -> dict[str, Any]:
    """Small read-only fingerprint of the database we are talking to.

    Used by ``/health`` so an operator can confirm the service is bound to the
    dedicated loopback cluster and not to anything production.
    """
    with connection(settings) as conn:
        row = fetch_one(
            conn,
            """
            select current_database() as database,
                   current_user      as db_user,
                   host(inet_server_addr()) as server_addr,
                   inet_server_port()       as server_port,
                   current_setting('server_version') as server_version
            """,
        )
    return dict(row or {})
