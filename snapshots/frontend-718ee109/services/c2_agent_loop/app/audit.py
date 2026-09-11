"""Append-only audit trail helper.

The append-only guarantee is enforced **in the database** (trigger installed by
``migrations/0003_audit_append_only.sql``) and additionally by table privileges:
the application role has ``SELECT``/``INSERT`` on ``agent_review_events`` but no
``UPDATE``/``DELETE``/``TRUNCATE``. This module is therefore a thin insert
helper and deliberately offers no update/delete code path.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import psycopg

logger = logging.getLogger("goaa.c2.loop.audit")


def record(
    conn: psycopg.Connection,
    *,
    action: str,
    application_id: str | None = None,
    user_id: str | None = None,
    actor_user_id: str | None = None,
    actor_role: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """Append one immutable audit event to the same transaction."""
    safe_detail = _redact(detail or {})
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into agent_review_events
                (application_id, user_id, actor_user_id, actor_role, action, detail)
            values (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                application_id,
                user_id,
                actor_user_id,
                actor_role,
                action,
                json.dumps(safe_detail, sort_keys=True),
            ),
        )


_SENSITIVE_KEYS = ("password", "secret", "token", "hash", "license_number", "licence_number")


def _redact(detail: dict[str, Any]) -> dict[str, Any]:
    """Defence in depth: never persist credential material in the audit trail."""
    clean: dict[str, Any] = {}
    for key, value in detail.items():
        lowered = key.lower()
        if any(marker in lowered for marker in _SENSITIVE_KEYS):
            clean[key] = "[redacted]"
        elif isinstance(value, dict):
            clean[key] = _redact(value)
        else:
            clean[key] = value
    return clean
