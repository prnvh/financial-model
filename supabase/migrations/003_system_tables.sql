create table system.cron_runs (
  run_id uuid primary key default extensions.gen_random_uuid(),
  trigger_type text not null check (trigger_type in ('cron', 'manual', 'webhook', 'test')),
  run_type text not null,
  status text not null check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  config_json jsonb not null default '{}'::jsonb,
  error_json jsonb,
  check (finished_at is null or finished_at >= started_at)
);

create table system.agent_runs (
  agent_run_id uuid primary key default extensions.gen_random_uuid(),
  run_id uuid references system.cron_runs(run_id),
  agent_name text not null,
  agent_role text not null,
  status text not null check (status in ('queued', 'running', 'succeeded', 'failed', 'skipped')),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  input_context_json jsonb not null default '{}'::jsonb,
  output_summary text,
  model_name text,
  token_usage_json jsonb,
  cost_estimate numeric check (cost_estimate is null or cost_estimate >= 0),
  error_json jsonb,
  check (finished_at is null or finished_at >= started_at)
);

create table system.usage_daily (
  usage_date date primary key,
  cron_runs int not null default 0,
  agent_runs int not null default 0,
  llm_calls int not null default 0,
  embedding_calls int not null default 0,
  reports_generated int not null default 0,
  raw_events_created int not null default 0,
  estimated_llm_cost numeric not null default 0,
  created_at timestamptz not null default now(),
  check (
    cron_runs >= 0
    and agent_runs >= 0
    and llm_calls >= 0
    and embedding_calls >= 0
    and reports_generated >= 0
    and raw_events_created >= 0
    and estimated_llm_cost >= 0
  )
);
