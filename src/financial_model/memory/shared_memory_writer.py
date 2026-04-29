from __future__ import annotations

from financial_model.domain.models import LedgerEvent
from financial_model.runtime.protocols import GovernedRepository


DOC_STATUS_BY_OPERATION = {
    "invalidate": "invalidated",
    "supersede": "superseded",
    "archive": "archived",
}

PORTFOLIO_NOTE_STATUS_BY_OPERATION = {
    "resolve": "resolved",
    "invalidate": "invalidated",
    "supersede": "superseded",
    "archive": "archived",
}

NEWS_STATUS_BY_OPERATION = {
    "dismiss": "dismissed",
    "archive": "archived",
    "supersede": "superseded",
    "stale": "stale",
}

DELIVERABLE_STATUS_BY_OPERATION = {
    "finalize": "final",
    "supersede": "superseded",
    "reject": "rejected",
    "archive": "archived",
}

SYSTEM_ISSUE_STATUS_BY_OPERATION = {
    "resolve": "resolved",
    "invalidate": "invalidated",
    "archive": "archived",
}


class SharedMemoryWriter:
    def __init__(self, repository: GovernedRepository):
        self.repository = repository

    def write(self, event: LedgerEvent) -> None:
        bucket = event.bucket
        if bucket.startswith("docs."):
            self._write_doc(event)
            return
        if bucket == "portfolio.item":
            self._write_portfolio_item(event)
            return
        if bucket.startswith("portfolio."):
            self._write_portfolio_note(event)
            return
        if bucket.startswith("news."):
            self._write_news_item(event)
            return
        if bucket == "deliverables.ref":
            self._write_deliverable_ref(event)
            return
        if bucket == "system.issue":
            self._write_system_issue(event)
            return
        if bucket == "system.task_state":
            self.repository.project_task_state(event)
            return
        raise ValueError(f"Unknown projection bucket '{bucket}'.")

    def _write_doc(self, event: LedgerEvent) -> None:
        doc_type = event.bucket.split(".", 1)[1]
        status = DOC_STATUS_BY_OPERATION.get(event.operation)
        if status:
            self.repository.project_doc_status(event, status)
            return
        self.repository.project_doc(event, doc_type=doc_type, status="active")

    def _write_portfolio_item(self, event: LedgerEvent) -> None:
        if event.operation == "archive":
            self.repository.project_portfolio_item_status(event, "archived")
            return
        self.repository.project_portfolio_item(event)

    def _write_portfolio_note(self, event: LedgerEvent) -> None:
        note_type = event.bucket.split(".", 1)[1]
        if note_type == "note":
            note_type = event.payload_json.get("note_type", "issue")
        status = PORTFOLIO_NOTE_STATUS_BY_OPERATION.get(event.operation)
        if status:
            self.repository.project_portfolio_note_status(event, status)
            return
        self.repository.project_portfolio_note(event, note_type=note_type, status="active")

    def _write_news_item(self, event: LedgerEvent) -> None:
        status = NEWS_STATUS_BY_OPERATION.get(event.operation)
        if status:
            self.repository.project_news_item_status(event, status)
            return
        self.repository.project_news_item(event, status="active")

    def _write_deliverable_ref(self, event: LedgerEvent) -> None:
        status = DELIVERABLE_STATUS_BY_OPERATION.get(event.operation)
        if status:
            self.repository.project_deliverable_ref_status(event, status)
            return
        self.repository.project_deliverable_ref(event)

    def _write_system_issue(self, event: LedgerEvent) -> None:
        status = SYSTEM_ISSUE_STATUS_BY_OPERATION.get(event.operation)
        if status:
            self.repository.project_system_issue_status(event, status)
            return
        self.repository.project_system_issue(event, status="open")
