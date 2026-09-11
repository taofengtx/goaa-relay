-- 0002_applications.sql
-- The application / licence / document / audit model for the C2 environment.
-- Forward-only and safe to re-run.

\set ON_ERROR_STOP on

-- ---------------------------------------------------------------------------
-- agent_applications: exactly one application record per user account
-- (the "apply with the same account you registered with" invariant).
-- ---------------------------------------------------------------------------
create table if not exists agent_applications (
    id                 uuid primary key default gen_random_uuid(),
    user_id            uuid        not null unique references users (id) on delete cascade,
    status             text        not null default 'draft',
    full_name          text,
    phone              text,
    email              text,
    address            text,
    terms_accepted_at  timestamptz,
    submitted_at       timestamptz,
    decided_at         timestamptz,
    decision_reason    text,
    decided_by         uuid        references users (id) on delete set null,
    pre_review         jsonb,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now(),
    constraint agent_applications_status_known check (
        status in ('draft', 'submitted', 'info_requested', 'approved', 'rejected', 'suspended')
    )
);

create index if not exists agent_applications_status_idx on agent_applications (status, submitted_at);

-- ---------------------------------------------------------------------------
-- agent_licenses: stable rows, updated in place (no delete/re-insert churn).
-- ---------------------------------------------------------------------------
create table if not exists agent_licenses (
    id             uuid primary key default gen_random_uuid(),
    application_id uuid        not null references agent_applications (id) on delete cascade,
    license_type   text        not null,
    license_number text        not null,
    issuer         text,
    jurisdiction   text,
    expires_on     date,
    no_expiry      boolean     not null default false,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    constraint agent_licenses_type_not_blank   check (length(btrim(license_type)) > 0),
    constraint agent_licenses_number_not_blank check (length(btrim(license_number)) > 0),
    constraint agent_licenses_expiry_present   check (no_expiry or expires_on is not null)
);

create index if not exists agent_licenses_application_idx on agent_licenses (application_id);

-- ---------------------------------------------------------------------------
-- agent_license_documents: private uploads. `storage_key` is opaque and the
-- store is local-private (no object storage / CDN in this environment).
-- ---------------------------------------------------------------------------
create table if not exists agent_license_documents (
    id             uuid primary key default gen_random_uuid(),
    application_id uuid        not null references agent_applications (id) on delete cascade,
    license_id     uuid        references agent_licenses (id) on delete set null,
    owner_user_id  uuid        not null references users (id) on delete cascade,
    side           text        not null,
    mime_type      text        not null,
    size_bytes     bigint      not null,
    sha256         text        not null,
    storage_key    text        not null,
    storage_label  text        not null default 'c2-local-private',
    scan_status    text        not null default 'stub',
    scanner        text        not null default 'stub',
    ocr_mode       text        not null default 'rules-only',
    uploaded_at    timestamptz not null default now(),
    deleted_at     timestamptz,
    constraint agent_license_documents_side_known check (side in ('front', 'back', 'id', 'credential')),
    constraint agent_license_documents_size_positive check (size_bytes > 0),
    constraint agent_license_documents_mime_known check (
        mime_type in ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')
    )
);

create index if not exists agent_license_documents_app_idx
    on agent_license_documents (application_id) where deleted_at is null;
create index if not exists agent_license_documents_owner_idx
    on agent_license_documents (owner_user_id) where deleted_at is null;

-- ---------------------------------------------------------------------------
-- agent_review_events: append-only audit trail (see 0003 for the enforcement).
-- ---------------------------------------------------------------------------
create table if not exists agent_review_events (
    id             bigint generated always as identity primary key,
    application_id uuid        references agent_applications (id) on delete cascade,
    user_id        uuid,
    actor_user_id  uuid,
    actor_role     text,
    action         text        not null,
    detail         jsonb       not null default '{}'::jsonb,
    created_at     timestamptz not null default now(),
    constraint agent_review_events_action_not_blank check (length(btrim(action)) > 0)
);

create index if not exists agent_review_events_app_idx on agent_review_events (application_id, created_at);
create index if not exists agent_review_events_created_idx on agent_review_events (created_at desc);

-- ---------------------------------------------------------------------------
-- idempotency_keys: makes approve/submit safe to retry.
-- ---------------------------------------------------------------------------
create table if not exists idempotency_keys (
    key             text primary key,
    user_id         uuid        not null references users (id) on delete cascade,
    endpoint        text        not null,
    response_status integer     not null,
    response_body   jsonb       not null,
    created_at      timestamptz not null default now()
);

create index if not exists idempotency_keys_user_idx on idempotency_keys (user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- explicit grants
-- ---------------------------------------------------------------------------
grant select, insert, update, delete on agent_applications        to goaa_c2_app;
grant select, insert, update, delete on agent_licenses            to goaa_c2_app;
grant select, insert, update, delete on agent_license_documents   to goaa_c2_app;
grant select, insert                 on agent_review_events       to goaa_c2_app;
grant select, insert, update, delete on idempotency_keys          to goaa_c2_app;
grant usage, select on all sequences in schema public             to goaa_c2_app;

insert into schema_migrations (version) values ('0002_applications')
    on conflict (version) do nothing;
