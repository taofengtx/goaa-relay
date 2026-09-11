-- 0004_role_grant_guard.sql
-- The runtime application role must be able to grant the `agent` role (that is
-- what an approval does) but must never be able to mint an administrator —
-- not even if a SQL injection ever reached an INSERT/UPDATE/DELETE on
-- user_roles. Administrator grants are an out-of-band operator action performed
-- as the schema-owning migration role.
-- Forward-only and safe to re-run.

\set ON_ERROR_STOP on

create or replace function goaa_c2_guard_user_roles()
returns trigger
language plpgsql
as $$
begin
    if session_user = 'goaa_c2_app' then
        if tg_op = 'INSERT' and new.role = 'admin' then
            raise exception 'the application role may not grant the admin role'
                using errcode = 'insufficient_privilege';
        end if;
        if tg_op = 'UPDATE' and (old.role = 'admin' or new.role = 'admin') then
            raise exception 'the application role may not modify the admin role'
                using errcode = 'insufficient_privilege';
        end if;
        if tg_op = 'DELETE' and old.role = 'admin' then
            raise exception 'the application role may not revoke the admin role'
                using errcode = 'insufficient_privilege';
        end if;
    end if;
    if tg_op = 'DELETE' then
        return old;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_user_roles_guard on user_roles;
create trigger trg_user_roles_guard
    before insert or update or delete on user_roles
    for each row execute function goaa_c2_guard_user_roles();

insert into schema_migrations (version) values ('0004_role_grant_guard')
    on conflict (version) do nothing;
