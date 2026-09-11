# goaa C2 agent-application loop (PostgreSQL-native)

A self-contained **C2 environment** implementation of the "ordinary user applies
to become a licensed agent" loop.

> **Scope and honesty statement.** This service runs on the C2 host only. It uses
> its own PostgreSQL 16 cluster on `127.0.0.1:5433`, its own database
> (`goaa_c2`), its own private document directory and its own unprivileged
> systemd unit bound to `127.0.0.1:3101`. It is **not** connected to the C1
> production runtime, the production database, production object storage, any
> network/firewall rule, or any external AI/OCR service. `/health` therefore
> reports `production_ready: false` and the capability labels
> `storage_mode=c2-local-private`, `scanner_mode=stub`, `ocr_mode=rules-only`,
> `email_delivery=disabled`. No component of this service should be described as
> production-ready.

## What it does

| Area | Behaviour |
| --- | --- |
| Identity | self-registration, bcrypt password hashes, case-insensitive unique e-mail |
| Sessions | HMAC-signed cookie/bearer token, only the SHA-256 of the token is stored, logout revokes immediately |
| Roles | `user` / `agent` / `admin` in a `user_roles` table; an account can hold several at once |
| Application | exactly one application row per account (unique `user_id`), draft → submitted → decided state machine |
| Licences | rows are updated in place, never deleted and re-inserted wholesale |
| Documents | private local disk store, opaque keys, content sniffing, short-lived signed download links bound to the owner |
| Admin | queue/detail/approve/reject/request-info/suspend/rerun-pre-review + audit stream; cross-account views are masked |
| Audit | append-only `agent_review_events`, enforced by a database trigger **and** by privileges |
| Pre-review | deterministic rules only, advisory, can never approve anything |

## Database layout

* cluster `16/goaa_c2test` (a cluster name may not contain a dash — Ubuntu's
  `postgresql@.service` substitutes `%I`, turning `-` into `/`), port `5433`,
  `listen_addresses = '127.0.0.1'`, `ssl = off`
* database `goaa_c2` — owner `goaa_c2_migrate`
* roles:
  * `goaa_c2_migrate` — owns the schema, runs migrations, performs the
    out-of-band administrator grants. `NOSUPERUSER NOCREATEDB NOCREATEROLE`.
  * `goaa_c2_app` — the runtime role used by this service. `NOSUPERUSER
    NOCREATEDB NOCREATEROLE`, no DDL, no `UPDATE`/`DELETE` on the audit trail,
    and a trigger stops it from ever minting an `admin` row.
* passwords live in `0600` pgpass files under `/opt/goaa-test/env/`; no password
  is ever placed on a command line, in an environment variable that we control
  verbatim, in the repository, or in a log.

### Database authentication posture

Administration is deliberately socket-only. `goaa_c2_app` and `goaa_c2_migrate`
are the only roles that may log in over loopback TCP, and the superuser has no
usable password at all:

* `ALTER ROLE postgres PASSWORD NULL` is applied after the bootstrap, so no
  password can ever authenticate the superuser;
* the `postgres` role is explicitly rejected on loopback TCP, and those reject
  rules sit **before** the generic SCRAM rules, so the first match wins:

  ```
  local   all   postgres                        peer
  local   all   all                             peer
  host    all   postgres        127.0.0.1/32    reject
  host    all   postgres        ::1/128         reject
  host    all   all             127.0.0.1/32    scram-sha-256
  host    all   all             ::1/128         scram-sha-256
  ```

* the superuser is therefore reachable only as the `postgres` OS account over the
  unix socket (`peer`); the service, the migrations and the test-suite never use
  it — they connect as `goaa_c2_app` / `goaa_c2_migrate` over TCP+SCRAM;
* after editing the file, reload rather than restart:
  `systemctl reload postgresql@16-goaa_c2test.service`.

Verify:

```sh
# must be rejected before authentication is even attempted
PGPASSFILE=/dev/null psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -w -c 'select 1'
# must succeed, as the postgres OS account
sudo -u postgres psql -h /var/run/postgresql -p 5433 -d postgres -c 'select current_user'
# must report the roles that still have a password (app + migrate only)
sudo -u postgres psql -h /var/run/postgresql -p 5433 -d postgres \
  -c 'select rolname, rolpassword is null from pg_authid order by 1'
```

### Migrations

`migrations/*.sql` are PostgreSQL-specific, forward-only and safe to re-run:

| File | Contents |
| --- | --- |
| `0001_identity.sql` | `schema_migrations`, `users` (case-insensitive unique e-mail), `user_roles`, `email_verifications`, `user_sessions` |
| `0002_applications.sql` | `agent_applications` (one per user), `agent_licenses`, `agent_license_documents`, `agent_review_events`, `idempotency_keys` |
| `0003_audit_append_only.sql` | `BEFORE UPDATE/DELETE` trigger that aborts, plus privilege revocation |
| `0004_role_grant_guard.sql` | trigger that stops the application role from granting/revoking `admin` |

Apply them with:

```sh
cd /opt/goaa-test/backend
GOAA_C2_DB_NAME=goaa_c2 /opt/goaa-test/venv/bin/python -m tools.migrate
GOAA_C2_DB_NAME=goaa_c2 /opt/goaa-test/venv/bin/python -m tools.migrate --status
```

## Host layout (C2)

