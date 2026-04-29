create schema if not exists system;
create schema if not exists raw;
create schema if not exists promotion;
create schema if not exists ledger;
create schema if not exists sml;
create schema if not exists deliverables;
create schema if not exists audit;

create or replace function system.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;
