-- 0001_identity.sql
-- PostgreSQL-native (schema is NOT a port of the SQLite prototype: identities
-- are normalised into one `users` row plus a `user_roles` grant table).
-- Forward-only and safe to re-run.

\set ON_ERROR_STOP on

create table if not exists schema_migrations (
    version    text primary key,
    applied_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- users: one identity per human. E-mail is unique case-insensitively.
-- ---------------------------------------------------------------------------
create table if not exists users (
    id                uuid primary key default gen_random_uuid(),
    email             text        not null,
    password_hash     text        not null,
    full_name         text,
    phone             text,
    address           text,
    email_verified_at timestamptz,
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now(),
    constraint users_email_not_blank check (length(btrim(email)) >= 3),
    constraint users_email_has_at    check (position('@' in email) > 1)
);

create unique index if not exists users_email_lower_key on users (lower(email));

create index if not exists users_created_at_idx on users (created_at desc);

-- ---------------------------------------------------------------------------
-- user_roles: many-to-many so one account can hold several roles at once.
-- ---------------------------------------------------------------------------
create table if not exists user_roles (
    user_id    uuid        not null references users (id) on delete cascade,
    role       text        not null,
    granted_at timestamptz not null default now(),
    granted_by uuid        references users (id) on delete set null,
    primary key (user_id, role),
    constraint user_roles_role_known check (role in ('user', 'agent', 'admin'))
);

create index if not exists user_roles_role_idx on user_roles (role);

-- ---------------------------------------------------------------------------
-- email_verifications: token *hashes* only; no plaintext token is persisted.
-- ---------------------------------------------------------------------------
create table if not exists email_verifications (
    id            uuid primary key default gen_random_uuid(),
    user_id       uuid        not null references users (id) on delete cascade,
    email         text        not null,
    token_hash    text        not null unique,
    created_at    timestamptz not null default now(),
    expires_at    timestamptz not null,
    consumed_at   timestamptz
);

create index if not exists email_verifications_user_idx on email_verifications (user_id);

-- ---------------------------------------------------------------------------
-- user_sessions: the cookie carries a signed token; we store only its SHA-256.
-- Revocation is immediate because roles/status are re-read on every request.
-- ---------------------------------------------------------------------------
create table if not exists user_sessions (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid        not null references users (id) on delete cascade,
    token_hash text        not null unique,
    issued_at  timestamptz not null default now(),
    expires_at timestamptz not null,
    revoked_at timestamptz
);

create index if not exists user_sessions_user_live_idx
    on user_sessions (user_id) where revoked_at is null;

-- ---------------------------------------------------------------------------
-- explicit grants (do not rely solely on default privileges)
-- ---------------------------------------------------------------------------
grant select, insert, update, delete on users               to goaa_c2_app;
grant select, insert, update, delete on user_roles          to goaa_c2_app;
grant select, insert, update, delete on email_verifications to goaa_c2_app;
grant select, insert, update, delete on user_sessions       to goaa_c2_app;
grant select on schema_migrations                           to goaa_c2_app;

insert into schema_migrations (version) values ('0001_identity')
    on conflict (version) do nothing;
