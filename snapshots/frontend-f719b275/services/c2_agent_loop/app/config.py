"""Runtime configuration for the C2-native agent application backend.

Every value comes from the process environment (provided by the systemd
``EnvironmentFile``). Secrets are never hardcoded here and are never logged or
returned by the API.

This service is an **isolated C2 development/verification environment**:

* it only talks to the dedicated PostgreSQL cluster on ``127.0.0.1:5433``;
* it only serves ``127.0.0.1:3101``;
* it never touches the C1 production runtime, the production database, or any
  production object storage / network rule.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_ALLOWED_MIME = ("image/jpeg", "image/png", "image/webp", "application/pdf")
DEFAULT_ALLOWED_SIDES = ("front", "back", "id", "credential")


def _raw(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    return default if value is None else value.strip()


def _int(name: str, default: int) -> int:
    raw = _raw(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - misconfiguration
        raise RuntimeError(f"environment variable {name} must be an integer") from exc


def _bool(name: str, default: bool) -> bool:
    raw = _raw(name).lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = _raw(name)
    if not raw:
        return default
    return tuple(part.strip() for part in raw.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    """Immutable settings snapshot built from the environment."""

    environment: str = field(default_factory=lambda: _raw("GOAA_C2_ENV", "c2-dev"))
    build_revision: str = field(default_factory=lambda: _raw("GOAA_C2_BUILD_REVISION", "unknown"))

    # --- PostgreSQL (dedicated cluster, loopback only) ---
    db_host: str = field(default_factory=lambda: _raw("GOAA_C2_DB_HOST", "127.0.0.1"))
    db_port: int = field(default_factory=lambda: _int("GOAA_C2_DB_PORT", 5433))
    db_name: str = field(default_factory=lambda: _raw("GOAA_C2_DB_NAME", "goaa_c2"))
    db_user: str = field(default_factory=lambda: _raw("GOAA_C2_DB_USER", "goaa_c2_app"))
    db_passfile: str = field(
        default_factory=lambda: _raw("GOAA_C2_DB_PASSFILE", "/opt/goaa-test/env/app.pgpass")
    )
    db_sslmode: str = field(default_factory=lambda: _raw("GOAA_C2_DB_SSLMODE", "disable"))
    # schema migrations run as a separate, DDL-only role
    migrate_user: str = field(default_factory=lambda: _raw("GOAA_C2_MIGRATE_USER", "goaa_c2_migrate"))
    migrate_passfile: str = field(
        default_factory=lambda: _raw("GOAA_C2_MIGRATE_PASSFILE", "/opt/goaa-test/env/migrate.pgpass")
    )
    psql_binary: str = field(
        default_factory=lambda: _raw("GOAA_C2_PSQL", "/usr/lib/postgresql/16/bin/psql")
    )
    db_connect_timeout: int = field(default_factory=lambda: _int("GOAA_C2_DB_CONNECT_TIMEOUT", 5))
    db_statement_timeout_ms: int = field(
        default_factory=lambda: _int("GOAA_C2_DB_STATEMENT_TIMEOUT_MS", 15000)
    )

    # --- sessions ---
    session_secret: str = field(default_factory=lambda: _raw("GOAA_C2_SESSION_SECRET"))
    session_ttl_seconds: int = field(default_factory=lambda: _int("GOAA_C2_SESSION_TTL", 43200))
    session_cookie_name: str = field(
        default_factory=lambda: _raw("GOAA_C2_SESSION_COOKIE", "goaa_c2_loop_session")
    )

    # --- private document storage (local disk, no external object storage) ---
    private_files_dir: str = field(
        default_factory=lambda: _raw("GOAA_C2_PRIVATE_FILES_DIR", "/opt/goaa-test/private-files")
    )
    storage_label: str = field(
        default_factory=lambda: _raw("GOAA_C2_STORAGE_LABEL", "c2-local-private")
    )
    scanner_label: str = field(default_factory=lambda: _raw("GOAA_C2_SCANNER", "stub"))
    ocr_label: str = field(default_factory=lambda: _raw("GOAA_C2_OCR", "rules-only"))
    download_token_ttl_seconds: int = field(
        default_factory=lambda: _int("GOAA_C2_DOWNLOAD_TTL", 120)
    )
    max_upload_bytes: int = field(default_factory=lambda: _int("GOAA_C2_MAX_UPLOAD_BYTES", 5242880))
    allowed_mime: tuple[str, ...] = field(default_factory=lambda: _csv("GOAA_C2_ALLOWED_MIME", DEFAULT_ALLOWED_MIME))

    # --- public surface (set only when a real reverse proxy fronts the service) ---
    public_base_url: str = field(default_factory=lambda: _raw("GOAA_C2_PUBLIC_BASE_URL", ""))

    # --- email delivery is intentionally disabled in this environment ---
    email_delivery: str = field(default_factory=lambda: _raw("GOAA_C2_EMAIL_DELIVERY", "disabled"))

    @property
    def production_ready(self) -> bool:
        """This service must always report that it is not production ready."""
        return False

    @property
    def allow_public_ingress(self) -> bool:
        return _bool("GOAA_C2_ALLOW_PUBLIC_INGRESS", False)

    def conninfo(self) -> str:
        """libpq connection string. The password is read from a 0600 pgpass file."""
        parts = [
            f"host={self.db_host}",
            f"port={self.db_port}",
            f"dbname={self.db_name}",
            f"user={self.db_user}",
            f"sslmode={self.db_sslmode}",
            f"connect_timeout={self.db_connect_timeout}",
            "application_name=goaa-c2-agent-loop",
        ]
        if self.db_passfile and os.path.exists(self.db_passfile):
            parts.append(f"passfile={self.db_passfile}")
        return " ".join(parts)

    def session_secret_bytes(self) -> bytes:
        if not self.session_secret:
            raise RuntimeError(
                "GOAA_C2_SESSION_SECRET is not set; refusing to start without a session secret"
            )
        if len(self.session_secret) < 32:
            raise RuntimeError("GOAA_C2_SESSION_SECRET is too short (need >= 32 characters)")
        return self.session_secret.encode()


def get_settings() -> Settings:
    return Settings()
