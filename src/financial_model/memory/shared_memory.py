from __future__ import annotations

from financial_model.domain.models import PendingMemoryEvent, SharedMemoryContext
from financial_model.runtime.protocols import GovernedRepository


class SharedMemory:
    def __init__(self, repository: GovernedRepository):
        self.repository = repository

    def get_context(self) -> SharedMemoryContext:
        return self.repository.get_shared_memory_context()

    def get_active_constraints(self) -> list[dict]:
        return self.get_context().active_constraints

    def get_open_system_issues(self) -> list[dict]:
        return self.get_context().open_system_issues

    def get_active_portfolio_pages(self) -> list[dict]:
        return self.get_context().active_portfolio_pages

    def get_active_portfolio_decisions(self) -> list[dict]:
        return self.get_context().active_portfolio_decisions

    def get_active_news_items(self) -> list[dict]:
        return self.get_context().active_news_items

    def snapshot(self) -> dict:
        return self.get_context().as_dict()
