create view sml.active_portfolio_pages as
select
  p.*,
  coalesce(notes_agg.notes, '[]'::jsonb) as notes
from sml.portfolio_items p
left join lateral (
  select jsonb_agg(to_jsonb(n) order by n.created_at) as notes
  from sml.portfolio_item_notes n
  where n.item_id = p.item_id
    and n.status = 'active'
) as notes_agg on true
where p.status in ('watchlist', 'active_position');

create view promotion.pending_replay_queue as
select *
from promotion.pending_memory_events
where status = 'open'
  and (next_retry_after is null or next_retry_after <= now())
order by created_at asc;

create view ledger.failed_projections as
select *
from ledger.events_memory
where applied_successfully = false
  and projection_error_json is not null;
