"""goaa C2 agent-application backend — FastAPI application.

Scope of this service (approved C2 isolated build)
-------------------------------------------------
* Runs only on ``127.0.0.1:3101`` and only talks to the dedicated PostgreSQL
  cluster on ``127.0.0.1:5433``.
* Owns its own database (``goaa_c2``) and its own private document directory.
* Never reads or writes anything belonging to the C1 production runtime, the
  production database, production object storage, or production network rules.

Honest capability labels are part of the contract and are reported by
``/health``: ``storage_mode=c2-local-private``, ``scanner_mode=stub``,
``ocr_mode=rules-only``, ``production_ready=false``, e-mail delivery ``disabled``.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import psycopg
from fastapi import Depends, FastAPI, Header, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from . import ai_review, audit, storage
from .config import Settings, get_settings
from .db import connection, fetch_all, fetch_one
from .security import (
    mask_address,
    mask_email,
    mask_license_number,
    new_download_token,
    new_session_token,
    parse_download_token,
    parse_session_token,
    password_problem,
    hash_password,
    token_fingerprint,
    verify_password,
)

logger = logging.getLogger("goaa.c2.loop")

API_PREFIX = "/api/v1/agent-loop"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EDITABLE_STATUSES = ("draft", "info_requested")


# ---------------------------------------------------------------------------
# request models
# ---------------------------------------------------------------------------
class RegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str
    full_name: str | None = None
    phone: str | None = None


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str


class VerifyEmailIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str


class LicenseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = None
    license_type: str
    license_number: str
    issuer: str | None = None
    jurisdiction: str | None = None
    expires_on: str | None = None
    no_expiry: bool = False


class ApplicationDraftIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    terms_accepted: bool = False
    licenses: list[LicenseIn] = Field(default_factory=list)


class ReasonIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = None
    note: str | None = None


class RoleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return value


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _public_user(row: dict[str, Any], roles: list[str]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "full_name": row.get("full_name"),
        "phone": row.get("phone"),
        "email_verified": row.get("email_verified_at") is not None,
        "roles": sorted(roles),
        "created_at": _iso(row.get("created_at")),
    }


def _session_user(conn: psycopg.Connection, settings: Settings, token: str | None) -> dict[str, Any] | None:
    """Resolve a session token into an active user with freshly read roles."""
    if not token:
        return None
    payload = parse_session_token(settings.session_secret_bytes(), token)
    if not payload:
        return None
    row = fetch_one(
        conn,
        """
        select s.id as session_id, s.user_id, s.expires_at, s.revoked_at,
               u.id, u.email, u.full_name, u.phone, u.email_verified_at, u.created_at,
               coalesce(array_agg(r.role) filter (where r.role is not null), '{}') as roles
          from user_sessions s
          join users u on u.id = s.user_id
          left join user_roles r on r.user_id = u.id
         where s.token_hash = %s
         group by s.id, s.user_id, s.expires_at, s.revoked_at,
                  u.id, u.email, u.full_name, u.phone, u.email_verified_at, u.created_at
        """,
        (token_fingerprint(token),),
    )
    if not row:
        return None
    if row["revoked_at"] is not None or row["expires_at"] <= _now():
        return None
    if str(row["user_id"]) != payload["sub"]:
        return None
    user = dict(row)
    user["roles"] = list(row["roles"] or [])
    return user


def _bearer_or_cookie(request: Request, settings: Settings) -> str | None:
    """An explicit Authorization header always wins over an ambient cookie."""
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    value = request.cookies.get(settings.session_cookie_name)
    return value or None


def _application_row(conn: psycopg.Connection, *, user_id: str) -> dict[str, Any] | None:
    return fetch_one(conn, "select * from agent_applications where user_id = %s", (user_id,))


def _licenses(conn: psycopg.Connection, application_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "select * from agent_licenses where application_id = %s order by created_at, id",
        (application_id,),
    )


def _documents(conn: psycopg.Connection, application_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        """
        select * from agent_license_documents
         where application_id = %s and deleted_at is null
         order by uploaded_at, id
        """,
        (application_id,),
    )


def _document_public(row: dict[str, Any], *, own_view: bool) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "side": row["side"],
        "mime_type": row["mime_type"],
        "size_bytes": row["size_bytes"],
        "sha256": row["sha256"],
        "storage_label": row["storage_label"],
        "scan_status": row["scan_status"],
        "scanner": row["scanner"],
        "ocr_mode": row["ocr_mode"],
        "uploaded_at": _iso(row["uploaded_at"]),
        "own_view": own_view,
    }


def _license_public(row: dict[str, Any], *, own_view: bool) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "license_type": row["license_type"],
        "license_number": row["license_number"] if own_view else mask_license_number(row["license_number"]),
        "issuer": row["issuer"],
        "jurisdiction": row["jurisdiction"],
        "expires_on": row["expires_on"].isoformat() if row["expires_on"] else None,
        "no_expiry": row["no_expiry"],
    }


def _application_public(
    conn: psycopg.Connection,
    row: dict[str, Any],
    *,
    own_view: bool,
    with_children: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": str(row["id"]),
        "user_id": str(row["user_id"]),
        "status": row["status"],
        "full_name": row["full_name"],
        "phone": row["phone"],
        "email": row["email"] if own_view else mask_email(row["email"]),
        "address": row["address"] if own_view else mask_address(row["address"]),
        "terms_accepted": row["terms_accepted_at"] is not None,
        "submitted_at": _iso(row["submitted_at"]),
        "decided_at": _iso(row["decided_at"]),
        "decision_reason": row["decision_reason"],
        "pre_review": row["pre_review"],
        "created_at": _iso(row["created_at"]),
        "updated_at": _iso(row["updated_at"]),
        "own_view": own_view,
    }
    if with_children:
        payload["licenses"] = [_license_public(lic, own_view=own_view) for lic in _licenses(conn, str(row["id"]))]
        payload["documents"] = [_document_public(doc, own_view=own_view) for doc in _documents(conn, str(row["id"]))]
    return payload


def _require_fields(application: dict[str, Any]) -> list[str]:
    missing = []
    for field in ai_review.REQUIRED_FIELDS:
        value = application.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing


def _idempotent_replay(
    conn: psycopg.Connection, key: str | None, user_id: str, endpoint: str
) -> JSONResponse | None:
    if not key:
        return None
    row = fetch_one(conn, "select * from idempotency_keys where key = %s", (key,))
    if not row:
        return None
    if str(row["user_id"]) != user_id or row["endpoint"] != endpoint:
        return _error(409, "idempotency_key_conflict", "idempotency key already used for another request")
    return JSONResponse(status_code=row["response_status"], content=row["response_body"])


def _idempotent_store(
    conn: psycopg.Connection,
    key: str | None,
    user_id: str,
    endpoint: str,
    response: JSONResponse,
) -> None:
    if not key:
        return
    body = response.body.decode("utf-8")
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into idempotency_keys (key, user_id, endpoint, response_status, response_body)
            values (%s, %s, %s, %s, %s::jsonb)
            on conflict (key) do nothing
            """,
            (key, user_id, endpoint, response.status_code, body),
        )


