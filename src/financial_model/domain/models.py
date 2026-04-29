from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class TriggerType(StrEnum):
    CRON = "cron"
    MANUAL = "manual"
    WEBHOOK = "webhook"
    TEST = "test"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class NoteType(StrEnum):
    AGENT = "agent"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"
    USER = "user"


class WriteDecision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"


class ResolutionDecision(StrEnum):
    COMMIT = "commit"
    PROVISIONAL = "provisional"
    REJECT = "reject"


class PromotionDecision(StrEnum):
    ACCEPT = "accept"
    PROVISIONAL = "provisional"
    REJECT = "reject"
    INVALID = "invalid"
    ERROR = "error"


@dataclass(slots=True)
class EvidenceRef:
    source_type: str
    source_name: str
    locator: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorkingMemoryNote:
    source_agent: str
    note_type: NoteType
    raw_text: str
    run_id: str | None = None
    agent_run_id: str | None = None
    note_id: str | None = None
    source_ref: str | None = None
    processed_by_promotion: bool = False
    promoted_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class WriteRequest:
    decision: WriteDecision
    rationale: str
    bucket: str | None = None
    target_id: str | None = None
    operation: str | None = None
    payload: dict[str, Any] | None = None
    reference_text: str | None = None
    candidate_aliases: list[str] = field(default_factory=list)
    confidence: float | None = None

    @classmethod
    def reject(cls, rationale: str) -> "WriteRequest":
        return cls(decision=WriteDecision.REJECT, rationale=rationale)


@dataclass(slots=True)
class ResolvedWrite:
    decision: ResolutionDecision
    resolution_reason: str
    bucket: str | None = None
    operation: str | None = None
    resolved_target_id: str | None = None
    matched_target_id: str | None = None
    payload: dict[str, Any] | None = None
    reference_text: str | None = None
    candidate_matches: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class PromotionResult:
    note_text: str
    decision: PromotionDecision
    rationale: str
    event_id: str | None = None
    bucket: str | None = None
    target_id: str | None = None


@dataclass(slots=True)
class LedgerEvent:
    source_agent: str
    bucket: str
    target_id: str
    operation: str
    payload_json: dict[str, Any]
    source_attempt_id: str | None = None
    raw_input: str | None = None
    source_ref: str | None = None
    event_id: str | None = None
    timestamp: datetime | None = None
    applied_successfully: bool = False
    projection_error_json: dict[str, Any] | None = None


@dataclass(slots=True)
class PendingMemoryEvent:
    bucket: str
    operation: str
    original_write_request_json: dict[str, Any]
    pending_id: str | None = None
    target_id: str | None = None
    source_agent: str | None = None
    raw_input: str | None = None
    reference_text: str | None = None
    reason: str = "unspecified"
    payload_json: dict[str, Any] = field(default_factory=dict)
    candidate_aliases_json: list[str] = field(default_factory=list)
    candidate_matches_json: list[dict[str, Any]] = field(default_factory=list)
    confidence: float | None = None
    status: str = "open"
    retry_count: int = 0
    last_retry_at: datetime | None = None
    last_retry_reason: str | None = None
    next_retry_after: datetime | None = None
    final_event_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class SharedMemoryContext:
    docs: list[dict[str, Any]] = field(default_factory=list)
    active_constraints: list[dict[str, Any]] = field(default_factory=list)
    active_portfolio_pages: list[dict[str, Any]] = field(default_factory=list)
    open_system_issues: list[dict[str, Any]] = field(default_factory=list)
    active_portfolio_decisions: list[dict[str, Any]] = field(default_factory=list)
    active_news_items: list[dict[str, Any]] = field(default_factory=list)
    deliverable_refs: list[dict[str, Any]] = field(default_factory=list)
    task_states: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "docs": self.docs,
            "active_constraints": self.active_constraints,
            "active_portfolio_pages": self.active_portfolio_pages,
            "open_system_issues": self.open_system_issues,
            "active_portfolio_decisions": self.active_portfolio_decisions,
            "active_news_items": self.active_news_items,
            "deliverable_refs": self.deliverable_refs,
            "task_states": self.task_states,
        }


@dataclass(slots=True)
class AgentObservation:
    text: str
    source_type: str = "agent"
    entity_type: str | None = None
    entity_id: str | None = None
    event_type: str = "observation"
    payload_json: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True)
class AgentRunSummary:
    output_summary: str
    observations: list[AgentObservation] = field(default_factory=list)
    working_notes: list[WorkingMemoryNote] = field(default_factory=list)
    cost_estimate: float | None = None
    token_usage_json: dict[str, Any] | None = None


@dataclass(slots=True)
class DeliverableSection:
    title: str
    body: str
    section_type: str = "body"
    evidence_refs_json: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class DeliverableDraft:
    deliverable_type: str
    title: str
    report_type: str
    markdown_body: str
    summary: str
    subject_entities_json: list[dict[str, Any]] = field(default_factory=list)
    source_events_json: list[str] = field(default_factory=list)
    source_documents_json: list[str] = field(default_factory=list)
    source_sml_objects_json: list[dict[str, Any]] = field(default_factory=list)
    sections: list[DeliverableSection] = field(default_factory=list)


@dataclass(slots=True)
class TriggerRequest:
    run_type: str
    trigger_type: TriggerType = TriggerType.MANUAL
    config_json: dict[str, Any] = field(default_factory=dict)
