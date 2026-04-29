insert into storage.buckets (id, name, public)
values
  ('raw-documents', 'raw-documents', false),
  ('generated-deliverables', 'generated-deliverables', false),
  ('snapshots', 'snapshots', false),
  ('exports', 'exports', false)
on conflict (id) do nothing;
