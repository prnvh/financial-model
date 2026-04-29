from __future__ import annotations

import re

from financial_model.domain.buckets import get_bucket_spec
from financial_model.domain.models import ResolvedWrite, ResolutionDecision, SharedMemoryContext, WriteDecision, WriteRequest


SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_\-]*$")
VALID_TASK_STATUSES = {"pending", "in_progress", "blocked", "done", "failed", "cancelled"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}


class ValidationError(Exception):
    pass


class Validator:
    def validate(self, write_request: WriteRequest, context: SharedMemoryContext | None = None) -> None:
        if write_request.decision != WriteDecision.ACCEPT:
            raise ValidationError("Only accepted write requests can be validated.")

        if not write_request.bucket:
            raise ValidationError("bucket is required.")

        spec = get_bucket_spec(write_request.bucket)

        if write_request.operation not in spec.allowed_operations:
            raise ValidationError(
                f"Operation '{write_request.operation}' is not allowed for bucket '{write_request.bucket}'."
            )

        if not write_request.target_id or not SLUG_PATTERN.match(write_request.target_id):
            raise ValidationError("target_id must be a non-empty slug-like identifier.")

        payload = write_request.payload or {}
        lifecycle_ops = {"resolve", "invalidate", "supersede", "archive", "dismiss", "stale", "reject", "finalize"}
        if write_request.operation not in lifecycle_ops:
            missing = [field for field in spec.required_fields if payload.get(field) in (None, "", [])]
            if missing:
                raise ValidationError(
                    f"payload for bucket '{write_request.bucket}' is missing required fields: {missing}"
                )

        self._validate_bucket_specific(write_request, context or SharedMemoryContext())

    def validate_resolved(self, resolved_write: ResolvedWrite, context: SharedMemoryContext | None = None) -> None:
        if resolved_write.decision != ResolutionDecision.COMMIT:
            raise ValidationError("validate_resolved only accepts committed writes.")

        self.validate(
            WriteRequest(
                decision=WriteDecision.ACCEPT,
                rationale=resolved_write.resolution_reason,
                bucket=resolved_write.bucket,
                target_id=resolved_write.resolved_target_id,
                operation=resolved_write.operation,
                payload=resolved_write.payload,
                reference_text=resolved_write.reference_text,
            ),
            context=context,
        )

    def _validate_bucket_specific(self, write_request: WriteRequest, context: SharedMemoryContext) -> None:
        payload = write_request.payload or {}
        bucket = write_request.bucket or ""
        operation = write_request.operation or ""

        severity = payload.get("severity")
        if severity is not None and severity not in VALID_SEVERITIES:
            raise ValidationError(f"Invalid severity '{severity}'.")

        if bucket.startswith("portfolio.") and bucket != "portfolio.item":
            if payload.get("item_id") in (None, "") and operation not in {"resolve", "invalidate", "archive", "supersede"}:
                raise ValidationError("portfolio child buckets require payload.item_id.")

        if bucket == "system.task_state":
            status = payload.get("status")
            if status not in VALID_TASK_STATUSES:
                raise ValidationError(f"Invalid task state status '{status}'.")

        if bucket == "portfolio.item":
            status = payload.get("status")
            if status is not None and status not in {"watchlist", "active_position", "closed", "rejected", "archived"}:
                raise ValidationError(f"Invalid portfolio item status '{status}'.")

        if bucket.startswith("news.") and operation not in {"dismiss", "archive", "supersede", "stale"}:
            valid_until = payload.get("valid_until")
            if valid_until is not None and not isinstance(valid_until, str):
                raise ValidationError("news valid_until must be an ISO timestamp string when present.")

        if operation == "invalidate" and bucket == "docs.constraint":
            ids = {row["doc_id"] for row in context.active_constraints}
            if write_request.target_id not in ids:
                raise ValidationError(f"Constraint '{write_request.target_id}' is not active.")

        if operation in {"resolve", "invalidate"} and bucket == "system.issue":
            ids = {row["issue_id"] for row in context.open_system_issues}
            if write_request.target_id not in ids:
                raise ValidationError(f"System issue '{write_request.target_id}' is not open.")

        if operation == "invalidate" and bucket == "portfolio.decision":
            ids = {row["note_id"] for row in context.active_portfolio_decisions}
            if write_request.target_id not in ids:
                raise ValidationError(f"Portfolio decision '{write_request.target_id}' is not active.")

        if operation in {"resolve", "invalidate"} and bucket == "portfolio.risk":
            risk_ids = {
                note["note_id"]
                for page in context.active_portfolio_pages
                for note in page.get("notes", [])
                if note.get("note_type") == "risk" and note.get("status") == "active"
            }
            if write_request.target_id not in risk_ids:
                raise ValidationError(f"Portfolio risk '{write_request.target_id}' is not active.")
