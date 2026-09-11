"""Apply the PostgreSQL migrations in order, forward-only and idempotent.

Each migration is executed by ``psql -1 -f <file>`` as the dedicated
``goaa_c2_migrate`` role (DSL/DDL privileges only, no superuser). The password
is supplied through a ``0600`` pgpass file, never on the command line.

Re-running the tool is safe: every migration file is written to be re-runnable
and its version is recorded in ``schema_migrations``.

Usage::

    python -m services.c2_agent_loop.tools.migrate --status
    python -m services.c2_agent_loop.tools.migrate
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _env_or(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else default


def _psql_args() -> list[str]:
    return [
        _env_or("GOAA_C2_PSQL", "/usr/lib/postgresql/16/bin/psql"),
        "-h", _env_or("GOAA_C2_DB_HOST", "127.0.0.1"),
        "-p", _env_or("GOAA_C2_DB_PORT", "5433"),
        "-U", _env_or("GOAA_C2_MIGRATE_USER", "goaa_c2_migrate"),
        "-d", _env_or("GOAA_C2_DB_NAME", "goaa_c2"),
        "-v", "ON_ERROR_STOP=1",
        "-X",
    ]


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PGPASSFILE"] = _env_or("GOAA_C2_MIGRATE_PASSFILE", "/opt/goaa-test/env/migrate.pgpass")
    return env


def _run(sql_or_file: list[str], *, use_file: bool) -> subprocess.CompletedProcess:
    args = _psql_args()
    args += (["-f", sql_or_file[0]] if use_file else ["-Atc", sql_or_file[0]])
    if use_file:
        args.insert(len(_psql_args()), "-1")  # single transaction per migration file
    return subprocess.run(args, env=_env(), capture_output=True, text=True)


def applied_versions() -> set[str]:
    probe = (
        "select version from schema_migrations order by version"
        " -- bootstrap: table may not exist yet"
    )
    result = _run([probe], use_file=False)
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def pending_migrations() -> list[Path]:
    have = applied_versions()
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    pending: list[Path] = []
    for path in files:
        # version key is the leading numeric prefix, e.g. "0001" -> "0001_identity"
        if path.stem not in have:
            pending.append(path)
    return pending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="apply goaa C2 PostgreSQL migrations")
    parser.add_argument("--status", action="store_true", help="only report what is applied/pending")
    args = parser.parse_args(argv)

    have = applied_versions()
    print(f"applied : {sorted(have) if have else '(none)'}")
    pending = pending_migrations()
    print(f"pending : {[p.name for p in pending] or '(none)'}")
    if args.status or not pending:
        return 0

    failures = 0
    for path in pending:
        result = _run([str(path)], use_file=True)
        if result.returncode != 0:
            failures += 1
            print(f"FAILED {path.name} rc={result.returncode}")
            print(result.stdout)
            print(result.stderr)
            break
        print(f"applied {path.name}")
    if failures:
        return 1
    print("migrations complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
