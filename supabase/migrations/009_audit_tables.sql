create table audit.sml_snapshots (
  snapshot_id uuid primary key default extensions.gen_random_uuid(),
  run_id uuid references system.cron_runs(run_id),
  snapshot_type text not null check (
    snapshot_type in ('pre_run', 'post_run', 'pre_report', 'pre_decision', 'manual')
  ),
  snapshot_json jsonb not null,
  created_at timestamptz not null default now()
);

create table audit.human_actions (
  human_action_id uuid primary key default extensions.gen_random_uuid(),
  actor_id uuid,
  action_type text not null,
  target_type text not null,
  target_id text not null,
  decision text,
  notes text,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table sml.deliverable_refs
add constraint deliverable_refs_source_snapshot_id_fkey
foreign key (source_snapshot_id) references audit.sml_snapshots(snapshot_id);

alter table deliverables.reports
add constraint reports_source_snapshot_id_fkey
foreign key (source_snapshot_id) references audit.sml_snapshots(snapshot_id);
