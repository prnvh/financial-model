from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BucketSpec:
    name: str
    allowed_operations: tuple[str, ...]
    required_fields: tuple[str, ...]
    projection_target: str


BUCKET_SPECS: dict[str, BucketSpec] = {
    "docs.doc": BucketSpec("docs.doc", ("upsert", "archive"), ("title",), "sml.docs"),
    "docs.strategy": BucketSpec("docs.strategy", ("upsert", "supersede", "archive"), ("title",), "sml.docs"),
    "docs.thesis": BucketSpec("docs.thesis", ("upsert", "supersede", "archive"), ("title",), "sml.docs"),
    "docs.learning": BucketSpec("docs.learning", ("append", "archive"), ("title", "statement"), "sml.docs"),
    "docs.constraint": BucketSpec("docs.constraint", ("upsert", "invalidate", "archive"), ("title", "statement"), "sml.docs"),
    "portfolio.item": BucketSpec("portfolio.item", ("upsert", "archive"), ("name", "status"), "sml.portfolio_items"),
    "portfolio.note": BucketSpec("portfolio.note", ("append", "resolve", "supersede", "archive"), ("item_id", "title"), "sml.portfolio_item_notes"),
    "portfolio.risk": BucketSpec("portfolio.risk", ("upsert", "resolve", "invalidate", "archive"), ("item_id", "title", "severity", "description"), "sml.portfolio_item_notes"),
    "portfolio.entry_plan": BucketSpec("portfolio.entry_plan", ("upsert", "supersede", "archive"), ("item_id", "title", "description"), "sml.portfolio_item_notes"),
    "portfolio.exit_plan": BucketSpec("portfolio.exit_plan", ("upsert", "supersede", "archive"), ("item_id", "title", "description"), "sml.portfolio_item_notes"),
    "portfolio.learning": BucketSpec("portfolio.learning", ("append", "archive"), ("item_id", "title", "statement"), "sml.portfolio_item_notes"),
    "portfolio.decision": BucketSpec("portfolio.decision", ("append", "invalidate", "archive"), ("item_id", "title", "statement"), "sml.portfolio_item_notes"),
    "portfolio.result": BucketSpec("portfolio.result", ("append", "archive"), ("item_id", "title", "result"), "sml.portfolio_item_notes"),
    "news.item": BucketSpec("news.item", ("upsert", "dismiss", "archive", "supersede", "stale"), ("title", "summary"), "sml.news_items"),
    "news.market_event": BucketSpec("news.market_event", ("upsert", "dismiss", "archive", "supersede", "stale"), ("title", "summary"), "sml.news_items"),
    "news.researched_item": BucketSpec("news.researched_item", ("upsert", "dismiss", "archive", "supersede", "stale"), ("title", "summary", "researched_summary"), "sml.news_items"),
    "deliverables.ref": BucketSpec("deliverables.ref", ("upsert", "finalize", "supersede", "reject", "archive"), ("title", "deliverable_type"), "sml.deliverable_refs"),
    "system.task_state": BucketSpec("system.task_state", ("upsert",), ("status",), "sml.task_states"),
    "system.issue": BucketSpec("system.issue", ("upsert", "resolve", "invalidate", "archive"), ("title",), "sml.system_issues"),
}


def get_bucket_spec(bucket: str) -> BucketSpec:
    try:
        return BUCKET_SPECS[bucket]
    except KeyError as exc:
        raise KeyError(f"Unknown bucket '{bucket}'.") from exc
