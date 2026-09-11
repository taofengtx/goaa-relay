-- 0006_golden_business_session.sql
-- Isolated candidate: bridge a *verified Clerk identity* onto the golden
-- (AI Butler) business identity, mapping by (issuer, subject) only.
--
-- What this file adds — and what it deliberately does NOT add:
--
--   Clerk (identity authority)          GOAA business authority (this file)
--   --------------------------          ----------------------------------
--   (issuer, subject)                   user_identities  -> users      (0005)
--                                       business_subject_links -> business_subjects  (new)
--   verified e-mail snapshot            never used to decide ownership
--   session token                       business_tokens (new) — same contract as
--                                       the golden `goaa_order_tokens`
--
--   * NO credential, password, OTP or Clerk session is stored here.
--   * NO agent / admin role can be produced by this path: `business_tokens.role`
--     is constrained to 'customer' in this round (the agent path is out of
--     scope and must be designed separately, not implicitly granted).
--   * The surrogate key in `business_subjects` is created by this service. The
--     local identity id in `users` (the C2 *test* identity table) is NEVER used
--     as a golden business id, and no user/order row is merged or moved.
--   * Nothing here touches `goaa_c2`, C1, the golden runtime, payments or the
--     existing authentication code. Target database for this round: goaa_c2test.
--
-- BUSINESS CONTRACT COMPATIBILITY (the reason this file looks like this)
-- ---------------------------------------------------------------------
-- The golden runtime authenticates a business caller with exactly:
--
--   runtime/order_db.py::authenticate_order_token
--     SELECT user_id, role FROM goaa_order_tokens WHERE token=%s AND revoked_at IS NULL
--   runtime/order_db.py::issue_order_token
--     INSERT INTO goaa_order_tokens (user_id, token, role) VALUES (%s,%s,%s)
--   runtime/order_db.py::revoke_order_tokens
--     UPDATE goaa_order_tokens SET revoked_at=now() WHERE user_id=%s
--
-- `business_tokens` below reproduces that shape and those semantics column for
-- column, so the golden authentication function applies to it verbatim with
-- only the table name changed (proved in tests/test_golden_business_contract.py,
-- which reads the golden SQL out of the golden clone rather than restating it).
-- Consequences that are deliberate, not accidental:
--
--   * `token` holds the same opaque value the caller presents (the golden
--     mechanism stores it as-is); it is not a digest.
--   * Revocation is the only way a token stops being accepted; there is no
--     expiry column, because the golden authentication function does not read
--     one and an expiry only this service honoured would be a second truth.
--   * The golden INSERT ends in `ON CONFLICT (user_id, token) DO NOTHING`, so
--     the pair must carry a unique constraint for that clause to be valid at
--     all — `business_tokens_user_token_key` below exists for exactly that
--     reason (found by running the golden statement, not by reading it).
--   * `user_id` references the *business* principal (business_subjects), which
--     plays the role `goaa_order_users.id` plays in the golden schema. It is
--     never the C2 test identity id.
--   * `last_used_at` and `issued_at` are additive bookkeeping columns the
--     golden function ignores; they change no decision it makes.
--
-- Forward-only. Applying it requires an explicit operator action; the candidate
-- is delivered as a file only (no migration is executed as part of this round).

\set ON_ERROR_STOP on

-- ---------------------------------------------------------------------------
-- business_subjects: the golden business principal (customer side, first).
--
-- Kept separate from `users` on purpose: `users` is the identity/credential
-- side (Clerk mapping), `business_subjects` is the business side that matters
-- and orders can hang off. One row per real business principal.
-- ---------------------------------------------------------------------------
create table if not exists business_subjects (
    id         uuid        primary key default gen_random_uuid(),
    kind       text        not null default 'customer',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint business_subjects_kind_known check (kind in ('customer'))
);

-- ---------------------------------------------------------------------------
-- business_subject_links: the one-to-one binding identity -> business subject.
--
--   user_id  PRIMARY KEY -> one identity row owns at most one business subject
--   subject_id UNIQUE    -> one business subject is owned by at most one identity
--
-- Both directions are enforced in the database, so a bug in the service can
-- never silently fuse two identities onto one business principal. No e-mail
-- column exists here: an address can never become the join key.
-- ---------------------------------------------------------------------------
create table if not exists business_subject_links (
    user_id    uuid        primary key references users (id) on delete cascade,
    subject_id uuid        not null unique references business_subjects (id) on delete cascade,
    linked_via text        not null default 'clerk_issuer_subject',
    issuer     text        not null,
    subject    text        not null,
    created_at timestamptz not null default now(),
    constraint business_subject_links_via_known check (linked_via in ('clerk_issuer_subject'))
);

-- ---------------------------------------------------------------------------
-- business_tokens: the opaque business credential, in the golden contract.
--
-- Shape mirrors `goaa_order_tokens` (see the header): the same columns the
-- golden authentication function reads, the same revocation semantics, and the
-- same "the token value is what the caller presents" rule. `role` is pinned to
-- 'customer' for this round by a CHECK constraint, so neither the service nor a
-- later edit can mint an agent/admin business credential here.
--
-- One live token per principal is maintained by the service (issuing rotates);
-- the database still allows the golden's own shape (several rows per user).
-- ---------------------------------------------------------------------------
create table if not exists business_tokens (
    id           uuid        primary key default gen_random_uuid(),
    user_id      uuid        not null references business_subjects (id) on delete cascade,
    token        text        not null unique,
    role         text        not null,
    created_at   timestamptz not null default now(),
    issued_at    timestamptz not null default now(),
    last_used_at timestamptz,
    revoked_at   timestamptz,
    constraint business_tokens_role_known check (role in ('customer')),
    constraint business_tokens_user_token_key unique (user_id, token)
);

-- The golden lookup is `token = %s AND revoked_at IS NULL`; the unique index on
-- `token` already serves it. These two help the sign-out and rotation paths.
create index if not exists business_tokens_user_idx on business_tokens (user_id);
create index if not exists business_tokens_live_user_idx
    on business_tokens (user_id) where revoked_at is null;

-- ---------------------------------------------------------------------------
-- identity_events: allow the business events of this bridge.
--
-- 0005 pinned the event vocabulary with a CHECK constraint, so a new event type
-- must be added by migration — silently widening an audit vocabulary would
-- defeat the constraint. The business events carry no token and no e-mail
-- value; `email_masked` stays masked, exactly as in 0005.
-- ---------------------------------------------------------------------------
alter table identity_events drop constraint if exists identity_events_type_known;
alter table identity_events add constraint identity_events_type_known check (
    event_type in (
        'identity.jit_create',
        'identity.bind',
        'identity.unbind',
        'identity.conflict',
        'identity.identifier_snapshot',
        'identity.recovery',
        'business.subject_linked',
        'business.token_issued',
        'business.token_revoked',
        'business.token_rejected'
    )
);

-- ---------------------------------------------------------------------------
-- grants: least privilege for the application role only.
-- The migration role owns the new objects; the app role may read the subject
-- rows and manage tokens. No DELETE anywhere: revocation is an UPDATE of
-- `revoked_at`, so history is preserved for the audit trail.
-- ---------------------------------------------------------------------------
grant select, insert on business_subjects to goaa_c2_app;
grant select, insert on business_subject_links to goaa_c2_app;
grant select, insert, update on business_tokens to goaa_c2_app;

-- ---------------------------------------------------------------------------
-- record the migration (same table/format the tooling already uses).
-- ---------------------------------------------------------------------------
insert into schema_migrations (version) values ('0006_golden_business_session')
    on conflict (version) do nothing;
