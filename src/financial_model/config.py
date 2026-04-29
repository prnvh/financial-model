from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    database_url: str
    openai_api_key: str | None = None
    default_model_name: str = "gpt-4.1"
    max_pending_replay_rounds: int = 3
    max_pending_replay_items: int = 25
    max_agents_per_run: int = 10
    max_documents_per_day: int = 25
    max_reports_per_day: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.environ.get("DATABASE_URL", "").strip()
        if not database_url:
            raise ValueError("DATABASE_URL is required to construct Settings.")

        return cls(
            database_url=database_url,
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            default_model_name=os.environ.get("FINANCIAL_MODEL_NAME", "gpt-4.1"),
            max_pending_replay_rounds=int(os.environ.get("MAX_PENDING_REPLAY_ROUNDS", "3")),
            max_pending_replay_items=int(os.environ.get("MAX_PENDING_REPLAY_ITEMS", "25")),
            max_agents_per_run=int(os.environ.get("MAX_AGENTS_PER_RUN", "10")),
            max_documents_per_day=int(os.environ.get("MAX_DOCUMENTS_PER_DAY", "25")),
            max_reports_per_day=int(os.environ.get("MAX_REPORTS_PER_DAY", "5")),
        )
