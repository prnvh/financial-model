create table deliverables.reports (
  report_id uuid primary key default extensions.gen_random_uuid(),
  deliverable_id text references sml.deliverable_refs(deliverable_id),
  report_type text not null,
  title text not null,
  status text not null check (status in ('draft', 'final', 'rejected', 'archived')),
  markdown_body text,
  summary text,
  source_events_json jsonb not null default '[]'::jsonb,
  source_documents_json jsonb not null default '[]'::jsonb,
  source_sml_objects_json jsonb not null default '[]'::jsonb,
  source_snapshot_id uuid,
  generated_by_agent_run_id uuid references system.agent_runs(agent_run_id),
  created_at timestamptz not null default now(),
  finalized_at timestamptz
);

create table deliverables.report_sections (
  section_id uuid primary key default extensions.gen_random_uuid(),
  report_id uuid not null references deliverables.reports(report_id) on delete cascade,
  section_order int not null,
  section_type text,
  title text,
  body text,
  evidence_refs_json jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (report_id, section_order)
);
