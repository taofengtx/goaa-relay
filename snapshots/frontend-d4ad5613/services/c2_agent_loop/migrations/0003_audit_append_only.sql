-- 0003_audit_append_only.sql
-- Make the audit trail append-only *inside PostgreSQL*, not merely by
-- convention in the application code. Two independent layers:
--   1. a trigger that aborts any UPDATE/DELETE/TRUNCATE on the table;
--   2. table privileges that never grant UPDATE/DELETE/TRUNCATE to the app role.
-- Forward-only and safe to re-run.

\set ON_ERROR_STOP on

create or replace function goaa_c2_review_events_append_only()
returns trigger
language plpgsql
as $$
begin
    raise exception
        'agent_review_events is append-only: % is not permitted', tg_op
        using errcode = 'restrict_violation';
end;
$$;

drop trigger if exists trg_agent_review_events_append_only on agent_review_events;
create trigger trg_agent_review_events_append_only
    before update or delete on agent_review_events
    for each row execute function goaa_c2_review_events_append_only();

-- TRUNCATE bypasses row triggers, so it is forbidden for the application role.
revoke update, delete, truncate on agent_review_events from goaa_c2_app;
grant select, insert on agent_review_events to goaa_c2_app;

-- The identity column's sequence must stay usable for inserts.
grant usage, select on all sequences in schema public to goaa_c2_app;

insert into schema_migrations (version) values ('0003_audit_append_only')
    on conflict (version) do nothing;
