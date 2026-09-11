"""Operator tool: grant a role to an existing account.

The first administrator cannot be created through the HTTP API (that would be a
privilege-escalation hole) and the runtime application role is barred by a
database trigger from granting ``admin`` at all. Administrator grants are
therefore an explicit, audited operator action performed as the schema-owning
migration role:

    /opt/goaa-test/venv/bin/python -m tools.grant_role --email admin@example.test --role admin --confirm

Refuses to run without ``--confirm``.
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import audit  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import connection, fetch_all, fetch_one  # noqa: E402

VALID_ROLES = ("user", "agent", "admin")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="grant a role to an existing goaa C2 account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=VALID_ROLES)
    parser.add_argument("--revoke", action="store_true", help="remove the role instead of granting it")
    parser.add_argument("--confirm", action="store_true", help="required acknowledgement")
    parser.add_argument("--actor-email", default=None, help="account recorded as the granting operator")
    args = parser.parse_args(argv)

    if not args.confirm:
        print("refusing to modify roles without --confirm")
        return 2

    # operator privileges: this runs as the schema-owning role, never as the
    # runtime application role.
    base = get_settings()
    settings = dataclasses.replace(
        base, db_user=base.migrate_user, db_passfile=base.migrate_passfile
    )

    with connection(settings) as conn:
        user = fetch_one(conn, "select id, email from users where lower(email) = lower(%s)", (args.email,))
        if not user:
            print(f"no account found for {args.email}")
            return 1
        actor = None
        if args.actor_email:
            actor_row = fetch_one(
                conn, "select id from users where lower(email) = lower(%s)", (args.actor_email,)
            )
            actor = str(actor_row["id"]) if actor_row else None
        if args.revoke:
            with conn.cursor() as cur:
                cur.execute("delete from user_roles where user_id = %s and role = %s", (str(user["id"]), args.role))
            action = "role.revoked"
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "insert into user_roles (user_id, role, granted_by) values (%s, %s, %s) "
                    "on conflict (user_id, role) do nothing",
                    (str(user["id"]), args.role, actor),
                )
            action = "role.granted"
        audit.record(
            conn,
            action=f"operator.{action}",
            user_id=str(user["id"]),
            actor_user_id=actor,
            actor_role="operator",
            detail={"role": args.role, "via": "tools.grant_role"},
        )
        roles = [
            r["role"]
            for r in fetch_all(conn, "select role from user_roles where user_id = %s order by role", (str(user["id"]),))
        ]
    print(f"{'revoked' if args.revoke else 'granted'} role={args.role} for {args.email}; roles now {roles}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
