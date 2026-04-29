create table ledger.events_memory (
  event_id uuid primary key default extensions.gen_random_uuid(),
  timestamp timestamptz not null default now(),
  source_agent text not null,
  source_attempt_id uuid references promotion.promotion_attempts(attempt_id),
  bucket text not null,
  target_id text not null,
  operation text not null,
  payload_json jsonb not null default '{}'::jsonb,
  raw_input text,
  source_ref text,
  applied_successfully boolean not null default false,
  projection_error_json jsonb,
  created_at timestamptz not null default now()
);

alter table promotion.pending_memory_events
add constraint pending_memory_events_final_event_id_fkey
foreign key (final_event_id) references ledger.events_memory(event_id);

create or replace function ledger.guard_events_memory_mutation()
returns trigger
language plpgsql
as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'ledger.events_memory is append-only and rows cannot be deleted';
  end if;

  if not (
    current_user in ('postgres', 'service_role')
    or exists (
      select 1
      from pg_roles
      where rolname = 'promotion_worker'
        and pg_has_role(current_user, oid, 'member')
    )
    or exists (
      select 1
      from pg_roles
      where rolname = 'admin'
        and pg_has_role(current_user, oid, 'member')
    )
  ) then
    raise exception 'only controlled projection roles may update ledger.events_memory';
  end if;

  if new.event_id is distinct from old.event_id
    or new.timestamp is distinct from old.timestamp
    or new.source_agent is distinct from old.source_agent
    or new.source_attempt_id is distinct from old.source_attempt_id
    or new.bucket is distinct from old.bucket
    or new.target_id is distinct from old.target_id
    or new.operation is distinct from old.operation
    or new.payload_json is distinct from old.payload_json
    or new.raw_input is distinct from old.raw_input
    or new.source_ref is distinct from old.source_ref
    or new.created_at is distinct from old.created_at then
    raise exception 'only applied_successfully and projection_error_json may be updated in ledger.events_memory';
  end if;

  return new;
end;
$$;

create trigger guard_events_memory_mutation
before update or delete on ledger.events_memory
for each row
execute function ledger.guard_events_memory_mutation();
