from __future__ import annotations

import json

from financial_model.domain.models import LedgerEvent, ResolutionDecision, ResolvedWrite, WriteRequest
from financial_model.memory.pending_memory import PendingMemoryQueue
from financial_model.memory.shared_memory_writer import SharedMemoryWriter
from financial_model.runtime.protocols import GovernedRepository


class Inputter:
    def __init__(
        self,
        repository: GovernedRepository,
        shared_memory_writer: SharedMemoryWriter,
        pending_queue: PendingMemoryQueue | None = None,
    ):
        self.repository = repository
        self.shared_memory_writer = shared_memory_writer
        self.pending_queue = pending_queue or PendingMemoryQueue(repository)

    def write_resolved(
        self,
        resolved_write: ResolvedWrite,
        source_agent: str,
        raw_input: str = "",
        write_request: WriteRequest | None = None,
        source_attempt_id: str | None = None,
    ) -> str:
        if resolved_write.decision is not ResolutionDecision.COMMIT:
            raise ValueError("write_resolved requires ResolvedWrite(decision=commit).")

        source_ref = {
            "matched_target_id": resolved_write.matched_target_id,
            "candidate_matches": resolved_write.candidate_matches,
            "resolution_reason": resolved_write.resolution_reason,
            "reference_text": resolved_write.reference_text,
            "candidate_aliases": list(write_request.candidate_aliases or []) if write_request else [],
        }
        event = LedgerEvent(
            source_agent=source_agent,
            source_attempt_id=source_attempt_id,
            bucket=resolved_write.bucket or "",
            target_id=resolved_write.resolved_target_id or "",
            operation=resolved_write.operation or "",
            payload_json=resolved_write.payload or {},
            raw_input=raw_input,
            source_ref=json.dumps(source_ref),
        )

        projection_error = None
        with self.repository.transaction():
            event_id = self.repository.insert_ledger_event(event)
            try:
                with self.repository.transaction():
                    self.shared_memory_writer.write(event)
            except Exception as exc:
                projection_error = {
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
                self.repository.mark_ledger_event_projection(
                    event_id,
                    applied_successfully=False,
                    projection_error_json=projection_error,
                )
            else:
                self.repository.mark_ledger_event_projection(event_id, applied_successfully=True)

        return event_id

    def write_provisional(
        self,
        resolved_write: ResolvedWrite,
        source_agent: str,
        raw_input: str,
        write_request: WriteRequest,
    ) -> str:
        if resolved_write.decision is not ResolutionDecision.PROVISIONAL:
            raise ValueError("write_provisional requires ResolvedWrite(decision=provisional).")
        return self.pending_queue.enqueue(
            resolved_write=resolved_write,
            source_agent=source_agent,
            raw_input=raw_input,
            write_request=write_request,
        )