# ---------------------------------------------------------------------------
# application factory
# ---------------------------------------------------------------------------
def _persist_document(
    settings: Settings,
    user_id: str,
    side: str,
    license_hint: str | None,
    mime_type: str,
    payload: bytes,
) -> dict[str, Any] | tuple[int, str, str]:
    """Blocking half of the upload path (disk + database), run in a threadpool."""
    with connection(settings) as conn:
        row = _application_row(conn, user_id=user_id)
        if not row:
            return (409, "no_application", "save an application draft before uploading documents")
        if row["status"] not in EDITABLE_STATUSES:
            return (409, "application_locked", f"application in status '{row['status']}' is read-only")
        application_id = str(row["id"])
        license_id = None
        if license_hint:
            match = fetch_one(
                conn,
                "select id from agent_licenses where id = %s and application_id = %s",
                (license_hint, application_id),
            )
            license_id = str(match["id"]) if match else None
        stored = storage.save_bytes(settings.private_files_dir, mime_type, payload)
        doc = fetch_one(
            conn,
            """
            insert into agent_license_documents
                (application_id, license_id, owner_user_id, side, mime_type, size_bytes, sha256,
                 storage_key, storage_label, scan_status, scanner, ocr_mode)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            returning *
            """,
            (application_id, license_id, user_id, side, mime_type, stored.size_bytes, stored.sha256,
             stored.storage_key, settings.storage_label, "stub", settings.scanner_label, settings.ocr_label),
        )
        audit.record(
            conn,
            action="document.uploaded",
            application_id=application_id,
            user_id=user_id,
            actor_user_id=user_id,
            actor_role="user",
            detail={"side": side, "mime_type": mime_type, "size_bytes": stored.size_bytes,
                    "scanner": settings.scanner_label, "ocr": settings.ocr_label},
        )
    return doc


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="goaa C2 agent application backend",
        version="1.0.0-c2",
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    app.state.settings = settings

    # -- dependencies -------------------------------------------------------
    def current_user(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        cfg: Settings = request.app.state.settings
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            token = request.cookies.get(cfg.session_cookie_name)
        if not token:
            raise _HTTPError(401, "not_authenticated", "authentication required")
        with connection(cfg) as conn:
            user = _session_user(conn, cfg, token)
        if not user:
            raise _HTTPError(401, "invalid_session", "session is missing, expired or revoked")
        return user

    def require_admin(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if "admin" not in user["roles"]:
            raise _HTTPError(403, "admin_required", "administrator role required")
        return user

    # -- error handling -----------------------------------------------------
    @app.exception_handler(_HTTPError)
    def _http_error_handler(_request: Request, exc: "_HTTPError") -> JSONResponse:
        return _error(exc.status, exc.code, exc.message)

    @app.middleware("http")
    async def _no_store(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    # -- health -------------------------------------------------------------
    @app.get(f"{API_PREFIX}/health")
    def health() -> dict[str, Any]:
        from .db import server_facts

        facts: dict[str, Any] = {}
        db_ok = True
        try:
            facts = server_facts(settings)
        except Exception:  # pragma: no cover - surfaced as degraded
            db_ok = False
            logger.warning("database health probe failed", exc_info=True)
        return {
            "status": "ok" if db_ok else "degraded",
            "service": "goaa-c2-agent-loop",
            "environment": settings.environment,
            "database": {
                "host": settings.db_host,
                "port": settings.db_port,
                "name": settings.db_name,
                "user": settings.db_user,
                "server_version": facts.get("server_version"),
                "server_addr": facts.get("server_addr"),
                "server_port": facts.get("server_port"),
                "reachable": db_ok,
            },
            "capabilities": {
                "storage_mode": settings.storage_label,
                "scanner_mode": settings.scanner_label,
                "ocr_mode": settings.ocr_label,
                "email_delivery": settings.email_delivery,
            },
            "production_ready": False,
            "production_resources_used": False,
        }

    # -- auth ---------------------------------------------------------------
    @app.post(f"{API_PREFIX}/auth/register", status_code=201)
    def register(payload: RegisterIn) -> JSONResponse:
        email = payload.email.strip()
        if not EMAIL_RE.match(email):
            return _error(422, "invalid_email", "a valid e-mail address is required")
        problem = password_problem(payload.password)
        if problem:
            return _error(422, "weak_password", problem)
        with connection(settings) as conn:
            existing = fetch_one(conn, "select id from users where lower(email) = lower(%s)", (email,))
            if existing:
                return _error(409, "email_in_use", "an account already exists for this e-mail address")
            row = fetch_one(
                conn,
                """
                insert into users (email, password_hash, full_name, phone)
                values (%s, %s, %s, %s)
                returning *
                """,
                (email, hash_password(payload.password), payload.full_name, payload.phone),
            )
            user_id = str(row["id"])
            with conn.cursor() as cur:
                cur.execute(
                    "insert into user_roles (user_id, role) values (%s, 'user') on conflict do nothing",
                    (user_id,),
                )
            audit.record(
                conn,
                action="user.registered",
                user_id=user_id,
                actor_user_id=user_id,
                actor_role="user",
                detail={"environment": settings.environment},
            )
        return JSONResponse(
            status_code=201,
            content={"user": _public_user(row, ["user"]), "next": "login"},
        )

    @app.post(f"{API_PREFIX}/auth/login")
    def login(payload: LoginIn) -> JSONResponse:
        email = payload.email.strip()
        with connection(settings) as conn:
            row = fetch_one(conn, "select * from users where lower(email) = lower(%s)", (email,))
            if not row or not verify_password(payload.password, row["password_hash"]):
                return _error(401, "invalid_credentials", "e-mail or password is incorrect")
            roles = [
                r["role"]
                for r in fetch_all(conn, "select role from user_roles where user_id = %s", (str(row["id"]),))
            ]
            token, fingerprint, expires_at = new_session_token(
                settings.session_secret_bytes(), str(row["id"]), settings.session_ttl_seconds
            )
            with conn.cursor() as cur:
                cur.execute(
                    "insert into user_sessions (user_id, token_hash, expires_at) values (%s, %s, to_timestamp(%s))",
                    (str(row["id"]), fingerprint, expires_at),
                )
            audit.record(
                conn,
                action="session.created",
                user_id=str(row["id"]),
                actor_user_id=str(row["id"]),
                actor_role=",".join(sorted(roles)) or "user",
                detail={"ttl_seconds": settings.session_ttl_seconds},
            )
        response = JSONResponse(
            content={
                "user": _public_user(row, roles),
                "access_token": token,
                "expires_at": _iso(datetime.fromtimestamp(expires_at, tz=timezone.utc)),
                "cookie_name": settings.session_cookie_name,
            }
        )
        # the cookie is set on the very response we return, so it can never be lost
        response.set_cookie(
            settings.session_cookie_name,
            token,
            max_age=settings.session_ttl_seconds,
            httponly=True,
            samesite="lax",
            secure=False,  # loopback HTTP only; no TLS listener in this environment
            path="/",
        )
        return response

    @app.post(f"{API_PREFIX}/auth/logout")
    def logout(
        user: dict[str, Any] = Depends(current_user),
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        token: str | None = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        with connection(settings) as conn:
            if token:
                with conn.cursor() as cur:
                    cur.execute(
                        "update user_sessions set revoked_at = now() where token_hash = %s and revoked_at is null",
                        (token_fingerprint(token),),
                    )
            else:
                with conn.cursor() as cur:
                    cur.execute(
                        "update user_sessions set revoked_at = now() where id = %s and revoked_at is null",
                        (str(user["session_id"]),),
                    )
            audit.record(
                conn,
                action="session.revoked",
                user_id=str(user["user_id"]),
                actor_user_id=str(user["user_id"]),
                actor_role=",".join(sorted(user["roles"])) or "user",
                detail={},
            )
        return JSONResponse(content={"status": "signed_out"})

    @app.get(f"{API_PREFIX}/auth/me")
    def me(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        with connection(settings) as conn:
            application = _application_row(conn, user_id=str(user["user_id"]))
        return {
            "user": _public_user(user, user["roles"]),
            "application": {
                "id": str(application["id"]),
                "status": application["status"],
            }
            if application
            else None,
        }

    @app.post(f"{API_PREFIX}/auth/verify-email")
    def verify_email(payload: VerifyEmailIn) -> JSONResponse:
        with connection(settings) as conn:
            row = fetch_one(
                conn,
                """
                update email_verifications
                   set consumed_at = now()
                 where token_hash = %s and consumed_at is null and expires_at > now()
                 returning user_id, email
                """,
                (token_fingerprint(payload.token),),
            )
            if not row:
                return _error(400, "invalid_token", "verification token is invalid or expired")
            with conn.cursor() as cur:
                cur.execute("update users set email_verified_at = now(), updated_at = now() where id = %s",
                            (str(row["user_id"]),))
            audit.record(
                conn,
                action="email.verified",
                user_id=str(row["user_id"]),
                actor_user_id=str(row["user_id"]),
                actor_role="user",
                detail={},
            )
        return {"status": "verified"}

    # -- applicant surfaces -------------------------------------------------
    @app.get(f"{API_PREFIX}/applications/me")
    def application_me(user: dict[str, Any] = Depends(current_user)) -> JSONResponse:
        with connection(settings) as conn:
            row = _application_row(conn, user_id=str(user["user_id"]))
            if not row:
                return JSONResponse(
                    content={
                        "application": None,
                        "can_apply": True,
                        "status": "none",
                        "environment": settings.environment,
                    }
                )
            return JSONResponse(content={"application": _application_public(conn, row, own_view=True)})

    @app.put(f"{API_PREFIX}/applications/me")
    def application_save(payload: ApplicationDraftIn, user: dict[str, Any] = Depends(current_user)) -> JSONResponse:
        user_id = str(user["user_id"])
        if payload.email and not EMAIL_RE.match(payload.email.strip()):
            return _error(422, "invalid_email", "a valid e-mail address is required")
        with connection(settings) as conn:
            row = _application_row(conn, user_id=user_id)
            if row and row["status"] not in EDITABLE_STATUSES:
                return _error(409, "application_locked", f"application in status '{row['status']}' is read-only")
            if not row:
                row = fetch_one(
                    conn,
                    "insert into agent_applications (user_id, status) values (%s, 'draft') returning *",
                    (user_id,),
                )
                audit.record(
                    conn,
                    action="application.created",
                    application_id=str(row["id"]),
                    user_id=user_id,
                    actor_user_id=user_id,
                    actor_role="user",
                    detail={},
                )
            application_id = str(row["id"])
            row = fetch_one(
                conn,
                """
                update agent_applications
                   set full_name = %s, phone = %s, email = %s, address = %s,
                       terms_accepted_at = case when %s then coalesce(terms_accepted_at, now()) else terms_accepted_at end,
                       updated_at = now()
                 where id = %s
                 returning *
                """,
                (payload.full_name, payload.phone, payload.email, payload.address, payload.terms_accepted, application_id),
            )
            _upsert_licenses(conn, application_id, payload.licenses)
            audit.record(
                conn,
                action="application.draft_saved",
                application_id=application_id,
                user_id=user_id,
                actor_user_id=user_id,
                actor_role="user",
                detail={"licenses": len(payload.licenses), "terms_accepted": payload.terms_accepted},
            )
            row = fetch_one(conn, "select * from agent_applications where id = %s", (application_id,))
            return JSONResponse(content={"application": _application_public(conn, row, own_view=True)})

    def _upsert_licenses(conn: psycopg.Connection, application_id: str, incoming: list[LicenseIn]) -> None:
        existing = {str(r["id"]): r for r in _licenses(conn, application_id)}
        keep: list[str] = []
        for item in incoming:
            expires_on = None
            if item.expires_on:
                try:
                    expires_on = datetime.fromisoformat(item.expires_on).date()
                except ValueError:
                    expires_on = None
            license_id = item.id
            if license_id and license_id in existing:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        update agent_licenses
                           set license_type = %s, license_number = %s, issuer = %s, jurisdiction = %s,
                               expires_on = %s, no_expiry = %s, updated_at = now()
                         where id = %s and application_id = %s
                        """,
                        (item.license_type, item.license_number, item.issuer, item.jurisdiction,
                         expires_on, item.no_expiry, license_id, application_id),
                    )
                keep.append(license_id)
            else:
                new_row = fetch_one(
                    conn,
                    """
                    insert into agent_licenses
                        (application_id, license_type, license_number, issuer, jurisdiction, expires_on, no_expiry)
                    values (%s, %s, %s, %s, %s, %s, %s)
                    returning id
                    """,
                    (application_id, item.license_type, item.license_number, item.issuer,
                     item.jurisdiction, expires_on, item.no_expiry),
                )
                keep.append(str(new_row["id"]))
        stale = [lid for lid in existing if lid not in keep]
        if stale:
            with conn.cursor() as cur:
                cur.execute("delete from agent_licenses where id = any(%s)", (stale,))

    @app.post(f"{API_PREFIX}/applications/me/submit")
    def application_submit(
        user: dict[str, Any] = Depends(current_user),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> JSONResponse:
        user_id = str(user["user_id"])
        with connection(settings) as conn:
            replay = _idempotent_replay(conn, idempotency_key, user_id, "applications.submit")
            if replay:
                return replay
            row = _application_row(conn, user_id=user_id)
            if not row:
                return _error(409, "no_application", "save a draft before submitting")
            if row["status"] not in EDITABLE_STATUSES:
                return _error(409, "application_locked", f"application in status '{row['status']}' cannot be submitted")
            missing = _require_fields(row)
            if missing:
                return _error(422, "incomplete_application", "missing required fields: " + ", ".join(missing))
            if row["terms_accepted_at"] is None:
                return _error(422, "terms_not_accepted", "the terms of service must be accepted")
            if not _licenses(conn, str(row["id"])):
                return _error(422, "no_license", "at least one licence must be supplied")
            if not _documents(conn, str(row["id"])):
                return _error(422, "no_document", "at least one supporting document must be uploaded")
            application_id = str(row["id"])
            licenses = _licenses(conn, application_id)
            documents = _documents(conn, application_id)
            review = ai_review.pre_review(row, licenses, documents).as_dict()
            row = fetch_one(
                conn,
                """
                update agent_applications
                   set status = 'submitted', submitted_at = now(), pre_review = %s::jsonb, updated_at = now()
                 where id = %s
                 returning *
                """,
                (json.dumps(review), application_id),
            )
            audit.record(
                conn,
                action="application.submitted",
                application_id=application_id,
                user_id=user_id,
                actor_user_id=user_id,
                actor_role="user",
                detail={"pre_review_recommendation": review["recommendation"]},
            )
            body = {"application": _application_public(conn, row, own_view=True), "pre_review": review}
            response = JSONResponse(content=body)
            _idempotent_store(conn, idempotency_key, user_id, "applications.submit", response)
            return response

    @app.get(f"{API_PREFIX}/applications/{{application_id}}")
    def application_by_id(application_id: str, user: dict[str, Any] = Depends(current_user)) -> JSONResponse:
        with connection(settings) as conn:
            row = fetch_one(conn, "select * from agent_applications where id = %s", (application_id,))
            if not row:
                return _error(404, "not_found", "application not found")
            own = str(row["user_id"]) == str(user["user_id"])
            if not own and "admin" not in user["roles"]:
                return _error(404, "not_found", "application not found")
            return JSONResponse(content={"application": _application_public(conn, row, own_view=own)})

    # -- documents ----------------------------------------------------------
    @app.post(f"{API_PREFIX}/documents", status_code=201)
    async def document_upload(
        request: Request,
        user: dict[str, Any] = Depends(current_user),
        x_document_side: str | None = Header(default=None, alias="X-Document-Side"),
        x_license_id: str | None = Header(default=None, alias="X-License-Id"),
    ) -> JSONResponse:
        user_id = str(user["user_id"])
        side = (x_document_side or "front").strip().lower()
        if side not in ("front", "back", "id", "credential"):
            return _error(422, "invalid_side", "document side must be one of front, back, id, credential")
        payload = await request.body()
        if not payload:
            return _error(422, "empty_body", "an empty document body was sent")
        if len(payload) > settings.max_upload_bytes:
            return _error(413, "too_large", f"document exceeds the {settings.max_upload_bytes} byte limit")
        declared = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
        sniffed = storage.sniff_mime(payload)
        if sniffed is None:
            return _error(415, "unsupported_media_type", "only JPEG, PNG, WebP and PDF are accepted")
        if declared and declared in settings.allowed_mime and declared != sniffed:
            return _error(415, "content_type_mismatch", "declared content type does not match the payload")
        mime_type = sniffed
        # blocking disk + database work is pushed off the event loop
        outcome = await run_in_threadpool(
            _persist_document, settings, user_id, side, x_license_id, mime_type, payload
        )
        if isinstance(outcome, tuple):
            return _error(*outcome)
        # NOTE: the storage key is intentionally not part of the response.
        return JSONResponse(status_code=201, content={"document": _document_public(outcome, own_view=True)})

    @app.get(f"{API_PREFIX}/documents/{{document_id}}/link")
    def document_link(document_id: str, user: dict[str, Any] = Depends(current_user)) -> JSONResponse:
        with connection(settings) as conn:
            doc = fetch_one(
                conn,
                "select * from agent_license_documents where id = %s and deleted_at is null",
                (document_id,),
            )
            if not doc:
                return _error(404, "not_found", "document not found")
            owner = str(doc["owner_user_id"])
            if owner != str(user["user_id"]) and "admin" not in user["roles"]:
                return _error(404, "not_found", "document not found")
            token = new_download_token(
                settings.session_secret_bytes(), str(doc["id"]), owner, settings.download_token_ttl_seconds
            )
            path = f"{API_PREFIX}/downloads/{token}"
            url = f"{settings.public_base_url.rstrip('/')}{path}" if settings.public_base_url else path
            return JSONResponse(
                content={
                    "url": url,
                    "expires_in": settings.download_token_ttl_seconds,
                    "storage_label": doc["storage_label"],
                    "scan_status": doc["scan_status"],
                    "scanner": doc["scanner"],
                }
            )

    @app.get(f"{API_PREFIX}/downloads/{{token}}")
    def document_download(token: str, user: dict[str, Any] = Depends(current_user)) -> Response:
        payload = parse_download_token(settings.session_secret_bytes(), token)
        if not payload:
            return _error(403, "invalid_link", "download link is invalid or expired")
        if payload["own"] != str(user["user_id"]) and "admin" not in user["roles"]:
            return _error(403, "invalid_link", "download link is invalid or expired")
        with connection(settings) as conn:
            doc = fetch_one(
                conn,
                "select * from agent_license_documents where id = %s and deleted_at is null",
                (payload["doc"],),
            )
        if not doc:
            return _error(404, "not_found", "document not found")
        try:
            blob = storage.read_bytes(settings.private_files_dir, doc["storage_key"])
        except (FileNotFoundError, ValueError):
            return _error(410, "gone", "document payload is no longer available")
        return Response(
            content=blob,
            media_type=doc["mime_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{doc["id"]}.{doc["mime_type"].split("/")[-1]}"',
                "Cache-Control": "no-store",
            },
        )

    @app.delete(f"{API_PREFIX}/documents/{{document_id}}")
    def document_delete(document_id: str, user: dict[str, Any] = Depends(current_user)) -> JSONResponse:
        with connection(settings) as conn:
            doc = fetch_one(
                conn,
                "select * from agent_license_documents where id = %s and deleted_at is null",
                (document_id,),
            )
            if not doc:
                return _error(404, "not_found", "document not found")
            if str(doc["owner_user_id"]) != str(user["user_id"]):
                return _error(404, "not_found", "document not found")
            app_row = fetch_one(conn, "select status from agent_applications where id = %s", (str(doc["application_id"]),))
            if app_row and app_row["status"] not in EDITABLE_STATUSES:
                return _error(409, "application_locked", "documents cannot be removed after submission")
            with conn.cursor() as cur:
                cur.execute("update agent_license_documents set deleted_at = now() where id = %s", (document_id,))
            storage.delete_bytes(settings.private_files_dir, doc["storage_key"])
            audit.record(
                conn,
                action="document.deleted",
                application_id=str(doc["application_id"]),
                user_id=str(user["user_id"]),
                actor_user_id=str(user["user_id"]),
                actor_role="user",
                detail={"side": doc["side"]},
            )
        return JSONResponse(content={"status": "deleted"})

    # -- agent panel --------------------------------------------------------
    @app.get(f"{API_PREFIX}/agent/panel")
    def agent_panel(user: dict[str, Any] = Depends(current_user)) -> JSONResponse:
        user_id = str(user["user_id"])
        with connection(settings) as conn:
            row = _application_row(conn, user_id=user_id)
            is_agent = "agent" in user["roles"]
            approved = bool(row and row["status"] == "approved")
            if not (is_agent and approved):
                # uniform answer so a non-agent cannot enumerate state
                return _error(403, "agent_role_required", "an approved agent licence is required")
            return JSONResponse(
                content={
                    "status": "active",
                    "application_id": str(row["id"]),
                    "granted_at": _iso(row["decided_at"]),
                    "licenses": [_license_public(l, own_view=True) for l in _licenses(conn, str(row["id"]))],
                }
            )

    # -- admin surfaces -----------------------------------------------------
    @app.get(f"{API_PREFIX}/admin/applications")
    def admin_queue(
        status: str | None = None,
        user: dict[str, Any] = Depends(require_admin),
    ) -> JSONResponse:
        with connection(settings) as conn:
            if status:
                rows = fetch_all(
                    conn,
                    "select * from agent_applications where status = %s order by updated_at desc limit 200",
                    (status,),
                )
            else:
                rows = fetch_all(conn, "select * from agent_applications order by updated_at desc limit 200")
            items = [_application_public(conn, r, own_view=False, with_children=False) for r in rows]
            return JSONResponse(content={"count": len(items), "items": items})

    @app.get(f"{API_PREFIX}/admin/applications/{{application_id}}")
    def admin_detail(application_id: str, user: dict[str, Any] = Depends(require_admin)) -> JSONResponse:
        with connection(settings) as conn:
            row = fetch_one(conn, "select * from agent_applications where id = %s", (application_id,))
            if not row:
                return _error(404, "not_found", "application not found")
            events = fetch_all(
                conn,
                "select id, action, actor_role, detail, created_at from agent_review_events where application_id = %s order by id",
                (application_id,),
            )
            return JSONResponse(
                content={
                    "application": _application_public(conn, row, own_view=False),
                    "events": [
                        {**e, "id": e["id"], "created_at": _iso(e["created_at"])} for e in events
                    ],
                }
            )

    def _decide(
        *,
        application_id: str,
        admin: dict[str, Any],
        idempotency_key: str | None,
        action: str,
        new_status: str,
        reason: str | None,
        grant_agent: bool,
        revoke_agent: bool,
    ) -> JSONResponse:
        admin_id = str(admin["user_id"])
        with connection(settings) as conn:
            endpoint = f"admin.{action}"
            replay = _idempotent_replay(conn, idempotency_key, admin_id, endpoint)
            if replay:
                return replay
            row = fetch_one(conn, "select * from agent_applications where id = %s", (application_id,))
            if not row:
                return _error(404, "not_found", "application not found")
            applicant_id = str(row["user_id"])
            if new_status in ("approved", "rejected", "info_requested") and row["status"] not in (
                "submitted",
                "info_requested",
                "approved",
                "rejected",
            ):
                return _error(409, "invalid_transition", f"cannot {action} an application in status '{row['status']}'")
            updated = fetch_one(
                conn,
                """
                update agent_applications
                   set status = %s,
                       decided_at = case when %s in ('approved','rejected','suspended') then now() else decided_at end,
                       decision_reason = %s,
                       decided_by = %s,
                       updated_at = now()
                 where id = %s
                 returning *
                """,
                (new_status, new_status, reason, admin_id, application_id),
            )
            granted = False
            if grant_agent:
                with conn.cursor() as cur:
                    cur.execute(
                        "insert into user_roles (user_id, role, granted_by) values (%s, 'agent', %s) "
                        "on conflict (user_id, role) do nothing",
                        (applicant_id, admin_id),
                    )
                    granted = cur.rowcount > 0
            if revoke_agent:
                with conn.cursor() as cur:
                    cur.execute("delete from user_roles where user_id = %s and role = 'agent'", (applicant_id,))
            audit.record(
                conn,
                action=f"application.{action}",
                application_id=application_id,
                user_id=applicant_id,
                actor_user_id=admin_id,
                actor_role="admin",
                detail={
                    "status": new_status,
                    "role_granted": granted,
                    "role_revoked": bool(revoke_agent),
                    "reason_present": bool(reason),
                },
            )
            body = {
                "application": _application_public(conn, updated, own_view=False),
                "agent_role_granted": granted,
            }
            response = JSONResponse(content=body)
            _idempotent_store(conn, idempotency_key, admin_id, endpoint, response)
            return response

    @app.post(f"{API_PREFIX}/admin/applications/{{application_id}}/approve")
    def admin_approve(
        application_id: str,
        user: dict[str, Any] = Depends(require_admin),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> JSONResponse:
        return _decide(
            application_id=application_id, admin=user, idempotency_key=idempotency_key,
            action="approve", new_status="approved", reason=None, grant_agent=True, revoke_agent=False,
        )

    @app.post(f"{API_PREFIX}/admin/applications/{{application_id}}/reject")
    def admin_reject(
        application_id: str,
        payload: ReasonIn,
        user: dict[str, Any] = Depends(require_admin),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> JSONResponse:
        return _decide(
            application_id=application_id, admin=user, idempotency_key=idempotency_key,
            action="reject", new_status="rejected", reason=payload.reason, grant_agent=False, revoke_agent=False,
        )

    @app.post(f"{API_PREFIX}/admin/applications/{{application_id}}/request-info")
    def admin_request_info(
        application_id: str,
        payload: ReasonIn,
        user: dict[str, Any] = Depends(require_admin),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> JSONResponse:
        return _decide(
            application_id=application_id, admin=user, idempotency_key=idempotency_key,
            action="request_info", new_status="info_requested", reason=payload.note or payload.reason,
            grant_agent=False, revoke_agent=False,
        )

    @app.post(f"{API_PREFIX}/admin/applications/{{application_id}}/suspend")
    def admin_suspend(
        application_id: str,
        payload: ReasonIn,
        user: dict[str, Any] = Depends(require_admin),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> JSONResponse:
        return _decide(
            application_id=application_id, admin=user, idempotency_key=idempotency_key,
            action="suspend", new_status="suspended", reason=payload.reason, grant_agent=False, revoke_agent=True,
        )

    @app.post(f"{API_PREFIX}/admin/applications/{{application_id}}/rerun-ai")
    def admin_rerun_ai(application_id: str, user: dict[str, Any] = Depends(require_admin)) -> JSONResponse:
        with connection(settings) as conn:
            row = fetch_one(conn, "select * from agent_applications where id = %s", (application_id,))
            if not row:
                return _error(404, "not_found", "application not found")
            review = ai_review.pre_review(row, _licenses(conn, application_id), _documents(conn, application_id)).as_dict()
            with conn.cursor() as cur:
                cur.execute(
                    "update agent_applications set pre_review = %s::jsonb, updated_at = now() where id = %s",
                    (json.dumps(review), application_id),
                )
            audit.record(
                conn,
                action="application.pre_review_rerun",
                application_id=application_id,
                user_id=str(row["user_id"]),
                actor_user_id=str(user["user_id"]),
                actor_role="admin",
                detail={"recommendation": review["recommendation"], "mode": review["mode"]},
            )
            return JSONResponse(content={"pre_review": review})

    @app.get(f"{API_PREFIX}/admin/audit")
    def admin_audit(
        application_id: str | None = None,
        limit: int = 100,
        user: dict[str, Any] = Depends(require_admin),
    ) -> JSONResponse:
        limit = max(1, min(limit, 500))
        with connection(settings) as conn:
            if application_id:
                rows = fetch_all(
                    conn,
                    "select id, application_id, action, actor_role, detail, created_at from agent_review_events "
                    "where application_id = %s order by id desc limit %s",
                    (application_id, limit),
                )
            else:
                rows = fetch_all(
                    conn,
                    "select id, application_id, action, actor_role, detail, created_at from agent_review_events "
                    "order by id desc limit %s",
                    (limit,),
                )
            return JSONResponse(
                content={
                    "count": len(rows),
                    "items": [
                        {
                            **{k: v for k, v in r.items() if k != "created_at"},
                            "application_id": str(r["application_id"]) if r["application_id"] else None,
                            "created_at": _iso(r["created_at"]),
                        }
                        for r in rows
                    ],
                }
            )

    @app.post(f"{API_PREFIX}/admin/users/{{target_user_id}}/roles")
    def admin_grant_role(
        target_user_id: str,
        payload: RoleIn,
        user: dict[str, Any] = Depends(require_admin),
    ) -> JSONResponse:
        # 'admin' is deliberately not grantable through the API: it is an
        # out-of-band operator action (see tools/grant_role.py) and is refused
        # by a database trigger for the runtime application role.
        if payload.role not in ("user", "agent"):
            return _error(
                403,
                "role_not_assignable",
                "only the user and agent roles can be granted through the API",
            )
        with connection(settings) as conn:
            target = fetch_one(conn, "select id from users where id = %s", (target_user_id,))
            if not target:
                return _error(404, "not_found", "user not found")
            with conn.cursor() as cur:
                cur.execute(
                    "insert into user_roles (user_id, role, granted_by) values (%s, %s, %s) "
                    "on conflict (user_id, role) do nothing",
                    (target_user_id, payload.role, str(user["user_id"])),
                )
            audit.record(
                conn,
                action="role.granted",
                user_id=target_user_id,
                actor_user_id=str(user["user_id"]),
                actor_role="admin",
                detail={"role": payload.role},
            )
            roles = [r["role"] for r in fetch_all(conn, "select role from user_roles where user_id = %s", (target_user_id,))]
            return JSONResponse(content={"user_id": target_user_id, "roles": sorted(roles)})

    return app


class _HTTPError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


app = create_app()
