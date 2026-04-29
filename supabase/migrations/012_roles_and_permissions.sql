do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'agent_writer') then
    create role agent_writer nologin;
  end if;

  if not exists (select 1 from pg_roles where rolname = 'promotion_worker') then
    create role promotion_worker nologin;
  end if;

  if not exists (select 1 from pg_roles where rolname = 'sml_reader') then
    create role sml_reader nologin;
  end if;

  if not exists (select 1 from pg_roles where rolname = 'report_writer') then
    create role report_writer nologin;
  end if;

  if not exists (select 1 from pg_roles where rolname = 'admin') then
    create role admin nologin;
  end if;
end;
$$;

grant agent_writer, promotion_worker, sml_reader, report_writer to admin;

revoke all on schema system from public;
revoke all on schema raw from public;
revoke all on schema promotion from public;
revoke all on schema ledger from public;
revoke all on schema sml from public;
revoke all on schema deliverables from public;
revoke all on schema audit from public;

grant usage on schema system, raw, promotion, sml to agent_writer;
grant usage on schema system, raw, promotion, ledger, sml to promotion_worker;
grant usage on schema sml to sml_reader;
grant usage on schema raw, system, ledger, sml, deliverables, audit to report_writer;
grant usage on schema system, raw, promotion, ledger, sml, deliverables, audit to admin;

grant select on system.cron_runs to agent_writer;
grant select, insert, update on system.agent_runs to agent_writer;
grant insert on raw.agent_events to agent_writer;
grant insert on promotion.working_memory_notes to agent_writer;
grant select on all tables in schema sml to agent_writer;

grant select on all tables in schema system to promotion_worker;
grant select on raw.agent_events, raw.documents, raw.document_chunks to promotion_worker;
grant select, insert, update on all tables in schema promotion to promotion_worker;
grant select, insert, update on ledger.events_memory to promotion_worker;
grant select, insert, update on all tables in schema sml to promotion_worker;

grant select on all tables in schema sml to sml_reader;

grant select on all tables in schema system to report_writer;
grant select on raw.agent_events, raw.documents, raw.document_chunks to report_writer;
grant select on ledger.events_memory, ledger.failed_projections to report_writer;
grant select on all tables in schema sml to report_writer;
grant select on audit.sml_snapshots, audit.human_actions to report_writer;
grant select, insert, update on all tables in schema deliverables to report_writer;

grant all privileges on all tables in schema system, raw, promotion, ledger, sml, deliverables, audit to admin;
grant all privileges on all sequences in schema system, raw, promotion, ledger, sml, deliverables, audit to admin;
grant execute on all functions in schema system, raw, promotion, ledger, sml, deliverables, audit to admin;

revoke all on function raw.match_document_chunks(extensions.vector, integer, uuid) from public;
grant execute on function raw.match_document_chunks(extensions.vector, integer, uuid) to agent_writer, promotion_worker, sml_reader, report_writer, admin;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    grant usage on schema system, raw, promotion, ledger, sml, deliverables, audit to service_role;
    grant all privileges on all tables in schema system, raw, promotion, ledger, sml, deliverables, audit to service_role;
    grant all privileges on all sequences in schema system, raw, promotion, ledger, sml, deliverables, audit to service_role;
    grant execute on all functions in schema system, raw, promotion, ledger, sml, deliverables, audit to service_role;
  end if;

  if exists (select 1 from pg_roles where rolname = 'anon') then
    revoke usage on schema system, raw, promotion, ledger, sml, deliverables, audit from anon;
    revoke all privileges on all tables in schema system, raw, promotion, ledger, sml, deliverables, audit from anon;
    revoke all privileges on all sequences in schema system, raw, promotion, ledger, sml, deliverables, audit from anon;
  end if;

  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    revoke usage on schema system, raw, promotion, ledger, sml, deliverables, audit from authenticated;
    revoke all privileges on all tables in schema system, raw, promotion, ledger, sml, deliverables, audit from authenticated;
    revoke all privileges on all sequences in schema system, raw, promotion, ledger, sml, deliverables, audit from authenticated;
  end if;
end;
$$;
