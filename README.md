# financial-model

Supabase-backed database foundation for the financial memory, promotion, and deliverables system.

## What is in this repo

This scaffold implements the first-pass database architecture described in the build spec:

- Supabase/Postgres as the single primary database
- `pgvector` support for retrieval on `raw.document_chunks`
- strict write-path separation across `raw`, `promotion`, `ledger`, `sml`, `deliverables`, `audit`, and `system`
- canonical system-level issue and task-state tables for governed runtime context
- SQL migrations from day one
- private storage buckets for research, snapshots, deliverables, and exports
- backup/export helper scripts for database dumps and Storage copies

## Repo layout

```text
docs/
  OPERATIONS.md
scripts/
  backup-db.ps1
  export-storage.ps1
supabase/
  config.toml
  migrations/
    001_extensions.sql
    002_schemas.sql
    003_system_tables.sql
    004_raw_tables.sql
    005_promotion_tables.sql
    006_ledger_tables.sql
    007_sml_tables.sql
    008_deliverables_tables.sql
    009_audit_tables.sql
    010_indexes.sql
    011_views.sql
    012_roles_and_permissions.sql
    013_storage_buckets.sql
```

## Quickstart

1. Install Docker and the Supabase CLI.
2. Copy `.env.example` to `.env` and fill in the remote values you actually need.
3. Start the local stack with `npx supabase start`.
4. Apply the migrations locally with `npx supabase db reset --local`.
5. Link a hosted project when ready, then deploy with `npx supabase db push --linked`.

The checked-in [`supabase/config.toml`](supabase/config.toml) is intentionally minimal. If your CLI version wants a fuller config, regenerate it with `npx supabase init --force` and keep the same `project_id`.

## Operating constraints

- Agents never write `sml.*` directly.
- `promotion.working_memory_notes` is the staging membrane.
- `ledger.events_memory` is the canonical committed mutation history.
- `sml.*` is current trusted state, not full history.
- Storage remains private by default.
- Weekly logical dumps and Storage exports are part of the baseline operating model.

The setup and cost-control checklist lives in [`docs/OPERATIONS.md`](docs/OPERATIONS.md).
