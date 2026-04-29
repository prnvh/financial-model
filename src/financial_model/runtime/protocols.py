from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol

from financial_model.domain.models import (
    AgentRunSummary,
    DeliverableDraft,
    LedgerEvent,
    PendingMemoryEvent,
    SharedMemoryContext,
    WorkingMemoryNote,
    WriteRequest,
)


class Interpreter(Protocol):
    def interpret(
        self,
        candidate_note: str,
        agent_name: str,
        context: SharedMemoryContext | None = None,
    ) -> WriteRequest: ...


class Agent(Protocol):
    name: str
    role: str

    def run(self, context: SharedMemoryContext) -> AgentRunSummary: ...


class GovernedRepository(Protocol):
    def transaction(self) -> AbstractContextManager[object]: ...

    def create_cron_run(self, trigger_type: str, run_type: str, config_json: dict[str, Any]) -> str: ...

    def update_cron_run_status(
        self,
        run_id: str,
        status: str,
        error_json: dict[str, Any] | None = None,
    ) -> None: ...

    def create_agent_run(
        self,
        run_id: str,
        agent_name: str,
        agent_role: str,
        input_context_json: dict[str, Any],
        model_name: str | None = None,
    ) -> str: ...

    def update_agent_run(
        self,
        agent_run_id: str,
        status: str,
        output_summary: str | None = None,
        token_usage_json: dict[str, Any] | None = None,
        cost_estimate: float | None = None,
        error_json: dict[str, Any] | None = None,
    ) -> None: ...

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
    ) -> str: ...

    def add_working_memory_note(self, note: WorkingMemoryNote) -> WorkingMemoryNote: ...

    def list_unprocessed_notes(self, run_id: str, agent_run_id: str) -> list[WorkingMemoryNote]: ...

    def mark_note_processed(self, note_id: str) -> None: ...

    def get_shared_memory_context(self) -> SharedMemoryContext: ...

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
    ) -> str: ...

    def create_pending_event(self, pending: PendingMemoryEvent) -> str: ...

    def list_retryable_pending_events(self, limit: int) -> list[PendingMemoryEvent]: ...

    def update_pending_event_status(
        self,
        pending_id: str,
        status: str,
        reason: str,
        final_event_id: str | None = None,
    ) -> None: ...

    def insert_ledger_event(self, event: LedgerEvent) -> str: ...

    def mark_ledger_event_projection(
        self,
        event_id: str,
        applied_successfully: bool,
        projection_error_json: dict[str, Any] | None = None,
    ) -> None: ...

    def project_doc(self, event: LedgerEvent, doc_type: str, status: str | None = None) -> None: ...

    def project_doc_status(self, event: LedgerEvent, status: str) -> None: ...

    def project_portfolio_item(self, event: LedgerEvent, status: str | None = None) -> None: ...

    def project_portfolio_item_status(self, event: LedgerEvent, status: str) -> None: ...

    def project_portfolio_note(self, event: LedgerEvent, note_type: str, status: str | None = None) -> None: ...

    def project_portfolio_note_status(self, event: LedgerEvent, status: str) -> None: ...

    def project_news_item(self, event: LedgerEvent, status: str | None = None) -> None: ...

    def project_news_item_status(self, event: LedgerEvent, status: str) -> None: ...

    def project_deliverable_ref(self, event: LedgerEvent, status: str | None = None) -> None: ...

    def project_deliverable_ref_status(self, event: LedgerEvent, status: str) -> None: ...

    def project_system_issue(self, event: LedgerEvent, status: str | None = None) -> None: ...

    def project_system_issue_status(self, event: LedgerEvent, status: str) -> None: ...

    def project_task_state(self, event: LedgerEvent) -> None: ...

    def create_snapshot(self, run_id: str | None, snapshot_type: str, snapshot_json: dict[str, Any]) -> str: ...

    def create_deliverable(self, draft: DeliverableDraft, generated_by_agent_run_id: str | None = None) -> str: ...
