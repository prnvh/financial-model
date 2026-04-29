# Operations

## Hosted setup checklist

- Supabase plan: Pro
- Spend Cap: on
- Project count: one
- PITR: off
- Read replicas: off
- Custom domains: off
- Compute upgrade: only if forced by workload
- Vector store: keep it in Postgres with `pgvector`

## Local workflow

1. Install Docker and the Supabase CLI.
2. Run `npx supabase start`.
3. Apply migrations with `npx supabase db reset --local`.
4. Use `npx supabase db lint --local` before pushing remote schema changes.

## Remote workflow

1. Authenticate the CLI with `supabase login` or `SUPABASE_ACCESS_TOKEN`.
2. Link the project with `supabase link --project-ref <ref>`.
3. Apply migrations with `supabase db push --linked`.
4. Keep all schema changes in `supabase/migrations`; do not mutate production schema manually.

## Storage buckets

The migrations create four private buckets:

- `raw-documents`
- `generated-deliverables`
- `snapshots`
- `exports`

Database backups do not restore Storage API objects. Back up file contents separately.

## Backup cadence

- Daily: Supabase platform backups on Pro
- Weekly: logical database export via `scripts/backup-db.ps1`
- Weekly: Storage export via `scripts/export-storage.ps1` using the Supabase CLI storage commands

Recommended destinations:

- encrypted local drive
- private cloud folder
- S3/R2 later if retention grows

## Cost guardrails

Initial operational caps:

- max cron runs per day: 3
- max agent runs per cron: 10
- max documents ingested per day: 25
- max chunks per document: 100
- max report generations per day: 5
- max pending replay items per run: 25
- max pending replay rounds per run: 3

## Notes

- `raw.document_chunks.embedding` is currently defined as `extensions.vector(1536)`.
- If the embedding model changes, update the column type, retrieval function, and IVFFlat index migration strategy together.
- `ledger.events_memory` is guarded so only projection status columns can be updated after insert.
- `scripts/export-storage.ps1` uses the CLI's experimental Storage copy support, so re-check the command behavior after CLI upgrades.
