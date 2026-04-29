create table sml.docs (
  doc_id text primary key,
  doc_type text not null check (
    doc_type in ('strategy', 'thesis', 'learning', 'constraint', 'watchlist', 'framework', 'note')
  ),
  title text not null,
  status text not null default 'active' check (status in ('active', 'superseded', 'archived', 'invalidated')),
  body text,
  payload_json jsonb not null default '{}'::jsonb,
  version int not null default 1 check (version >= 1),
  first_seen_event_id uuid references ledger.events_memory(event_id),
  last_event_id uuid references ledger.events_memory(event_id),
  reference_memory_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table sml.portfolio_items (
  item_id text primary key,
  name text not null,
  symbol text,
  market text,
  asset_type text not null default 'equity',
  status text not null default 'watchlist'
    check (status in ('watchlist', 'active_position', 'closed', 'rejected', 'archived')),
  position_status text not null default 'not_held'
    check (position_status in ('not_held', 'held', 'partially_closed', 'closed')),
  official_entry numeric,
  entry_range_json jsonb not null default '{}'::jsonb,
  exit_range_json jsonb not null default '{}'::jsonb,
  thesis text,
  risks_json jsonb not null default '[]'::jsonb,
  learnings_json jsonb not null default '[]'::jsonb,
  payload_json jsonb not null default '{}'::jsonb,
  first_seen_event_id uuid references ledger.events_memory(event_id),
  last_event_id uuid references ledger.events_memory(event_id),
  reference_memory_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table sml.portfolio_item_notes (
  note_id text primary key,
  item_id text not null references sml.portfolio_items(item_id),
  note_type text not null check (
    note_type in ('risk', 'entry_plan', 'exit_plan', 'learning', 'issue', 'decision', 'result')
  ),
  status text not null default 'active'
    check (status in ('active', 'resolved', 'superseded', 'invalidated', 'archived')),
  title text,
  body text,
  payload_json jsonb not null default '{}'::jsonb,
  first_seen_event_id uuid references ledger.events_memory(event_id),
  last_event_id uuid references ledger.events_memory(event_id),
  reference_memory_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table sml.news_items (
  news_item_id text primary key,
  title text not null,
  status text not null default 'active'
    check (status in ('active', 'stale', 'superseded', 'dismissed', 'archived')),
  source_type text,
  source_uri text,
  related_entities_json jsonb not null default '[]'::jsonb,
  related_docs_json jsonb not null default '[]'::jsonb,
  summary text,
  researched_summary text,
  impact text check (impact in ('positive', 'negative', 'mixed', 'neutral', 'unknown')),
  severity text check (severity in ('low', 'medium', 'high', 'critical')),
  valid_until timestamptz,
  payload_json jsonb not null default '{}'::jsonb,
  first_seen_event_id uuid references ledger.events_memory(event_id),
  last_event_id uuid references ledger.events_memory(event_id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table sml.deliverable_refs (
  deliverable_id text primary key,
  deliverable_type text not null check (
    deliverable_type in ('daily_brief', 'ticker_report', 'trade_memo', 'risk_review', 'post_trade_review')
  ),
  title text not null,
  status text not null default 'draft'
    check (status in ('draft', 'final', 'superseded', 'archived', 'rejected')),
  subject_entities_json jsonb not null default '[]'::jsonb,
  storage_bucket text,
  storage_path text,
  source_events_json jsonb not null default '[]'::jsonb,
  source_snapshot_id uuid,
  human_decision text,
  decision_notes text,
  first_seen_event_id uuid references ledger.events_memory(event_id),
  last_event_id uuid references ledger.events_memory(event_id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table sml.system_issues (
  issue_id text primary key,
  title text not null,
  description text,
  status text not null default 'open'
    check (status in ('open', 'resolved', 'invalidated', 'archived')),
  severity text check (severity in ('low', 'medium', 'high', 'critical')),
  entity_type text,
  entity_id text,
  payload_json jsonb not null default '{}'::jsonb,
  first_seen_event_id uuid references ledger.events_memory(event_id),
  last_event_id uuid references ledger.events_memory(event_id),
  reference_memory_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table sml.task_states (
  task_id text primary key,
  status text not null
    check (status in ('pending', 'in_progress', 'blocked', 'done', 'failed', 'cancelled')),
  phase text,
  owner_agent text,
  blockers_json jsonb not null default '[]'::jsonb,
  payload_json jsonb not null default '{}'::jsonb,
  first_seen_event_id uuid references ledger.events_memory(event_id),
  last_event_id uuid references ledger.events_memory(event_id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger set_docs_updated_at
before update on sml.docs
for each row
execute function system.set_updated_at();

create trigger set_portfolio_items_updated_at
before update on sml.portfolio_items
for each row
execute function system.set_updated_at();

create trigger set_portfolio_item_notes_updated_at
before update on sml.portfolio_item_notes
for each row
execute function system.set_updated_at();

create trigger set_news_items_updated_at
before update on sml.news_items
for each row
execute function system.set_updated_at();

create trigger set_system_issues_updated_at
before update on sml.system_issues
for each row
execute function system.set_updated_at();

create trigger set_task_states_updated_at
before update on sml.task_states
for each row
execute function system.set_updated_at();

create trigger set_deliverable_refs_updated_at
before update on sml.deliverable_refs
for each row
execute function system.set_updated_at();
