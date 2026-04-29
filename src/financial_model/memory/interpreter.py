from __future__ import annotations

import json
import re

from financial_model.domain.buckets import BUCKET_SPECS
from financial_model.domain.models import SharedMemoryContext, WriteDecision, WriteRequest
from financial_model.domain.utils import slugify
from financial_model.runtime.protocols import Interpreter


SEVERITIES = ("low", "medium", "high", "critical")


class FinancialInterpreter:
    def __init__(self, fallback_interpreter: Interpreter | None = None):
        self.fallback_interpreter = fallback_interpreter

    def interpret(
        self,
        candidate_note: str,
        agent_name: str,
        context: SharedMemoryContext | None = None,
    ) -> WriteRequest:
        text = candidate_note.strip()
        if not text:
            return WriteRequest.reject("empty_note")

        structured = self._parse_structured_json(text)
        if structured is not None:
            return structured

        heuristic = self._heuristic_write_request(text, context or SharedMemoryContext())
        if heuristic is not None:
            return heuristic

        if self.fallback_interpreter is not None:
            return self.fallback_interpreter.interpret(text, agent_name, context)

        return WriteRequest.reject("no_interpreter_rule_matched")

    def _parse_structured_json(self, text: str) -> WriteRequest | None:
        stripped = text
        if stripped.startswith("```"):
            parts = stripped.split("```")
            if len(parts) >= 3:
                stripped = parts[1]
                if stripped.startswith("json"):
                    stripped = stripped[4:]
                stripped = stripped.strip()

        if not (stripped.startswith("{") and stripped.endswith("}")):
            return None

        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return None

        decision = payload.get("decision")
        if decision == "reject":
            return WriteRequest.reject(payload.get("rationale", "structured_reject"))
        if decision != "accept":
            return None

        bucket = payload.get("bucket")
        if bucket not in BUCKET_SPECS:
            return None

        return WriteRequest(
            decision=WriteDecision.ACCEPT,
            rationale=payload.get("rationale", "structured_json"),
            bucket=bucket,
            target_id=payload.get("target_id"),
            operation=payload.get("operation"),
            payload=payload.get("payload") or {},
            reference_text=payload.get("reference_text"),
            candidate_aliases=list(payload.get("candidate_aliases") or []),
            confidence=payload.get("confidence"),
        )

    def _heuristic_write_request(
        self,
        text: str,
        context: SharedMemoryContext,
    ) -> WriteRequest | None:
        lowered = text.lower()

        if lowered.startswith("constraint:"):
            statement = text.split(":", 1)[1].strip()
            title = self._title_from_text(statement, prefix="constraint")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_constraint",
                bucket="docs.constraint",
                target_id=slugify(title, prefix="constraint"),
                operation="upsert",
                payload={"title": title, "statement": statement},
            )

        if lowered.startswith("strategy:"):
            body = text.split(":", 1)[1].strip()
            title = self._title_from_text(body, prefix="strategy")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_strategy",
                bucket="docs.strategy",
                target_id=slugify(title, prefix="strategy"),
                operation="upsert",
                payload={"title": title, "body": body},
            )

        if lowered.startswith("thesis:"):
            body = text.split(":", 1)[1].strip()
            title = self._title_from_text(body, prefix="thesis")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_thesis",
                bucket="docs.thesis",
                target_id=slugify(title, prefix="thesis"),
                operation="upsert",
                payload={"title": title, "body": body},
            )

        if lowered.startswith("learning:"):
            statement = text.split(":", 1)[1].strip()
            title = self._title_from_text(statement, prefix="learning")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_learning",
                bucket="docs.learning",
                target_id=slugify(title, prefix="learning"),
                operation="append",
                payload={"title": title, "statement": statement},
            )

        if lowered.startswith("issue:"):
            body = text.split(":", 1)[1].strip()
            title = self._title_from_text(body, prefix="issue")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_issue",
                bucket="system.issue",
                target_id=slugify(title, prefix="issue"),
                operation="upsert",
                payload={
                    "title": title,
                    "description": body,
                    "severity": self._extract_severity(lowered),
                },
            )

        if lowered.startswith("task state:"):
            state_text = text.split(":", 1)[1].strip()
            status = self._extract_task_status(state_text.lower())
            if status is None:
                return WriteRequest.reject("task_state_missing_status")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_task_state",
                bucket="system.task_state",
                target_id="main",
                operation="upsert",
                payload={"status": status, "phase": None, "blockers_json": []},
            )

        if lowered.startswith("portfolio item:"):
            item_text = text.split(":", 1)[1].strip()
            name, symbol = self._extract_item_identity(item_text)
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_portfolio_item",
                bucket="portfolio.item",
                target_id=slugify(symbol or name, prefix="item"),
                operation="upsert",
                payload={"name": name, "symbol": symbol, "status": "watchlist"},
            )

        if lowered.startswith("risk:"):
            body = text.split(":", 1)[1].strip()
            item = self._match_portfolio_item(body, context)
            if item is None:
                return WriteRequest.reject("risk_missing_portfolio_item_reference")
            title = self._title_from_text(body, prefix="risk")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_portfolio_risk",
                bucket="portfolio.risk",
                target_id=slugify(f"{item['item_id']}_{title}", prefix="risk"),
                operation="upsert",
                payload={
                    "item_id": item["item_id"],
                    "title": title,
                    "severity": self._extract_severity(lowered),
                    "description": body,
                },
                candidate_aliases=[item.get("symbol"), item.get("name")],
            )

        if lowered.startswith("decision:"):
            body = text.split(":", 1)[1].strip()
            item = self._match_portfolio_item(body, context)
            if item is None:
                return WriteRequest.reject("decision_missing_portfolio_item_reference")
            title = self._title_from_text(body, prefix="decision")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_portfolio_decision",
                bucket="portfolio.decision",
                target_id=slugify(f"{item['item_id']}_{title}", prefix="decision"),
                operation="append",
                payload={
                    "item_id": item["item_id"],
                    "title": title,
                    "statement": body,
                },
                candidate_aliases=[item.get("symbol"), item.get("name")],
            )

        if lowered.startswith("news:"):
            body = text.split(":", 1)[1].strip()
            related = self._extract_related_entities(body, context)
            title = self._title_from_text(body, prefix="news")
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_news_item",
                bucket="news.item",
                target_id=slugify(title, prefix="news"),
                operation="upsert",
                payload={
                    "title": title,
                    "summary": body,
                    "related_entities_json": related,
                },
            )

        task_status = self._extract_task_status(lowered)
        if task_status is not None:
            return WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale="heuristic_inline_task_state",
                bucket="system.task_state",
                target_id="main",
                operation="upsert",
                payload={"status": task_status, "phase": None, "blockers_json": []},
            )

        return None

    def _title_from_text(self, text: str, prefix: str) -> str:
        head = text.split(".")[0].split(";")[0].strip()
        if not head:
            return prefix
        return head[:80]

    def _extract_severity(self, lowered: str) -> str:
        for severity in ("critical", "high", "medium", "low"):
            if severity in lowered:
                return severity
        return "medium"

    def _extract_task_status(self, lowered: str) -> str | None:
        if "blocked" in lowered:
            return "blocked"
        if "in progress" in lowered or "in_progress" in lowered or "started" in lowered:
            return "in_progress"
        if "done" in lowered or "complete" in lowered or "completed" in lowered:
            return "done"
        if "failed" in lowered:
            return "failed"
        if "pending" in lowered:
            return "pending"
        return None

    def _match_portfolio_item(self, text: str, context: SharedMemoryContext) -> dict | None:
        lowered = text.lower()
        for item in context.active_portfolio_pages:
            symbol = str(item.get("symbol") or "").lower()
            name = str(item.get("name") or "").lower()
            if symbol and re.search(rf"\b{re.escape(symbol)}\b", lowered):
                return item
            if name and name in lowered:
                return item
        return None

    def _extract_related_entities(self, text: str, context: SharedMemoryContext) -> list[dict]:
        related = []
        lowered = text.lower()
        for item in context.active_portfolio_pages:
            symbol = str(item.get("symbol") or "").lower()
            name = str(item.get("name") or "").lower()
            if symbol and re.search(rf"\b{re.escape(symbol)}\b", lowered):
                related.append({"item_id": item["item_id"], "symbol": item.get("symbol")})
                continue
            if name and name in lowered:
                related.append({"item_id": item["item_id"], "name": item.get("name")})
        return related

    def _extract_item_identity(self, text: str) -> tuple[str, str | None]:
        if " - " in text:
            left, right = text.split(" - ", 1)
            name = right.strip() or left.strip()
            symbol = left.strip().upper()
            return name, symbol
        tokens = text.split()
        if tokens and tokens[0].isupper() and len(tokens[0]) <= 8:
            return text, tokens[0]
        return text, None
