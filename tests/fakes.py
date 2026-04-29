from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from itertools import count
from typing import Any

from financial_model.domain.models import DeliverableDraft, LedgerEvent, PendingMemoryEvent, SharedMemoryContext, WorkingMemoryNote
from financial_model.domain.utils import utc_now


class InMemoryRepository:
    def __init__(self) -> None:
        self._ids = count(1)
        self.cron_runs: dict[str, dict[str, Any]] = {}
        self.agent_runs: dict[str, dict[str, Any]] = {}
        self.raw_events: dict[str, dict[str, Any]] = {}
        self.working_notes: dict[str, dict[str, Any]] = {}
        self.promotion_attempts: dict[str, dict[str, Any]] = {}
        self.pending_events: dict[str, PendingMemoryEvent] = {}
        self.ledger_events: dict[str, LedgerEvent] = {}
        self.docs: dict[str, dict[str, Any]] = {}
        self.portfolio_items: dict[str, dict[str, Any]] = {}
        self.portfolio_notes: dict[str, dict[str, Any]] = {}
        self.news_items: dict[str, dict[str, Any]] = {}
        self.deliverable_refs: dict[str, dict[str, Any]] = {}
        self.system_issues: dict[str, dict[str, Any]] = {}
        self.task_states: dict[str, dict[str, Any]] = {}
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.reports: dict[str, dict[str, Any]] = {}
        self.report_sections: list[dict[str, Any]] = []

    def transaction(self):
        return nullcontext()

    def create_cron_run(self, trigger_type: str, run_type: str, config_json: dict[str, Any]) -> str:
        run_id = self._new_id("run")
        self.cron_runs[run_id] = {
            "run_id": run_id,
            "trigger_type": trigger_type,
            "run_type": run_type,
            "status": "queued",
            "config_json": config_json,
        }
        return run_id

    def update_cron_run_status(self, run_id: str, status: str, error_json: dict[str, Any] | None = None) -> None:
        self.cron_runs[run_id]["status"] = status
        self.cron_runs[run_id]["error_json"] = error_json

    def create_agent_run(
        self,
        run_id: str,
        agent_name: str,
        agent_role: str,
        input_context_json: dict[str, Any],
        model_name: str | None = None,
    ) -> str:
        agent_run_id = self._new_id("agent")
        self.agent_runs[agent_run_id] = {
            "agent_run_id": agent_run_id,
            "run_id": run_id,
            "agent_name": agent_name,
            "agent_role": agent_role,
            "status": "queued",
            "input_context_json": input_context_json,
            "model_name": model_name,
        }
        return agent_run_id

    def update_agent_run(
        self,
        agent_run_id: str,
        status: str,
        output_summary: str | None = None,
        token_usage_json: dict[str, Any] | None = None,
        cost_estimate: float | None = None,
        error_json: dict[str, Any] | None = None,
    ) -> None:
        self.agent_runs[agent_run_id].update(
            {
                "status": status,
                "output_summary": output_summary,
                "token_usage_json": token_usage_json,
                "cost_estimate": cost_estimate,
                "error_json": error_json,
            }
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
        raw_event_id = self._new_id("raw")
        self.raw_events[raw_event_id] = {
            "raw_event_id": raw_event_id,
            "run_id": run_id,
            "agent_run_id": agent_run_id,
            "source_type": source_type,
            "source_name": source_name,
            "event_type": event_type,
            "raw_text": raw_text,
            "payload_json": payload_json,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "confidence": confidence,
            "evidence_refs_json": evidence_refs_json or [],
        }
        return raw_event_id

    def add_working_memory_note(self, note: WorkingMemoryNote) -> WorkingMemoryNote:
        note_id = self._new_id("note")
        note.note_id = note_id
        note.created_at = utc_now()
        self.working_notes[note_id] = {
            "note": note,
            "processed": False,
        }
        return note

    def list_unprocessed_notes(self, run_id: str, agent_run_id: str) -> list[WorkingMemoryNote]:
        return [
            row["note"]
            for row in self.working_notes.values()
            if row["note"].run_id == run_id and row["note"].agent_run_id == agent_run_id and not row["processed"]
        ]

    def mark_note_processed(self, note_id: str) -> None:
        self.working_notes[note_id]["processed"] = True

    def get_shared_memory_context(self) -> SharedMemoryContext:
        active_constraints = [
            row for row in self.docs.values() if row["doc_type"] == "constraint" and row["status"] == "active"
        ]
        active_portfolio_pages = []
        for item in self.portfolio_items.values():
            if item["status"] not in {"watchlist", "active_position"}:
                continue
            notes = [
                note
                for note in self.portfolio_notes.values()
                if note["item_id"] == item["item_id"] and note["status"] == "active"
            ]
            page = dict(item)
            page["notes"] = notes
            active_portfolio_pages.append(page)
        active_decisions = [note for note in self.portfolio_notes.values() if note["note_type"] == "decision" and note["status"] == "active"]
        active_news = [row for row in self.news_items.values() if row["status"] == "active"]
        open_issues = [row for row in self.system_issues.values() if row["status"] == "open"]
        deliverable_refs = [row for row in self.deliverable_refs.values() if row["status"] in {"draft", "final"}]
        task_states = [row for row in self.task_states.values() if row["status"] in {"pending", "in_progress", "blocked"}]
        docs = [row for row in self.docs.values() if row["status"] == "active"]
        return SharedMemoryContext(
            docs=docs,
            active_constraints=active_constraints,
            active_portfolio_pages=active_portfolio_pages,
            open_system_issues=open_issues,
            active_portfolio_decisions=active_decisions,
            active_news_items=active_news,
            deliverable_refs=deliverable_refs,
            task_states=task_states,
        )

    def create_promotion_attempt(self, **kwargs) -> str:
        attempt_id = self._new_id("attempt")
        self.promotion_attempts[attempt_id] = dict(kwargs) | {"attempt_id": attempt_id}
        return attempt_id

    def create_pending_event(self, pending: PendingMemoryEvent) -> str:
        pending_id = self._new_id("pending")
        pending.pending_id = pending_id
        self.pending_events[pending_id] = pending
        return pending_id

    def list_retryable_pending_events(self, limit: int) -> list[PendingMemoryEvent]:
        events = [
            pending
            for pending in self.pending_events.values()
            if pending.status in {"open", "on_hold"}
        ]
        return events[:limit]

    def update_pending_event_status(
        self,
        pending_id: str,
        status: str,
        reason: str,
        final_event_id: str | None = None,
    ) -> None:
        pending = self.pending_events[pending_id]
        pending.status = status
        pending.retry_count += 1
        pending.last_retry_reason = reason
        pending.last_retry_at = utc_now()
        if final_event_id is not None:
            pending.final_event_id = final_event_id

    def insert_ledger_event(self, event: LedgerEvent) -> str:
        event_id = self._new_id("event")
        event.event_id = event_id
        event.timestamp = utc_now()
        self.ledger_events[event_id] = event
        return event_id

    def mark_ledger_event_projection(
        self,
        event_id: str,
        applied_successfully: bool,
        projection_error_json: dict[str, Any] | None = None,
    ) -> None:
        event = self.ledger_events[event_id]
        event.applied_successfully = applied_successfully
        event.projection_error_json = projection_error_json

    def project_doc(self, event: LedgerEvent, doc_type: str, status: str | None = None) -> None:
        existing = self.docs.get(event.target_id)
        version = (existing["version"] + 1) if existing else 1
        payload = event.payload_json
        self.docs[event.target_id] = {
            "doc_id": event.target_id,
            "doc_type": doc_type,
            "title": payload.get("title", event.target_id),
            "status": status or "active",
            "body": payload.get("body") or payload.get("statement") or payload.get("description") or payload.get("text"),
            "payload_json": payload,
            "version": version,
            "first_seen_event_id": existing["first_seen_event_id"] if existing else event.event_id,
            "last_event_id": event.event_id,
            "reference_memory_json": existing["reference_memory_json"] if existing else {},
        }

    def project_doc_status(self, event: LedgerEvent, status: str) -> None:
        self.docs[event.target_id]["status"] = status
        self.docs[event.target_id]["last_event_id"] = event.event_id

    def project_portfolio_item(self, event: LedgerEvent, status: str | None = None) -> None:
        existing = self.portfolio_items.get(event.target_id)
        payload = event.payload_json
        self.portfolio_items[event.target_id] = {
            "item_id": event.target_id,
            "name": payload.get("name", event.target_id),
            "symbol": payload.get("symbol"),
            "market": payload.get("market"),
            "asset_type": payload.get("asset_type", "equity"),
            "status": status or payload.get("status", "watchlist"),
            "position_status": payload.get("position_status", "not_held"),
            "official_entry": payload.get("official_entry"),
            "entry_range_json": payload.get("entry_range_json") or {},
            "exit_range_json": payload.get("exit_range_json") or {},
            "thesis": payload.get("thesis"),
            "risks_json": payload.get("risks_json") or [],
            "learnings_json": payload.get("learnings_json") or [],
            "payload_json": payload,
            "first_seen_event_id": existing["first_seen_event_id"] if existing else event.event_id,
            "last_event_id": event.event_id,
            "reference_memory_json": existing["reference_memory_json"] if existing else {},
        }

    def project_portfolio_item_status(self, event: LedgerEvent, status: str) -> None:
        self.portfolio_items[event.target_id]["status"] = status

    def project_portfolio_note(self, event: LedgerEvent, note_type: str, status: str | None = None) -> None:
        existing = self.portfolio_notes.get(event.target_id)
        payload = event.payload_json
        self.portfolio_notes[event.target_id] = {
            "note_id": event.target_id,
            "item_id": payload["item_id"],
            "note_type": note_type,
            "status": status or "active",
            "title": payload.get("title", event.target_id),
            "body": payload.get("body") or payload.get("description") or payload.get("statement") or payload.get("result"),
            "payload_json": payload,
            "first_seen_event_id": existing["first_seen_event_id"] if existing else event.event_id,
            "last_event_id": event.event_id,
            "reference_memory_json": existing["reference_memory_json"] if existing else {},
        }

    def project_portfolio_note_status(self, event: LedgerEvent, status: str) -> None:
        self.portfolio_notes[event.target_id]["status"] = status
        self.portfolio_notes[event.target_id]["last_event_id"] = event.event_id

    def project_news_item(self, event: LedgerEvent, status: str | None = None) -> None:
        existing = self.news_items.get(event.target_id)
        payload = event.payload_json
        self.news_items[event.target_id] = {
            "news_item_id": event.target_id,
            "title": payload.get("title", event.target_id),
            "status": status or "active",
            "summary": payload.get("summary"),
            "researched_summary": payload.get("researched_summary"),
            "source_type": payload.get("source_type"),
            "source_uri": payload.get("source_uri"),
            "related_entities_json": payload.get("related_entities_json") or [],
            "related_docs_json": payload.get("related_docs_json") or [],
            "impact": payload.get("impact"),
            "severity": payload.get("severity"),
            "valid_until": payload.get("valid_until"),
            "payload_json": payload,
            "first_seen_event_id": existing["first_seen_event_id"] if existing else event.event_id,
            "last_event_id": event.event_id,
        }

    def project_news_item_status(self, event: LedgerEvent, status: str) -> None:
        self.news_items[event.target_id]["status"] = status

    def project_deliverable_ref(self, event: LedgerEvent, status: str | None = None) -> None:
        existing = self.deliverable_refs.get(event.target_id)
        payload = event.payload_json
        self.deliverable_refs[event.target_id] = {
            "deliverable_id": event.target_id,
            "deliverable_type": payload.get("deliverable_type"),
            "title": payload.get("title", event.target_id),
            "status": status or payload.get("status", "draft"),
            "subject_entities_json": payload.get("subject_entities_json") or [],
            "storage_bucket": payload.get("storage_bucket"),
            "storage_path": payload.get("storage_path"),
            "source_events_json": payload.get("source_events_json") or [],
            "source_snapshot_id": payload.get("source_snapshot_id"),
            "human_decision": payload.get("human_decision"),
            "decision_notes": payload.get("decision_notes"),
            "first_seen_event_id": existing["first_seen_event_id"] if existing else event.event_id,
            "last_event_id": event.event_id,
        }

    def project_deliverable_ref_status(self, event: LedgerEvent, status: str) -> None:
        self.deliverable_refs[event.target_id]["status"] = status

    def project_system_issue(self, event: LedgerEvent, status: str | None = None) -> None:
        existing = self.system_issues.get(event.target_id)
        payload = event.payload_json
        self.system_issues[event.target_id] = {
            "issue_id": event.target_id,
            "title": payload.get("title", event.target_id),
            "description": payload.get("description"),
            "status": status or "open",
            "severity": payload.get("severity"),
            "entity_type": payload.get("entity_type"),
            "entity_id": payload.get("entity_id"),
            "payload_json": payload,
            "first_seen_event_id": existing["first_seen_event_id"] if existing else event.event_id,
            "last_event_id": event.event_id,
            "reference_memory_json": existing["reference_memory_json"] if existing else {},
        }

    def project_system_issue_status(self, event: LedgerEvent, status: str) -> None:
        self.system_issues[event.target_id]["status"] = status
        self.system_issues[event.target_id]["last_event_id"] = event.event_id

    def project_task_state(self, event: LedgerEvent) -> None:
        existing = self.task_states.get(event.target_id)
        payload = event.payload_json
        self.task_states[event.target_id] = {
            "task_id": event.target_id,
            "status": payload.get("status"),
            "phase": payload.get("phase"),
            "owner_agent": payload.get("owner_agent", event.source_agent),
            "blockers_json": payload.get("blockers_json") or [],
            "payload_json": payload,
            "first_seen_event_id": existing["first_seen_event_id"] if existing else event.event_id,
            "last_event_id": event.event_id,
        }

    def create_snapshot(self, run_id: str | None, snapshot_type: str, snapshot_json: dict[str, Any]) -> str:
        snapshot_id = self._new_id("snapshot")
        self.snapshots[snapshot_id] = {
            "snapshot_id": snapshot_id,
            "run_id": run_id,
            "snapshot_type": snapshot_type,
            "snapshot_json": snapshot_json,
        }
        return snapshot_id

    def create_deliverable(self, draft: DeliverableDraft, generated_by_agent_run_id: str | None = None) -> str:
        report_id = self._new_id("report")
        self.reports[report_id] = {
            "report_id": report_id,
            "deliverable_id": None,
            "report_type": draft.report_type,
            "title": draft.title,
            "status": "draft",
            "markdown_body": draft.markdown_body,
            "summary": draft.summary,
            "source_events_json": draft.source_events_json,
            "source_documents_json": draft.source_documents_json,
            "source_sml_objects_json": draft.source_sml_objects_json,
            "generated_by_agent_run_id": generated_by_agent_run_id,
        }
        for index, section in enumerate(draft.sections, start=1):
            self.report_sections.append(
                {
                    "report_id": report_id,
                    "section_order": index,
                    "section_type": section.section_type,
                    "title": section.title,
                    "body": section.body,
                    "evidence_refs_json": section.evidence_refs_json,
                }
            )
        return report_id

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{next(self._ids)}"
