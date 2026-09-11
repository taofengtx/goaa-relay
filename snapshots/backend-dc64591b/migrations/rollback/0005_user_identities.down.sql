-- 0005_user_identities.down.sql  —  ROLLBACK for 0005_user_identities.sql
--
-- NOT a migration. This file lives in `rollback/` on purpose: tools/migrate.py
-- globs `migrations/*.sql` non-recursively, so anything parked here is never
-- auto-applied. Run it by hand, only on goaa_c2test, only to undo 0005.
--
-- Deliberately does NOT restore `users.password_hash` / `users.email` NOT NULL:
-- re-adding the constraints would fail if any credential-less row already
-- exists, and the relaxation is harmless to the legacy code paths. Recorded in
-- the report instead.

\set ON_ERROR_STOP on

begin;

drop trigger if exists trg_identity_events_append_only on identity_events;
drop function if exists goaa_c2_identity_events_append_only();

drop table if exists identity_events;
drop table if exists user_identities;

delete from schema_migrations where version = '0005_user_identities';

commit;
