create table raw.agent_events (
  raw_event_id uuid primary key default extensions.gen_random_uuid(),
  run_id uuid references system.cron_runs(run_id),
  agent_run_id uuid references system.agent_runs(agent_run_id),
  source_type text not null check (source_type in ('agent', 'tool', 'market_data', 'news', 'user', 'system')),
  source_name text not null,
  entity_type text,
  entity_id text,
  event_type text not null,
  raw_text text,
  payload_json jsonb not null default '{}'::jsonb,
  confidence numeric check (confidence is null or (confidence >= 0 and confidence <= 1)),
  evidence_refs_json jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table raw.documents (
  document_id uuid primary key default extensions.gen_random_uuid(),
  title text not null,
  source_type text not null,
  source_uri text,
  storage_bucket text,
  storage_path text,
  content_hash text,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table raw.document_chunks (
  chunk_id uuid primary key default extensions.gen_random_uuid(),
  document_id uuid not null references raw.documents(document_id) on delete cascade,
  chunk_index int not null,
  chunk_text text not null,
  metadata_json jsonb not null default '{}'::jsonb,
  embedding extensions.vector(1536),
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create or replace function raw.match_document_chunks(
  query_embedding extensions.vector(1536),
  match_count int default 10,
  filter_document_id uuid default null
)
returns table (
  chunk_id uuid,
  document_id uuid,
  title text,
  source_uri text,
  storage_bucket text,
  storage_path text,
  chunk_index int,
  chunk_text text,
  metadata_json jsonb,
  similarity double precision
)
language sql
stable
security definer
set search_path = raw, public, extensions
as $$
  select
    c.chunk_id,
    c.document_id,
    d.title,
    d.source_uri,
    d.storage_bucket,
    d.storage_path,
    c.chunk_index,
    c.chunk_text,
    c.metadata_json,
    1 - (c.embedding <=> query_embedding) as similarity
  from raw.document_chunks c
  join raw.documents d on d.document_id = c.document_id
  where c.embedding is not null
    and (filter_document_id is null or c.document_id = filter_document_id)
  order by c.embedding <=> query_embedding
  limit greatest(match_count, 1);
$$;
