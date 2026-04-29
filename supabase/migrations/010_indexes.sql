create index if not exists agent_events_run_idx
on raw.agent_events(run_id);

create index if not exists agent_events_entity_idx
on raw.agent_events(entity_type, entity_id);

create index if not exists agent_events_created_idx
on raw.agent_events(created_at desc);

create index if not exists document_chunks_document_idx
on raw.document_chunks(document_id);

create index if not exists document_chunks_embedding_idx
on raw.document_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

create index if not exists working_memory_unprocessed_idx
on promotion.working_memory_notes(processed_by_promotion, created_at);

create index if not exists promotion_attempts_note_idx
on promotion.promotion_attempts(note_id);

create index if not exists promotion_attempts_status_idx
on promotion.promotion_attempts(attempt_status, created_at desc);

create index if not exists pending_memory_status_idx
on promotion.pending_memory_events(status, next_retry_after);

create index if not exists pending_memory_bucket_target_idx
on promotion.pending_memory_events(bucket, target_id);

create index if not exists pending_memory_replay_idx
on promotion.pending_memory_events(status, next_retry_after, created_at);

create index if not exists events_memory_bucket_target_idx
on ledger.events_memory(bucket, target_id, timestamp desc);

create index if not exists events_memory_applied_idx
on ledger.events_memory(applied_successfully, timestamp desc);

create index if not exists portfolio_items_symbol_idx
on sml.portfolio_items(symbol, market);

create index if not exists portfolio_item_notes_item_idx
on sml.portfolio_item_notes(item_id, note_type, status);

create index if not exists docs_type_status_idx
on sml.docs(doc_type, status, updated_at desc);

create index if not exists news_items_status_valid_idx
on sml.news_items(status, valid_until);

create index if not exists system_issues_status_idx
on sml.system_issues(status, severity, updated_at desc);

create index if not exists system_issues_entity_idx
on sml.system_issues(entity_type, entity_id);

create index if not exists task_states_status_idx
on sml.task_states(status, owner_agent);

create index if not exists portfolio_items_payload_gin_idx
on sml.portfolio_items
using gin(payload_json);
