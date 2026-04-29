from __future__ import annotations

import re
from typing import Any

from financial_model.domain.models import ResolvedWrite, ResolutionDecision, SharedMemoryContext, WriteDecision, WriteRequest
from financial_model.domain.utils import slugify


TOKEN_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "by", "for", "from",
    "has", "have", "in", "into", "is", "it", "its", "not", "of", "on", "or",
    "that", "the", "their", "them", "this", "to", "was", "with",
}
SNAKE_CASE_PATTERN = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")


class Resolver:
    def resolve(
        self,
        write_request: WriteRequest,
        raw_input: str,
        context: SharedMemoryContext | None = None,
    ) -> ResolvedWrite:
        if write_request.decision != WriteDecision.ACCEPT:
            return ResolvedWrite(decision=ResolutionDecision.REJECT, resolution_reason=write_request.rationale)

        context = context or SharedMemoryContext()

        if write_request.bucket == "docs.constraint":
            return self._resolve_constraints(write_request, raw_input, context)
        if write_request.bucket == "system.issue":
            return self._resolve_system_issues(write_request, raw_input, context)
        if write_request.bucket == "portfolio.decision":
            return self._resolve_portfolio_decisions(write_request, raw_input, context)
        if write_request.bucket == "portfolio.risk":
            return self._resolve_portfolio_risks(write_request, raw_input, context)

        return ResolvedWrite(
            decision=ResolutionDecision.COMMIT,
            resolution_reason="resolver_passthrough",
            bucket=write_request.bucket,
            operation=write_request.operation,
            resolved_target_id=write_request.target_id or self._creation_target_id(write_request, raw_input, "item"),
            matched_target_id=write_request.target_id,
            payload=write_request.payload or {},
            reference_text=self._reference_text(write_request, raw_input),
        )

    def _resolve_constraints(
        self,
        write_request: WriteRequest,
        raw_input: str,
        context: SharedMemoryContext,
    ) -> ResolvedWrite:
        reference = self._reference_text(write_request, raw_input)
        candidates = context.active_constraints
        matches = self._score_candidates(
            reference,
            candidates,
            id_key="doc_id",
            text_fields=["title", "body"],
            alias_hints=write_request.candidate_aliases,
            requested_target_id=write_request.target_id,
        )
        if write_request.operation == "invalidate":
            matched = self._choose_match(matches)
            if matched is None:
                return self._provisional("docs.constraint", "invalidate", write_request.payload, reference, matches, "unresolved_constraint_reference")
            return ResolvedWrite(
                decision=ResolutionDecision.COMMIT,
                resolution_reason="resolved_constraint_match",
                bucket="docs.constraint",
                operation="invalidate",
                resolved_target_id=matched["candidate_id"],
                matched_target_id=matched["candidate_id"],
                payload=write_request.payload or {},
                reference_text=reference,
                candidate_matches=matches,
            )

        target_id = write_request.target_id or self._creation_target_id(write_request, reference, "constraint")
        return ResolvedWrite(
            decision=ResolutionDecision.COMMIT,
            resolution_reason="constraint_passthrough",
            bucket="docs.constraint",
            operation=write_request.operation,
            resolved_target_id=target_id,
            matched_target_id=target_id,
            payload=write_request.payload or {},
            reference_text=reference,
            candidate_matches=matches,
        )

    def _resolve_system_issues(
        self,
        write_request: WriteRequest,
        raw_input: str,
        context: SharedMemoryContext,
    ) -> ResolvedWrite:
        reference = self._reference_text(write_request, raw_input)
        candidates = context.open_system_issues
        matches = self._score_candidates(
            reference,
            candidates,
            id_key="issue_id",
            text_fields=["title", "description"],
            alias_hints=write_request.candidate_aliases,
            requested_target_id=write_request.target_id,
        )
        if write_request.operation in {"resolve", "invalidate"}:
            matched = self._choose_match(matches)
            if matched is None:
                return self._provisional("system.issue", write_request.operation or "resolve", write_request.payload, reference, matches, "unresolved_system_issue_reference")
            return ResolvedWrite(
                decision=ResolutionDecision.COMMIT,
                resolution_reason="resolved_system_issue_match",
                bucket="system.issue",
                operation=write_request.operation,
                resolved_target_id=matched["candidate_id"],
                matched_target_id=matched["candidate_id"],
                payload=write_request.payload or {},
                reference_text=reference,
                candidate_matches=matches,
            )

        target_id = write_request.target_id or self._creation_target_id(write_request, reference, "issue")
        existing = self._choose_match(matches, min_score=3.0)
        if existing is not None:
            target_id = existing["candidate_id"]
        return ResolvedWrite(
            decision=ResolutionDecision.COMMIT,
            resolution_reason="system_issue_upsert",
            bucket="system.issue",
            operation=write_request.operation,
            resolved_target_id=target_id,
            matched_target_id=existing["candidate_id"] if existing else target_id,
            payload=write_request.payload or {},
            reference_text=reference,
            candidate_matches=matches,
        )

    def _resolve_portfolio_decisions(
        self,
        write_request: WriteRequest,
        raw_input: str,
        context: SharedMemoryContext,
    ) -> ResolvedWrite:
        reference = self._reference_text(write_request, raw_input)
        candidates = context.active_portfolio_decisions
        matches = self._score_candidates(
            reference,
            candidates,
            id_key="note_id",
            text_fields=["title", "body"],
            alias_hints=write_request.candidate_aliases,
            requested_target_id=write_request.target_id,
        )
        if write_request.operation == "invalidate":
            matched = self._choose_match(matches)
            if matched is None:
                return self._provisional("portfolio.decision", "invalidate", write_request.payload, reference, matches, "unresolved_portfolio_decision_reference")
            return ResolvedWrite(
                decision=ResolutionDecision.COMMIT,
                resolution_reason="resolved_portfolio_decision_match",
                bucket="portfolio.decision",
                operation="invalidate",
                resolved_target_id=matched["candidate_id"],
                matched_target_id=matched["candidate_id"],
                payload=write_request.payload or {},
                reference_text=reference,
                candidate_matches=matches,
            )

        target_id = write_request.target_id or self._creation_target_id(write_request, reference, "decision")
        return ResolvedWrite(
            decision=ResolutionDecision.COMMIT,
            resolution_reason="portfolio_decision_passthrough",
            bucket="portfolio.decision",
            operation=write_request.operation,
            resolved_target_id=target_id,
            matched_target_id=target_id,
            payload=write_request.payload or {},
            reference_text=reference,
            candidate_matches=matches,
        )

    def _resolve_portfolio_risks(
        self,
        write_request: WriteRequest,
        raw_input: str,
        context: SharedMemoryContext,
    ) -> ResolvedWrite:
        reference = self._reference_text(write_request, raw_input)
        candidates = [
            note
            for page in context.active_portfolio_pages
            for note in page.get("notes", [])
            if note.get("note_type") == "risk" and note.get("status") == "active"
        ]
        matches = self._score_candidates(
            reference,
            candidates,
            id_key="note_id",
            text_fields=["title", "body"],
            alias_hints=write_request.candidate_aliases,
            requested_target_id=write_request.target_id,
        )
        if write_request.operation in {"resolve", "invalidate"}:
            matched = self._choose_match(matches)
            if matched is None:
                return self._provisional("portfolio.risk", write_request.operation or "resolve", write_request.payload, reference, matches, "unresolved_portfolio_risk_reference")
            return ResolvedWrite(
                decision=ResolutionDecision.COMMIT,
                resolution_reason="resolved_portfolio_risk_match",
                bucket="portfolio.risk",
                operation=write_request.operation,
                resolved_target_id=matched["candidate_id"],
                matched_target_id=matched["candidate_id"],
                payload=write_request.payload or {},
                reference_text=reference,
                candidate_matches=matches,
            )

        target_id = write_request.target_id or self._creation_target_id(write_request, reference, "risk")
        existing = self._choose_match(matches, min_score=3.2)
        if existing is not None:
            target_id = existing["candidate_id"]
        return ResolvedWrite(
            decision=ResolutionDecision.COMMIT,
            resolution_reason="portfolio_risk_upsert",
            bucket="portfolio.risk",
            operation=write_request.operation,
            resolved_target_id=target_id,
            matched_target_id=existing["candidate_id"] if existing else target_id,
            payload=write_request.payload or {},
            reference_text=reference,
            candidate_matches=matches,
        )

    def _provisional(
        self,
        bucket: str,
        operation: str,
        payload: dict[str, Any] | None,
        reference_text: str,
        candidate_matches: list[dict[str, Any]],
        reason: str,
    ) -> ResolvedWrite:
        return ResolvedWrite(
            decision=ResolutionDecision.PROVISIONAL,
            resolution_reason=reason,
            bucket=bucket,
            operation=operation,
            payload=payload or {},
            reference_text=reference_text,
            candidate_matches=candidate_matches,
        )

    def _reference_text(self, write_request: WriteRequest, raw_input: str) -> str:
        reference_text = (write_request.reference_text or "").strip()
        raw = raw_input.strip()
        if reference_text and raw:
            if reference_text.lower() in raw.lower():
                return raw
            return f"{reference_text}\n{raw}"
        return reference_text or raw

    def _creation_target_id(self, write_request: WriteRequest, reference_text: str, prefix: str) -> str:
        if write_request.target_id:
            return write_request.target_id
        explicit = self._single_explicit_slug(reference_text)
        if explicit:
            return explicit
        payload = write_request.payload or {}
        for field in ("title", "statement", "description", "name", "status"):
            value = payload.get(field)
            if value:
                return slugify(str(value), prefix=prefix)
        return slugify(reference_text or prefix, prefix=prefix)

    def _score_candidates(
        self,
        text: str,
        candidates: list[dict[str, Any]],
        id_key: str,
        text_fields: list[str],
        alias_hints: list[str],
        requested_target_id: str | None,
    ) -> list[dict[str, Any]]:
        lowered = text.lower()
        text_tokens = self._tokens(lowered)
        explicit_slugs = set(self._explicit_slugs(lowered))
        matches = []

        for candidate in candidates:
            candidate_id = str(candidate.get(id_key, "") or "")
            score = 0.0
            reasons: list[str] = []
            reference_memory = candidate.get("reference_memory_json") or {}
            aliases = {str(alias).lower() for alias in reference_memory.get("aliases", [])}

            if requested_target_id and candidate_id == requested_target_id:
                score += 4.0
                reasons.append("requested_target_id")
            if candidate_id and candidate_id in explicit_slugs:
                score += 3.0
                reasons.append("explicit_id")
            if explicit_slugs.intersection(aliases):
                score += 2.0
                reasons.append("explicit_alias")

            candidate_text = [candidate_id.replace("_", " ")]
            for field in text_fields:
                value = candidate.get(field)
                if value:
                    candidate_text.append(str(value))
            for key in ("canonical_text", "creation_note_text"):
                value = reference_memory.get(key)
                if value:
                    candidate_text.append(str(value))
            for key in ("reference_phrases", "seen_referring_expressions"):
                values = reference_memory.get(key) or []
                candidate_text.extend(str(value) for value in values if str(value).strip())

            token_overlap = len(text_tokens & self._tokens(" ".join(candidate_text).lower()))
            if token_overlap:
                score += token_overlap / max(len(text_tokens), 1)
                reasons.append(f"token_overlap={token_overlap}")

            for alias in alias_hints or []:
                alias_text = str(alias or "").lower()
                if alias_text and alias_text in " ".join(candidate_text).lower():
                    score += 0.75
                    reasons.append("alias_hint")

            if score > 0:
                matches.append({"candidate_id": candidate_id, "score": round(score, 3), "reasons": reasons})

        matches.sort(key=lambda item: (-item["score"], item["candidate_id"]))
        return matches

    def _choose_match(
        self,
        matches: list[dict[str, Any]],
        min_score: float = 0.6,
        min_gap: float = 0.2,
    ) -> dict[str, Any] | None:
        if not matches:
            return None
        top = matches[0]
        if top["score"] < min_score:
            return None
        if len(matches) > 1 and (top["score"] - matches[1]["score"]) < min_gap:
            return None
        return top

    def _tokens(self, text: str) -> set[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return {token for token in tokens if token not in TOKEN_STOPWORDS}

    def _explicit_slugs(self, text: str) -> list[str]:
        return [match.group(0) for match in SNAKE_CASE_PATTERN.finditer(text)]

    def _single_explicit_slug(self, text: str) -> str | None:
        slugs = list(dict.fromkeys(self._explicit_slugs(text.lower())))
        if len(slugs) == 1:
            return slugs[0]
        return None
