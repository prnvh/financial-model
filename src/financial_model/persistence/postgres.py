from __future__ import annotations

import json
from contextlib import AbstractContextManager
from datetime import timedelta
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from financial_model.domain.models import (
    DeliverableDraft,
    LedgerEvent,
    NoteType,
    PendingMemoryEvent,
    SharedMemoryContext,
    WorkingMemoryNote,
)
from financial_model.domain.utils import utc_now


TERMINAL_RUN_STATUSES = {"succeeded", "failed", "cancelled"}
TERMINAL_AGENT_RUN_STATUSES = {"succeeded", "failed", "skipped"}


class PostgresRepository:
    def __init__(self, connection: psycopg.Connection):
        self._connection = connection

    @classmethod
    def connect(cls, dsn: str) -> "PostgresRepository":
        connection = psycopg.connect(dsn, row_factory=dict_row)
        return cls(connection)

    def close(self) -> None:
        self._connection.close()

    def transaction(self) -> AbstractContextManager[object]:
        return self._connection.transaction()

    def create_cron_run(self, trigger_type: str, run_type: str, config_json: dict[str, Any]) -> str:
        query = """
            insert into system.cron_runs (trigger_type, run_type, status, config_json)
            values (%s, %s, 'queued', %s)
            returning run_id::text
        """
        return self._scalar(query, (trigger_type, run_type, Jsonb(config_json)))

    def update_cron_run_status(
        self,
        run_id: str,
        status: str,
        error_json: dict[str, Any] | None = None,
    ) -> None:
        finished_at = utc_now() if status in TERMINAL_RUN_STATUSES else None
        query = """
            update system.cron_runs
            set status = %s,
                finished_at = coalesce(%s, finished_at),
                error_json = %s
            where run_id = %s::uuid
        """
        self._execute(query, (status, finished_at, Jsonb(error_json) if error_json else None, run_id))

    def create_agent_run(
        self,
        run_id: str,
        agent_name: str,
        agent_role: str,
        input_context_json: dict[str, Any],
        model_name: str | None = None,
    ) -> str:
        query = """
            insert into system.agent_runs (
                run_id,
                agent_name,
                agent_role,
                status,
                input_context_json,
                model_name
            )
            values (%s::uuid, %s, %s, 'queued', %s, %s)
            returning agent_run_id::text
        """
        return self._scalar(query, (run_id, agent_name, agent_role, Jsonb(input_context_json), model_name))

    def update_agent_run(
        self,
        agent_run_id: str,
        status: str,
        output_summary: str | None = None,
        token_usage_json: dict[str, Any] | None = None,
        cost_estimate: float | None = None,
        error_json: dict[str, Any] | None = None,
    ) -> None:
        finished_at = utc_now() if status in TERMINAL_AGENT_RUN_STATUSES else None
        query = """
            update system.agent_runs
            set status = %s,
                finished_at = coalesce(%s, finished_at),
                output_summary = coalesce(%s, output_summary),
                token_usage_json = coalesce(%s, token_usage_json),
                cost_estimate = coalesce(%s, cost_estimate),
                error_json = %s
            where agent_run_id = %s::uuid
        """
        self._execute(
            query,
            (
                status,
                finished_at,
                output_summary,
                Jsonb(token_usage_json) if token_usage_json else None,
                cost_estimate,
                Jsonb(error_json) if error_json else None,
                agent_run_id,
            ),
        )

    def record_raw_agent_event(
        self,
        run_id: str,
        agent_run_id: str,
        source_type: str,
        source_name: str,
        event_type: str,
        raw_text: str | None,
        payload_json: dict[str, Any],
        entity_type: str | None = None,
        entity_id: str | None = None,
        confidence: float | None = None,
        evidence_refs_json: list[dict[str, Any]] | None = None,
    ) -> str:
        query = """
            insert into raw.agent_events (
                run_id,
                agent_run_id,
                source_type,
                source_name,
                entity_type,
                entity_id,
                event_type,
                raw_text,
                payload_json,
                confidence,
                evidence_refs_json
            )
            values (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            returning raw_event_id::text
        """
        return self._scalar(
            query,
            (
                run_id,
                agent_run_id,
                source_type,
                source_name,
                entity_type,
                entity_id,
                event_type,
                raw_text,
                Jsonb(payload_json),
                confidence,
                Jsonb(evidence_refs_json or []),
            ),
        )

    def add_working_memory_note(self, note: WorkingMemoryNote) -> WorkingMemoryNote:
        query = """
            insert into promotion.working_memory_notes (
                run_id,
                agent_run_id,
                source_agent,
                note_type,
                raw_text,
                source_ref
            )
            values (%s::uuid, %s::uuid, %s, %s, %s, %s)
            returning note_id::text, created_at
        """
        row = self._fetchone(
            query,
            (note.run_id, note.agent_run_id, note.source_agent, note.note_type.value, note.raw_text, note.source_ref),
        )
        note.note_id = row["note_id"]
        note.created_at = row["created_at"]
        return note

    def list_unprocessed_notes(self, run_id: str, agent_run_id: str) -> list[WorkingMemoryNote]:
        query = """
            select note_id::text as note_id,
                   run_id::text as run_id,
                   agent_run_id::text as agent_run_id,
                   source_agent,
                   note_type,
                   raw_text,
                   source_ref,
                   processed_by_promotion,
                   promoted_at,
                   created_at
            from promotion.working_memory_notes
            where run_id = %s::uuid
              and agent_run_id = %s::uuid
              and processed_by_promotion = false
            order by created_at asc
        """
        rows = self._fetchall(query, (run_id, agent_run_id))
        return [
            WorkingMemoryNote(
                note_id=row["note_id"],
                run_id=row["run_id"],
                agent_run_id=row["agent_run_id"],
                source_agent=row["source_agent"],
                note_type=NoteType(row["note_type"]),
                raw_text=row["raw_text"],
                source_ref=row["source_ref"],
                processed_by_promotion=row["processed_by_promotion"],
                promoted_at=row["promoted_at"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def mark_note_processed(self, note_id: str) -> None:
        query = """
            update promotion.working_memory_notes
            set processed_by_promotion = true,
                promoted_at = now()
            where note_id = %s::uuid
        """
        self._execute(query, (note_id,))

    def get_shared_memory_context(self) -> SharedMemoryContext:
        docs = self._fetchall(
            """
            select doc_id, doc_type, title, status, body, payload_json, reference_memory_json
            from sml.docs
            where status = 'active'
            order by updated_at desc
            """
        )
        active_constraints = self._fetchall("select * from sml.active_constraints order by updated_at desc")
        active_portfolio_pages = self._fetchall("select * from sml.active_portfolio_pages order by updated_at desc")
        open_system_issues = self._fetchall("select * from sml.open_system_issues order by updated_at desc")
        active_portfolio_decisions = self._fetchall(
            """
            select n.*, p.name as item_name, p.symbol, p.market
            from sml.portfolio_item_notes n
            join sml.portfolio_items p on p.item_id = n.item_id
            where n.note_type = 'decision'
              and n.status = 'active'
            order by n.updated_at desc
            """
        )
        active_news_items = self._fetchall(
            """
            select *
            from sml.news_items
            where status = 'active'
              and (valid_until is null or valid_until >= now())
            order by updated_at desc
            """
        )
        deliverable_refs = self._fetchall(
            """
            select *
            from sml.deliverable_refs
            where status in ('draft', 'final')
            order by updated_at desc
            """
        )
        task_states = self._fetchall(
            """
            select *
            from sml.task_states
            where status in ('pending', 'in_progress', 'blocked')
            order by updated_at desc
            """
        )
        return SharedMemoryContext(
            docs=docs,
            active_constraints=active_constraints,
            active_portfolio_pages=active_portfolio_pages,
            open_system_issues=open_system_issues,
            active_portfolio_decisions=active_portfolio_decisions,
            active_news_items=active_news_items,
            deliverable_refs=deliverable_refs,
            task_states=task_states,
        )

    def create_promotion_attempt(
        self,
        note_id: str,
        run_id: str | None,
        source_agent: str,
        attempt_status: str,
        interpreter_decision: str | None = None,
        resolver_decision: str | None = None,
        validator_decision: str | None = None,
        bucket: str | None = None,
        operation: str | None = None,
        target_id: str | None = None,
        write_request_json: dict[str, Any] | None = None,
        resolved_write_json: dict[str, Any] | None = None,
        validator_errors_json: dict[str, Any] | None = None,
        error_json: dict[str, Any] | None = None,
    ) -> str:
        query = """
            insert into promotion.promotion_attempts (
                note_id,
                run_id,
                source_agent,
                attempt_status,
                interpreter_decision,
                resolver_decision,
                validator_decision,
                bucket,
                operation,
                target_id,
                write_request_json,
                resolved_write_json,
                validator_errors_json,
                error_json
            )
            values (
                %s::uuid,
                %s::uuid,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            returning attempt_id::text
        """
        return self._scalar(
            query,
            (
                note_id,
                run_id,
                source_agent,
                attempt_status,
                interpreter_decision,
                resolver_decision,
                validator_decision,
                bucket,
                operation,
                target_id,
                Jsonb(write_request_json) if write_request_json else None,
                Jsonb(resolved_write_json) if resolved_write_json else None,
                Jsonb(validator_errors_json) if validator_errors_json else None,
                Jsonb(error_json) if error_json else None,
            ),
        )

    def create_pending_event(self, pending: PendingMemoryEvent) -> str:
        query = """
            insert into promotion.pending_memory_events (
                bucket,
                operation,
                original_write_request_json,
                target_id,
                source_agent,
                raw_input,
                reference_text,
                reason,
                payload_json,
                candidate_aliases_json,
                candidate_matches_json,
                confidence,
                status,
                retry_count,
                next_retry_after
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            returning pending_id::text
        """
        return self._scalar(
            query,
            (
                pending.bucket,
                pending.operation,
                Jsonb(pending.original_write_request_json),
                pending.target_id,
                pending.source_agent,
                pending.raw_input,
                pending.reference_text,
                pending.reason,
                Jsonb(pending.payload_json),
                Jsonb(pending.candidate_aliases_json),
                Jsonb(pending.candidate_matches_json),
                pending.confidence,
                pending.status,
                pending.retry_count,
                pending.next_retry_after,
            ),
        )

    def list_retryable_pending_events(self, limit: int) -> list[PendingMemoryEvent]:
        rows = self._fetchall(
            "select * from promotion.pending_replay_queue limit %s",
            (limit,),
        )
        return [self._pending_from_row(row) for row in rows]

    def update_pending_event_status(
        self,
        pending_id: str,
        status: str,
        reason: str,
        final_event_id: str | None = None,
    ) -> None:
        next_retry_after = None
        if status == "on_hold":
            next_retry_after = utc_now() + timedelta(minutes=15)
        query = """
            update promotion.pending_memory_events
            set status = %s,
                retry_count = retry_count + 1,
                last_retry_at = now(),
                last_retry_reason = %s,
                next_retry_after = %s,
                final_event_id = coalesce(%s::uuid, final_event_id)
            where pending_id = %s::uuid
        """
        self._execute(query, (status, reason, next_retry_after, final_event_id, pending_id))

    def insert_ledger_event(self, event: LedgerEvent) -> str:
        query = """
            insert into ledger.events_memory (
                source_agent,
                source_attempt_id,
                bucket,
                target_id,
                operation,
                payload_json,
                raw_input,
                source_ref,
                applied_successfully
            )
            values (%s, %s::uuid, %s, %s, %s, %s, %s, %s, false)
            returning event_id::text, timestamp
        """
        row = self._fetchone(
            query,
            (
                event.source_agent,
                event.source_attempt_id,
                event.bucket,
                event.target_id,
                event.operation,
                Jsonb(event.payload_json),
                event.raw_input,
                event.source_ref,
            ),
        )
        event.event_id = row["event_id"]
        event.timestamp = row["timestamp"]
        return event.event_id

    def mark_ledger_event_projection(
        self,
        event_id: str,
        applied_successfully: bool,
        projection_error_json: dict[str, Any] | None = None,
    ) -> None:
        query = """
            update ledger.events_memory
            set applied_successfully = %s,
                projection_error_json = %s
            where event_id = %s::uuid
        """
        self._execute(
            query,
            (
                applied_successfully,
                Jsonb(projection_error_json) if projection_error_json else None,
                event_id,
            ),
        )

    def project_doc(self, event: LedgerEvent, doc_type: str, status: str | None = None) -> None:
        existing = self._fetchone_optional(
            "select version, first_seen_event_id::text as first_seen_event_id, reference_memory_json from sml.docs where doc_id = %s",
            (event.target_id,),
        )
        payload = event.payload_json
        version = (existing["version"] + 1) if existing else 1
        body = payload.get("body") or payload.get("statement") or payload.get("description") or payload.get("text")
        title = payload.get("title") or payload.get("name") or event.target_id
        reference_memory = self._merge_reference_memory(
            existing["reference_memory_json"] if existing else None,
            event.target_id,
            title,
            event,
        )
        query = """
            insert into sml.docs (
                doc_id,
                doc_type,
                title,
                status,
                body,
                payload_json,
                version,
                first_seen_event_id,
                last_event_id,
                reference_memory_json
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                coalesce(%s::uuid, %s::uuid),
                %s::uuid,
                %s
            )
            on conflict (doc_id) do update
            set doc_type = excluded.doc_type,
                title = excluded.title,
                status = excluded.status,
                body = excluded.body,
                payload_json = excluded.payload_json,
                version = excluded.version,
                last_event_id = excluded.last_event_id,
                reference_memory_json = excluded.reference_memory_json
        """
        self._execute(
            query,
            (
                event.target_id,
                doc_type,
                title,
                status or "active",
                body,
                Jsonb(payload),
                version,
                existing["first_seen_event_id"] if existing else None,
                event.event_id,
                event.event_id,
                Jsonb(reference_memory),
            ),
        )

    def project_doc_status(self, event: LedgerEvent, status: str) -> None:
        self._execute(
            """
            update sml.docs
            set status = %s,
                last_event_id = %s::uuid
            where doc_id = %s
            """,
            (status, event.event_id, event.target_id),
        )

    def project_portfolio_item(self, event: LedgerEvent, status: str | None = None) -> None:
        existing = self._fetchone_optional(
            "select first_seen_event_id::text as first_seen_event_id from sml.portfolio_items where item_id = %s",
            (event.target_id,),
        )
        payload = event.payload_json
        query = """
            insert into sml.portfolio_items (
                item_id,
                name,
                symbol,
                market,
                asset_type,
                status,
                position_status,
                official_entry,
                entry_range_json,
                exit_range_json,
                thesis,
                risks_json,
                learnings_json,
                payload_json,
                first_seen_event_id,
                last_event_id,
                reference_memory_json
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                coalesce(%s::uuid, %s::uuid),
                %s::uuid,
                %s
            )
            on conflict (item_id) do update
            set name = excluded.name,
                symbol = excluded.symbol,
                market = excluded.market,
                asset_type = excluded.asset_type,
                status = excluded.status,
                position_status = excluded.position_status,
                official_entry = excluded.official_entry,
                entry_range_json = excluded.entry_range_json,
                exit_range_json = excluded.exit_range_json,
                thesis = excluded.thesis,
                risks_json = excluded.risks_json,
                learnings_json = excluded.learnings_json,
                payload_json = excluded.payload_json,
                last_event_id = excluded.last_event_id,
                reference_memory_json = excluded.reference_memory_json
        """
        self._execute(
            query,
            (
                event.target_id,
                payload.get("name", event.target_id),
                payload.get("symbol"),
                payload.get("market"),
                payload.get("asset_type", "equity"),
                status or payload.get("status", "watchlist"),
                payload.get("position_status", "not_held"),
                payload.get("official_entry"),
                Jsonb(payload.get("entry_range_json") or {}),
                Jsonb(payload.get("exit_range_json") or {}),
                payload.get("thesis"),
                Jsonb(payload.get("risks_json") or []),
                Jsonb(payload.get("learnings_json") or []),
                Jsonb(payload),
                existing["first_seen_event_id"] if existing else None,
                event.event_id,
                event.event_id,
                Jsonb(payload.get("reference_memory_json") or {}),
            ),
        )

    def project_portfolio_item_status(self, event: LedgerEvent, status: str) -> None:
        self._execute(
            """
            update sml.portfolio_items
            set status = %s,
                last_event_id = %s::uuid
            where item_id = %s
            """,
            (status, event.event_id, event.target_id),
        )

    def project_portfolio_note(self, event: LedgerEvent, note_type: str, status: str | None = None) -> None:
        existing = self._fetchone_optional(
            "select first_seen_event_id::text as first_seen_event_id, reference_memory_json from sml.portfolio_item_notes where note_id = %s",
            (event.target_id,),
        )
        payload = event.payload_json
        title = payload.get("title") or payload.get("risk_type") or payload.get("note_title") or event.target_id
        body = payload.get("body") or payload.get("description") or payload.get("statement") or payload.get("result")
        reference_memory = self._merge_reference_memory(
            existing["reference_memory_json"] if existing else None,
            event.target_id,
            title,
            event,
        )
        query = """
            insert into sml.portfolio_item_notes (
                note_id,
                item_id,
                note_type,
                status,
                title,
                body,
                payload_json,
                first_seen_event_id,
                last_event_id,
                reference_memory_json
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                coalesce(%s::uuid, %s::uuid),
                %s::uuid,
                %s
            )
            on conflict (note_id) do update
            set item_id = excluded.item_id,
                note_type = excluded.note_type,
                status = excluded.status,
                title = excluded.title,
                body = excluded.body,
                payload_json = excluded.payload_json,
                last_event_id = excluded.last_event_id,
                reference_memory_json = excluded.reference_memory_json
        """
        self._execute(
            query,
            (
                event.target_id,
                payload.get("item_id"),
                note_type,
                status or "active",
                title,
                body,
                Jsonb(payload),
                existing["first_seen_event_id"] if existing else None,
                event.event_id,
                event.event_id,
                Jsonb(reference_memory),
            ),
        )

    def project_portfolio_note_status(self, event: LedgerEvent, status: str) -> None:
        self._execute(
            """
            update sml.portfolio_item_notes
            set status = %s,
                last_event_id = %s::uuid
            where note_id = %s
            """,
            (status, event.event_id, event.target_id),
        )

    def project_news_item(self, event: LedgerEvent, status: str | None = None) -> None:
        existing = self._fetchone_optional(
            "select first_seen_event_id::text as first_seen_event_id from sml.news_items where news_item_id = %s",
            (event.target_id,),
        )
        payload = event.payload_json
        query = """
            insert into sml.news_items (
                news_item_id,
                title,
                status,
                source_type,
                source_uri,
                related_entities_json,
                related_docs_json,
                summary,
                researched_summary,
                impact,
                severity,
                valid_until,
                payload_json,
                first_seen_event_id,
                last_event_id
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                coalesce(%s::uuid, %s::uuid),
                %s::uuid
            )
            on conflict (news_item_id) do update
            set title = excluded.title,
                status = excluded.status,
                source_type = excluded.source_type,
                source_uri = excluded.source_uri,
                related_entities_json = excluded.related_entities_json,
                related_docs_json = excluded.related_docs_json,
                summary = excluded.summary,
                researched_summary = excluded.researched_summary,
                impact = excluded.impact,
                severity = excluded.severity,
                valid_until = excluded.valid_until,
                payload_json = excluded.payload_json,
                last_event_id = excluded.last_event_id
        """
        self._execute(
            query,
            (
                event.target_id,
                payload.get("title", event.target_id),
                status or "active",
                payload.get("source_type"),
                payload.get("source_uri"),
                Jsonb(payload.get("related_entities_json") or []),
                Jsonb(payload.get("related_docs_json") or []),
                payload.get("summary"),
                payload.get("researched_summary"),
                payload.get("impact"),
                payload.get("severity"),
                payload.get("valid_until"),
                Jsonb(payload),
                existing["first_seen_event_id"] if existing else None,
                event.event_id,
                event.event_id,
            ),
        )

    def project_news_item_status(self, event: LedgerEvent, status: str) -> None:
        self._execute(
            """
            update sml.news_items
            set status = %s,
                last_event_id = %s::uuid
            where news_item_id = %s
            """,
            (status, event.event_id, event.target_id),
        )

    def project_deliverable_ref(self, event: LedgerEvent, status: str | None = None) -> None:
        existing = self._fetchone_optional(
            "select first_seen_event_id::text as first_seen_event_id from sml.deliverable_refs where deliverable_id = %s",
            (event.target_id,),
        )
        payload = event.payload_json
        query = """
            insert into sml.deliverable_refs (
                deliverable_id,
                deliverable_type,
                title,
                status,
                subject_entities_json,
                storage_bucket,
                storage_path,
                source_events_json,
                human_decision,
                decision_notes,
                first_seen_event_id,
                last_event_id
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                coalesce(%s::uuid, %s::uuid),
                %s::uuid
            )
            on conflict (deliverable_id) do update
            set deliverable_type = excluded.deliverable_type,
                title = excluded.title,
                status = excluded.status,
                subject_entities_json = excluded.subject_entities_json,
                storage_bucket = excluded.storage_bucket,
                storage_path = excluded.storage_path,
                source_events_json = excluded.source_events_json,
                human_decision = excluded.human_decision,
                decision_notes = excluded.decision_notes,
                last_event_id = excluded.last_event_id
        """
        self._execute(
            query,
            (
                event.target_id,
                payload.get("deliverable_type"),
                payload.get("title", event.target_id),
                status or payload.get("status", "draft"),
                Jsonb(payload.get("subject_entities_json") or []),
                payload.get("storage_bucket"),
                payload.get("storage_path"),
                Jsonb(payload.get("source_events_json") or []),
                payload.get("human_decision"),
                payload.get("decision_notes"),
                existing["first_seen_event_id"] if existing else None,
                event.event_id,
                event.event_id,
            ),
        )

    def project_deliverable_ref_status(self, event: LedgerEvent, status: str) -> None:
        self._execute(
            """
            update sml.deliverable_refs
            set status = %s,
                last_event_id = %s::uuid
            where deliverable_id = %s
            """,
            (status, event.event_id, event.target_id),
        )

    def project_system_issue(self, event: LedgerEvent, status: str | None = None) -> None:
        existing = self._fetchone_optional(
            "select first_seen_event_id::text as first_seen_event_id, reference_memory_json from sml.system_issues where issue_id = %s",
            (event.target_id,),
        )
        payload = event.payload_json
        title = payload.get("title", event.target_id)
        reference_memory = self._merge_reference_memory(
            existing["reference_memory_json"] if existing else None,
            event.target_id,
            title,
            event,
        )
        query = """
            insert into sml.system_issues (
                issue_id,
                title,
                description,
                status,
                severity,
                entity_type,
                entity_id,
                payload_json,
                first_seen_event_id,
                last_event_id,
                reference_memory_json
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                coalesce(%s::uuid, %s::uuid),
                %s::uuid,
                %s
            )
            on conflict (issue_id) do update
            set title = excluded.title,
                description = excluded.description,
                status = excluded.status,
                severity = excluded.severity,
                entity_type = excluded.entity_type,
                entity_id = excluded.entity_id,
                payload_json = excluded.payload_json,
                last_event_id = excluded.last_event_id,
                reference_memory_json = excluded.reference_memory_json
        """
        self._execute(
            query,
            (
                event.target_id,
                title,
                payload.get("description"),
                status or "open",
                payload.get("severity"),
                payload.get("entity_type"),
                payload.get("entity_id"),
                Jsonb(payload),
                existing["first_seen_event_id"] if existing else None,
                event.event_id,
                event.event_id,
                Jsonb(reference_memory),
            ),
        )

    def project_system_issue_status(self, event: LedgerEvent, status: str) -> None:
        self._execute(
            """
            update sml.system_issues
            set status = %s,
                last_event_id = %s::uuid
            where issue_id = %s
            """,
            (status, event.event_id, event.target_id),
        )

    def project_task_state(self, event: LedgerEvent) -> None:
        existing = self._fetchone_optional(
            "select first_seen_event_id::text as first_seen_event_id from sml.task_states where task_id = %s",
            (event.target_id,),
        )
        payload = event.payload_json
        query = """
            insert into sml.task_states (
                task_id,
                status,
                phase,
                owner_agent,
                blockers_json,
                payload_json,
                first_seen_event_id,
                last_event_id
            )
            values (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                coalesce(%s::uuid, %s::uuid),
                %s::uuid
            )
            on conflict (task_id) do update
            set status = excluded.status,
                phase = excluded.phase,
                owner_agent = excluded.owner_agent,
                blockers_json = excluded.blockers_json,
                payload_json = excluded.payload_json,
                last_event_id = excluded.last_event_id
        """
        self._execute(
            query,
            (
                event.target_id,
                payload.get("status"),
                payload.get("phase"),
                payload.get("owner_agent", event.source_agent),
                Jsonb(payload.get("blockers_json") or []),
                Jsonb(payload),
                existing["first_seen_event_id"] if existing else None,
                event.event_id,
                event.event_id,
            ),
        )

    def create_snapshot(self, run_id: str | None, snapshot_type: str, snapshot_json: dict[str, Any]) -> str:
        query = """
            insert into audit.sml_snapshots (run_id, snapshot_type, snapshot_json)
            values (%s::uuid, %s, %s)
            returning snapshot_id::text
        """
        return self._scalar(query, (run_id, snapshot_type, Jsonb(snapshot_json)))

    def create_deliverable(self, draft: DeliverableDraft, generated_by_agent_run_id: str | None = None) -> str:
        report_query = """
            insert into deliverables.reports (
                deliverable_id,
                report_type,
                title,
                status,
                markdown_body,
                summary,
                source_events_json,
                source_documents_json,
                source_sml_objects_json,
                generated_by_agent_run_id
            )
            values (
                %s,
                %s,
                %s,
                'draft',
                %s,
                %s,
                %s,
                %s,
                %s,
                %s::uuid
            )
            returning report_id::text
        """
        report_id = self._scalar(
            report_query,
            (
                None,
                draft.report_type,
                draft.title,
                draft.markdown_body,
                draft.summary,
                Jsonb(draft.source_events_json),
                Jsonb(draft.source_documents_json),
                Jsonb(draft.source_sml_objects_json),
                generated_by_agent_run_id,
            ),
        )
        for index, section in enumerate(draft.sections, start=1):
            self._execute(
                """
                insert into deliverables.report_sections (
                    report_id,
                    section_order,
                    section_type,
                    title,
                    body,
                    evidence_refs_json
                )
                values (%s::uuid, %s, %s, %s, %s, %s)
                """,
                (
                    report_id,
                    index,
                    section.section_type,
                    section.title,
                    section.body,
                    Jsonb(section.evidence_refs_json),
                ),
            )
        return report_id

    def _pending_from_row(self, row: dict[str, Any]) -> PendingMemoryEvent:
        return PendingMemoryEvent(
            pending_id=str(row["pending_id"]) if isinstance(row["pending_id"], UUID) else row["pending_id"],
            bucket=row["bucket"],
            operation=row["operation"],
            original_write_request_json=row["original_write_request_json"],
            target_id=row["target_id"],
            source_agent=row.get("source_agent"),
            raw_input=row.get("raw_input"),
            reference_text=row.get("reference_text"),
            reason=row.get("reason", "unspecified"),
            payload_json=row.get("payload_json") or {},
            candidate_aliases_json=row.get("candidate_aliases_json") or [],
            candidate_matches_json=row.get("candidate_matches_json") or [],
            confidence=row.get("confidence"),
            status=row.get("status", "open"),
            retry_count=row.get("retry_count", 0),
            last_retry_at=row.get("last_retry_at"),
            last_retry_reason=row.get("last_retry_reason"),
            next_retry_after=row.get("next_retry_after"),
            final_event_id=str(row["final_event_id"]) if row.get("final_event_id") else None,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _merge_reference_memory(
        self,
        existing_reference_memory: dict[str, Any] | None,
        target_id: str,
        canonical_text: str | None,
        event: LedgerEvent,
    ) -> dict[str, Any]:
        memory = {
            "canonical_text": None,
            "creation_note_text": None,
            "aliases": [],
            "reference_phrases": [],
            "seen_referring_expressions": [],
        }
        if isinstance(existing_reference_memory, dict):
            memory.update(existing_reference_memory)
            for key in ("aliases", "reference_phrases", "seen_referring_expressions"):
                memory[key] = list(memory.get(key) or [])

        if canonical_text:
            memory["canonical_text"] = canonical_text

        raw_input = (event.raw_input or "").strip()
        if raw_input and not memory.get("creation_note_text"):
            memory["creation_note_text"] = raw_input

        self._append_unique(memory["aliases"], target_id)
        if canonical_text:
            self._append_unique(memory["reference_phrases"], canonical_text)

        source_ref = self._parse_json_string(event.source_ref) if self._looks_like_json(event.source_ref) else {}
        if isinstance(source_ref, dict):
            reference_text = str(source_ref.get("reference_text") or "").strip()
            if reference_text:
                self._append_unique(memory["reference_phrases"], reference_text)
                self._append_unique(memory["seen_referring_expressions"], reference_text)
            for alias in source_ref.get("candidate_aliases") or []:
                alias_text = str(alias).strip()
                if alias_text:
                    self._append_unique(memory["aliases"], alias_text)

        if raw_input:
            self._append_unique(memory["seen_referring_expressions"], raw_input)

        memory["aliases"] = memory["aliases"][:12]
        memory["reference_phrases"] = memory["reference_phrases"][:16]
        memory["seen_referring_expressions"] = memory["seen_referring_expressions"][:10]
        return memory

    def _append_unique(self, items: list[str], value: str) -> None:
        if value and value not in items:
            items.append(value)

    def _execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(query, params)

    def _scalar(self, query: str, params: tuple[Any, ...] | None = None) -> str:
        row = self._fetchone(query, params)
        return next(iter(row.values()))

    def _fetchone(self, query: str, params: tuple[Any, ...] | None = None) -> dict[str, Any]:
        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
        if row is None:
            raise LookupError("Expected a row but query returned none.")
        return row

    def _fetchone_optional(self, query: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
        return row

    def _fetchall(self, query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return rows

    def _looks_like_json(self, value: str | None) -> bool:
        if not value:
            return False
        stripped = value.strip()
        return stripped.startswith("{") and stripped.endswith("}")

    def _parse_json_string(self, value: str | None) -> dict[str, Any]:
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
