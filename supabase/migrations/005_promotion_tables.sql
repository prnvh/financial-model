create table promotion.working_memory_notes (
  note_id uuid primary key default extensions.gen_random_uuid(),
  run_id uuid references system.cron_runs(run_id),
  agent_run_id uuid references system.agent_runs(agent_run_id),
  source_agent text not null,
  note_type text not null check (note_type in ('agent', 'tool_result', 'system', 'user')),
  raw_text text not null,
  source_ref text,
  processed_by_promotion boolean not null default false,
  promoted_at timestamptz,
  created_at timestamptz not null default now()
);

create table promotion.promotion_attempts (
  attempt_id uuid primary key default extensions.gen_random_uuid(),
  note_id uuid not null references promotion.working_memory_notes(note_id),
  run_id uuid references system.cron_runs(run_id),
  source_agent text not null,
  attempt_status text not null check (
    attempt_status in ('interpreted', 'committed', 'provisional', 'rejected', 'failed')
  ),
  interpreter_decision text check (interpreter_decision in ('accept', 'reject')),
  resolver_decision text check (resolver_decision in ('commit', 'provisional', 'reject')),
  validator_decision text check (validator_decision in ('pass', 'fail')),
  bucket text,
  operation text,
  target_id text,
  write_request_json jsonb,
  resolved_write_json jsonb,
  validator_errors_json jsonb,
  error_json jsonb,
  created_at timestamptz not null default now()
);

create table promotion.pending_memory_events (
  pending_id uuid primary key default extensions.gen_random_uuid(),
  original_attempt_id uuid references promotion.promotion_attempts(attempt_id),
  note_id uuid references promotion.working_memory_notes(note_id),
  source_agent text,
  raw_input text,
  bucket text not null,
  operation text not null,
  target_id text,
  reference_text text,
  reason text not null default 'unspecified',
  payload_json jsonb not null default '{}'::jsonb,
  candidate_aliases_json jsonb not null default '[]'::jsonb,
  candidate_matches_json jsonb not null default '[]'::jsonb,
  confidence numeric check (confidence is null or (confidence >= 0 and confidence <= 1)),
  original_write_request_json jsonb not null,
  status text not null default 'open' check (status in ('open', 'on_hold', 'committed', 'rejected')),
  retry_count int not null default 0 check (retry_count >= 0),
  last_retry_at timestamptz,
  last_retry_reason text,
  next_retry_after timestamptz,
  final_event_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger set_pending_memory_events_updated_at
before update on promotion.pending_memory_events
for each row
execute function system.set_updated_at();
