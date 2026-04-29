from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from financial_model.domain.models import DeliverableDraft, DeliverableSection, SharedMemoryContext
from financial_model.domain.utils import slugify
from financial_model.memory.shared_memory import SharedMemory
from financial_model.runtime.protocols import GovernedRepository


@dataclass(slots=True)
class DeliverableBuilder:
    name: str
    role: str
    build: Callable[[SharedMemoryContext], DeliverableDraft]


class DeliverableService:
    def __init__(self, repository: GovernedRepository, shared_memory: SharedMemory):
        self.repository = repository
        self.shared_memory = shared_memory

    def build_daily_brief(self, context: SharedMemoryContext | None = None, title: str | None = None) -> DeliverableDraft:
        context = context or self.shared_memory.get_context()
        active_items = context.active_portfolio_pages[:5]
        active_news = context.active_news_items[:5]
        open_issues = context.open_system_issues[:5]

        sections = [
            DeliverableSection(
                title="Portfolio Focus",
                body=self._portfolio_summary(active_items),
                section_type="portfolio",
            ),
            DeliverableSection(
                title="Active News",
                body=self._news_summary(active_news),
                section_type="news",
            ),
            DeliverableSection(
                title="Open System Issues",
                body=self._issue_summary(open_issues),
                section_type="issues",
            ),
        ]
        markdown_body = "\n\n".join(f"## {section.title}\n{section.body}" for section in sections)
        return DeliverableDraft(
            deliverable_type="daily_brief",
            title=title or "Daily Market Brief",
            report_type="daily_brief",
            markdown_body=markdown_body,
            summary="Daily summary of trusted portfolio state, news, and open issues.",
            source_sml_objects_json=[
                {"bucket": "portfolio.item", "count": len(active_items)},
                {"bucket": "news.item", "count": len(active_news)},
                {"bucket": "system.issue", "count": len(open_issues)},
            ],
            sections=sections,
        )

    def build_ticker_report(self, item_id: str, context: SharedMemoryContext | None = None) -> DeliverableDraft:
        context = context or self.shared_memory.get_context()
        page = next((row for row in context.active_portfolio_pages if row.get("item_id") == item_id), None)
        if page is None:
            raise ValueError(f"Portfolio item '{item_id}' is not active.")

        notes = page.get("notes", [])
        sections = [
            DeliverableSection(
                title="Item Snapshot",
                body=self._ticker_snapshot(page),
                section_type="snapshot",
            ),
            DeliverableSection(
                title="Active Notes",
                body=self._note_summary(notes),
                section_type="notes",
            ),
        ]
        markdown_body = "\n\n".join(f"## {section.title}\n{section.body}" for section in sections)
        return DeliverableDraft(
            deliverable_type="ticker_report",
            title=f"{page.get('name') or item_id} Report",
            report_type="ticker_report",
            markdown_body=markdown_body,
            summary=f"Trusted memory snapshot for {page.get('name') or item_id}.",
            subject_entities_json=[{"item_id": item_id, "symbol": page.get("symbol")}],
            source_sml_objects_json=[{"bucket": "portfolio.item", "item_id": item_id}],
            sections=sections,
        )

    def build_trade_memo(self, item_id: str, context: SharedMemoryContext | None = None) -> DeliverableDraft:
        context = context or self.shared_memory.get_context()
        page = next((row for row in context.active_portfolio_pages if row.get("item_id") == item_id), None)
        if page is None:
            raise ValueError(f"Portfolio item '{item_id}' is not active.")

        notes = page.get("notes", [])
        decisions = [note for note in notes if note.get("note_type") == "decision" and note.get("status") == "active"]
        risks = [note for note in notes if note.get("note_type") == "risk" and note.get("status") == "active"]

        sections = [
            DeliverableSection(
                title="Setup",
                body=self._ticker_snapshot(page),
                section_type="setup",
            ),
            DeliverableSection(
                title="Active Decisions",
                body=self._note_summary(decisions),
                section_type="decisions",
            ),
            DeliverableSection(
                title="Active Risks",
                body=self._note_summary(risks),
                section_type="risks",
            ),
        ]
        markdown_body = "\n\n".join(f"## {section.title}\n{section.body}" for section in sections)
        return DeliverableDraft(
            deliverable_type="trade_memo",
            title=f"{page.get('name') or item_id} Trade Memo",
            report_type="trade_memo",
            markdown_body=markdown_body,
            summary=f"Trade memo assembled from trusted portfolio state for {page.get('name') or item_id}.",
            subject_entities_json=[{"item_id": item_id, "symbol": page.get("symbol")}],
            source_sml_objects_json=[{"bucket": "portfolio.item", "item_id": item_id}],
            sections=sections,
        )

    def persist_draft(
        self,
        draft: DeliverableDraft,
        run_id: str | None,
        generated_by_agent_run_id: str | None = None,
    ) -> tuple[str, str, str]:
        snapshot_id = self.repository.create_snapshot(run_id, "pre_report", self.shared_memory.snapshot())
        report_id = self.repository.create_deliverable(draft, generated_by_agent_run_id=generated_by_agent_run_id)
        reference_note = self.build_reference_note(draft, report_id, snapshot_id)
        return report_id, snapshot_id, reference_note

    def build_reference_note(self, draft: DeliverableDraft, report_id: str, snapshot_id: str) -> str:
        target_id = slugify(draft.title, prefix=draft.deliverable_type)
        payload = {
            "decision": "accept",
            "bucket": "deliverables.ref",
            "target_id": target_id,
            "operation": "upsert",
            "payload": {
                "deliverable_type": draft.deliverable_type,
                "title": draft.title,
                "status": "draft",
                "subject_entities_json": draft.subject_entities_json,
                "storage_path": f"report:{report_id}",
                "source_events_json": draft.source_events_json,
                "source_snapshot_id": snapshot_id,
            },
            "rationale": "deliverable_reference_generation",
        }
        return json.dumps(payload)

    def _portfolio_summary(self, items: list[dict]) -> str:
        if not items:
            return "No active portfolio pages."
        return "\n".join(
            f"- {item.get('name')} ({item.get('symbol') or item.get('item_id')}): {item.get('status')}"
            for item in items
        )

    def _news_summary(self, news_items: list[dict]) -> str:
        if not news_items:
            return "No active trusted news items."
        return "\n".join(f"- {item.get('title')}: {item.get('summary') or 'No summary'}" for item in news_items)

    def _issue_summary(self, issues: list[dict]) -> str:
        if not issues:
            return "No open system issues."
        return "\n".join(f"- {issue.get('title')} [{issue.get('severity') or 'unknown'}]" for issue in issues)

    def _ticker_snapshot(self, page: dict) -> str:
        return "\n".join(
            [
                f"- Name: {page.get('name')}",
                f"- Symbol: {page.get('symbol') or 'n/a'}",
                f"- Status: {page.get('status')}",
                f"- Position Status: {page.get('position_status')}",
                f"- Thesis: {page.get('thesis') or 'n/a'}",
            ]
        )

    def _note_summary(self, notes: list[dict]) -> str:
        if not notes:
            return "No matching notes."
        return "\n".join(
            f"- {note.get('title') or note.get('note_id')}: {note.get('body') or 'No detail'}"
            for note in notes
        )
