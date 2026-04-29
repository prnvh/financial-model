from __future__ import annotations

import re
from datetime import datetime, timezone


SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(text: str, prefix: str | None = None, max_length: int = 64) -> str:
    slug = SLUG_PATTERN.sub("_", text.lower()).strip("_")
    if not slug:
        slug = "item"
    if prefix:
        slug = f"{prefix}_{slug}"
    return slug[:max_length].rstrip("_")
