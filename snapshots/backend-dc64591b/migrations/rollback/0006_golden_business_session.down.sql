-- 0006_golden_business_session.down.sql — rollback for the isolated candidate.
--
-- Not executed in this round. `tools/migrate.py` scans `migrations/*.sql`
-- non-recursively, so this file lives in `migrations/rollback/` and is only
-- ever run by hand.
--
-- Order matters: the grants go first (they are the only thing granted to the
-- application role), then the indexes and tables, then the audit vocabulary is
-- restored to exactly what 0005 pinned, then the migration marker is removed.
-- Nothing here touches `user_identities`, `users`, `identity_events` rows, or
-- any other database.

\set ON_ERROR_STOP on

revoke all on business_tokens from goaa_c2_app;
revoke all on business_subject_links from goaa_c2_app;
revoke all on business_subjects from goaa_c2_app;

drop index if exists business_tokens_live_user_idx;
drop index if exists business_tokens_user_idx;
drop table if exists business_tokens;
drop table if exists business_subject_links;
drop table if exists business_subjects;

-- restore the 0005 vocabulary verbatim.
alter table identity_events drop constraint if exists identity_events_type_known;
alter table identity_events add constraint identity_events_type_known check (
    event_type in (
        'identity.jit_create',
        'identity.bind',
        'identity.unbind',
        'identity.conflict',
        'identity.identifier_snapshot',
        'identity.recovery'
    )
);

delete from schema_migrations where version = '0006_golden_business_session';
