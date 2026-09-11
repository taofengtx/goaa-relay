-- 0005_user_identities.sql
-- Clerk becomes the single identity authority for GOAA. PostgreSQL stops being
-- a credential store and becomes a *mapping* store:
--
--   Clerk (identity authority)            GOAA PostgreSQL (business authority)
--   ---------------------------           ----------------------------------
--   Clerk user id  ->  subject            user_identities  (issuer, subject) -> user_id
--   Google / email / phone identifiers    nothing but a verified snapshot
--   password / OTP / session              never stored here
--
-- Two invariants this file enforces at the database level:
--   1. (issuer, subject) is unique  -> one Clerk user maps to at most one GOAA user.
--   2. (user_id, provider) is unique -> one GOAA user has at most one Clerk identity.
-- Neither direction may ever be decided by matching on an e-mail address.
--
-- Forward-only and safe to re-run. Target database for this round: goaa_c2test.
-- (goaa_c2 and C1 are NOT migrated.)

\set ON_ERROR_STOP on

-- ---------------------------------------------------------------------------
-- users: allow a credential-less, e-mail-less account.
--
-- Clerk owns every credential, so GOAA never writes a password again. The
-- `+1` SMS-OTP registration path is also first-class, which means a legitimate
-- account can exist with no e-mail address at all. Both columns therefore have
-- to lose their NOT NULL, otherwise a phone-only Clerk user cannot be
-- represented. Rows created before this migration are untouched.
--
--   * password_hash IS NULL  -> this account has no GOAA password, by design.
--     Any legacy password login MUST fail closed on a NULL hash rather than
--     compare against it.
--   * the existing lower(email) unique index already permits multiple NULLs,
--     so no index change is required.
-- ---------------------------------------------------------------------------
alter table users alter column password_hash drop not null;
alter table users alter column email         drop not null;

-- ---------------------------------------------------------------------------
-- user_identities: the (issuer, subject) -> user_id mapping table.
--
-- `subject` is the stable Clerk user id (e.g. user_2abc...). It is the only
-- identity key. `email_snapshot` / `email_verified` are *snapshots* taken from
-- the verified Clerk session and are never used to decide account ownership.
-- ---------------------------------------------------------------------------
create table if not exists user_identities (
    id             uuid        primary key default gen_random_uuid(),
    user_id        uuid        not null references users (id) on delete cascade,
    provider       text        not null default 'clerk',
    issuer         text        not null,
    subject        text        not null,
    email_snapshot text,
    email_verified boolean     not null default false,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    constraint user_identities_provider_fixed
        check (provider = 'clerk'),
    constraint user_identities_issuer_not_blank
        check (length(btrim(issuer)) > 0),
    constraint user_identities_subject_not_blank
        check (length(btrim(subject)) > 0)
);

-- (issuer, subject) unique: one Clerk user -> at most one GOAA user.
create unique index if not exists user_identities_issuer_subject_key
    on user_identities (issuer, subject);

-- (user_id, provider) unique: one GOAA user -> at most one Clerk identity.
create unique index if not exists user_identities_user_provider_key
    on user_identities (user_id, provider);

create index if not exists user_identities_user_idx
    on user_identities (user_id);

-- Deliberately NOT unique on lower(email_snapshot): two different Clerk users
-- may legitimately present the same unverified snapshot address, and a shared
-- address must never merge accounts. Conflicts are surfaced by the
-- application (fail closed) and recorded in identity_events.
create index if not exists user_identities_email_snapshot_idx
    on user_identities (lower(email_snapshot))
    where email_snapshot is not null;

-- ---------------------------------------------------------------------------
-- identity_events: append-only audit for every bind / unbind / conflict, and
-- for every verified-identifier snapshot change (e-mail, phone, provider).
--
-- Never stores a token, an OTP, a session id or a secret: only the outcome and
-- the identifiers' *existence*, with the e-mail masked by the caller.
-- ---------------------------------------------------------------------------
create table if not exists identity_events (
    id              uuid        primary key default gen_random_uuid(),
    occurred_at     timestamptz not null default now(),
    event_type      text        not null,
    actor_user_id   uuid        references users (id) on delete set null,
    subject_user_id uuid        references users (id) on delete set null,
    provider        text,
    issuer          text,
    subject         text,
    email_masked    text,
    detail          jsonb       not null default '{}'::jsonb,
    constraint identity_events_type_known check (
        event_type in (
            'identity.jit_create',      -- first login: clerk subject -> new user
            'identity.bind',            -- existing user bound to a clerk subject
            'identity.unbind',          -- binding removed (must keep a factor)
            'identity.conflict',        -- subject/identifier already owned -> fail closed
            'identity.identifier_snapshot', -- verified e-mail/phone snapshot changed
            'identity.recovery'         -- access recovered via a verified factor
        )
    ),
    constraint identity_events_detail_is_object
        check (jsonb_typeof(detail) = 'object')
);

create index if not exists identity_events_created_idx
    on identity_events (occurred_at desc);
create index if not exists identity_events_subject_user_idx
    on identity_events (subject_user_id, occurred_at desc);

-- Append-only, enforced inside PostgreSQL (mirrors 0003_audit_append_only.sql).
create or replace function goaa_c2_identity_events_append_only()
returns trigger
language plpgsql
as $$
begin
    raise exception
        'identity_events is append-only: % is not permitted', tg_op
        using errcode = 'restrict_violation';
end;
$$;

drop trigger if exists trg_identity_events_append_only on identity_events;
create trigger trg_identity_events_append_only
    before update or delete on identity_events
    for each row execute function goaa_c2_identity_events_append_only();

-- ---------------------------------------------------------------------------
-- explicit grants
-- ---------------------------------------------------------------------------
grant select, insert, update on user_identities to goaa_c2_app;
grant select, insert         on identity_events to goaa_c2_app;
revoke update, delete, truncate on identity_events from goaa_c2_app;

insert into schema_migrations (version) values ('0005_user_identities')
    on conflict (version) do nothing;
