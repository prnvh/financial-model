from __future__ import annotations

from financial_model.domain.models import PendingMemoryEvent, ResolvedWrite, WriteDecision, WriteRequest
from financial_model.runtime.protocols import GovernedRepository


class PendingMemoryQueue:
    def __init__(self, repository: GovernedRepository):
        self.repository = repository

    def enqueue(
        self,
        resolved_write: ResolvedWrite,
        source_agent: str,
        raw_input: str,
        write_request: WriteRequest,
    ) -> str:
        pending = PendingMemoryEvent(
            bucket=resolved_write.bucket or "",
            operation=resolved_write.operation or "",
            original_write_request_json=self._write_request_to_dict(write_request),
            target_id=write_request.target_id,
            source_agent=source_agent,
            raw_input=raw_input,
            reference_text=resolved_write.reference_text,
            reason=resolved_write.resolution_reason,
            payload_json=resolved_write.payload or {},
            candidate_aliases_json=list(write_request.candidate_aliases or []),
            candidate_matches_json=list(resolved_write.candidate_matches),
            confidence=write_request.confidence,
        )
        return self.repository.create_pending_event(pending)

    def get_retryable(self, limit: int = 25) -> list[PendingMemoryEvent]:
        return self.repository.list_retryable_pending_events(limit)

    def mark_on_hold(self, pending_id: str, reason: str) -> None:
        self.repository.update_pending_event_status(pending_id, "on_hold", reason)

    def mark_rejected(self, pending_id: str, reason: str) -> None:
        self.repository.update_pending_event_status(pending_id, "rejected", reason)

    def mark_committed(self, pending_id: str, event_id: str, reason: str) -> None:
        self.repository.update_pending_event_status(pending_id, "committed", reason, final_event_id=event_id)

    def rebuild_write_request(self, pending: PendingMemoryEvent) -> WriteRequest:
        raw = pending.original_write_request_json
        return WriteRequest(
            decision=WriteDecision(raw.get("decision", "accept")),
            rationale=raw.get("rationale", pending.reason),
            bucket=raw.get("bucket"),
            target_id=raw.get("target_id"),
            operation=raw.get("operation"),
            payload=raw.get("payload"),
            reference_text=raw.get("reference_text"),
            candidate_aliases=list(raw.get("candidate_aliases") or []),
            confidence=raw.get("confidence"),
        )

    def _write_request_to_dict(self, write_request: WriteRequest) -> dict:
        return {
            "decision": write_request.decision.value,
            "rationale": write_request.rationale,
            "bucket": write_request.bucket,
            "target_id": write_request.target_id,
            "operation": write_request.operation,
            "payload": write_request.payload,
            "reference_text": write_request.reference_text,
            "candidate_aliases": list(write_request.candidate_aliases or []),
            "confidence": write_request.confidence,
        }