```
/opt/goaa-test/
├── backend/                 this source tree (0750 root:goaa-c2loop)
├── env/                     0700 root:root
│   ├── app_role_password    0600, never printed
│   ├── migrate_role_password 0600, never printed
│   ├── session_secret       0600, never printed
│   ├── postgres_superuser_password 0600, legacy bootstrap secret, now inert
│   ├── .pgpass              0600 operator/bootstrap pgpass
│   ├── app.pgpass           0600 goaa-c2loop only
│   ├── migrate.pgpass       0600 operator only
│   └── goaa-c2-backend.env  0440 root:goaa-c2loop (non-secret settings)
├── log/                     0700 (reserved)
├── private-files/           0700 goaa-c2loop — uploaded documents
├── run/                     0700 (reserved)
├── venv/                    Python virtualenv (offline wheel install)
└── wheels/                  pinned wheels used for that install
```

## Install from scratch (C2, as root)

```sh
# 1. PostgreSQL 16 from the Ubuntu archive (no PGDG repository is added)
apt-get install -y --no-install-recommends postgresql-16
pg_dropcluster 16 main --stop            # only if 16/main is empty and unreferenced
pg_createcluster 16 goaa_c2test --port 5433 --start -- --pwfile=/tmp/pwfile
#    The pwfile only bootstraps the cluster: it lets the roles, databases and
#    schema be created over loopback TCP+SCRAM. Once that is done the bootstrap
#    password is cleared again (see "Database authentication posture" below), so
#    it never becomes a standing credential.

# 2. runtime + dependencies, installed offline from the pinned wheels
python3 -m venv /opt/goaa-test/venv
/opt/goaa-test/venv/bin/pip install --no-index --find-links=/opt/goaa-test/wheels -r requirements.txt

# 3. deploy the service and the unit
install -d -o root -g goaa-c2loop -m 0750 /opt/goaa-test/backend
cp -r app migrations tests tools README.md requirements*.txt /opt/goaa-test/backend/
install -m 0644 deploy/goaa-c2-agent-loop.service /etc/systemd/system/goaa-c2-agent-loop.service
systemctl daemon-reload && systemctl enable --now goaa-c2-agent-loop.service
```

## Environment reference (`goaa-c2-backend.env`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `GOAA_C2_ENV` | `c2-dev` | label reported by `/health` |
| `GOAA_C2_DB_HOST` / `_PORT` / `_NAME` | `127.0.0.1` / `5433` / `goaa_c2` | dedicated cluster |
| `GOAA_C2_DB_USER` | `goaa_c2_app` | runtime role |
| `GOAA_C2_DB_PASSFILE` | `/opt/goaa-test/env/app.pgpass` | password source (never inline) |
| `GOAA_C2_SESSION_SECRET` | – | HMAC key for session/download tokens (required) |
| `GOAA_C2_SESSION_TTL` | `43200` | session lifetime in seconds |
| `GOAA_C2_PRIVATE_FILES_DIR` | `/opt/goaa-test/private-files` | document store root |
| `GOAA_C2_DOWNLOAD_TTL` | `120` | signed link lifetime |
| `GOAA_C2_MAX_UPLOAD_BYTES` | `5242880` | upload ceiling |
| `GOAA_C2_PUBLIC_BASE_URL` | *(empty)* | set only behind a real reverse proxy |

## API surface (`/api/v1/agent-loop`)

```
POST   /auth/register            POST /auth/login        POST /auth/logout
GET    /auth/me                  POST /auth/verify-email
GET    /applications/me          PUT  /applications/me    POST /applications/me/submit
GET    /applications/{id}        (owner or admin only)
POST   /documents                GET  /documents/{id}/link  DELETE /documents/{id}
GET    /downloads/{token}
GET    /agent/panel              (requires the agent role *and* status=approved)
GET    /admin/applications       GET  /admin/applications/{id}
POST   /admin/applications/{id}/{approve|reject|request-info|suspend|rerun-ai}
GET    /admin/audit              POST /admin/users/{id}/roles   (user|agent only)
GET    /health
```

Retry-safe writes accept an `Idempotency-Key` header (submit, approve, reject,
request-info, suspend).

## Security model

* passwords: bcrypt (cost 12); the hash is never returned or logged
* sessions: signed token, only its SHA-256 persisted, revocation is immediate
  because roles and status are re-read on every request
* an explicit `Authorization: Bearer` header always wins over an ambient cookie,
  so a stale cookie can never silently authenticate a request
* administrator views mask applicant e-mail, address and licence numbers; an
  account always sees its own data unmasked
* documents: never served by path, only through a short-lived HMAC link bound to
  the owner (or an admin), with an authenticated caller
* the audit trail cannot be rewritten, even by the runtime role
* the runtime role cannot create roles/databases and cannot grant `admin`
* the service process runs unprivileged with `NoNewPrivileges`, a read-only
  filesystem except for its own data directory, `IPAddressAllow=localhost`,
  an empty capability set and a `@system-service` syscall filter

### Known limitations (deliberate, this environment only)

* no TLS listener: the cookie is `Secure=false` because the service is reachable
  on loopback only. A production deployment must terminate TLS in front and flip
  the flag.
* no real antivirus and no real OCR: `scanner_mode=stub`, `ocr_mode=rules-only`.
* e-mail delivery is disabled, so `email_verified_at` is only ever set by an
  explicit `POST /auth/verify-email` with a token an operator supplies.
* `admin` grants are an out-of-band operator action
  (`python -m tools.grant_role --email ... --role admin --confirm`), audited in
  the same append-only stream.
* the Next.js front end of the earlier prototype is **not** wired to this
  service yet; this deliverable is the backend only and leaves the existing C2
  front end untouched.

## Tests

```sh
cd /opt/goaa-test/backend
GOAA_C2_DB_NAME=goaa_c2test /opt/goaa-test/venv/bin/python -m pytest -q
```

The suite recreates the `public` schema of the dedicated **test** database
(`goaa_c2test`) from the migration files and then exercises the loop against the
real PostgreSQL 16 cluster.
