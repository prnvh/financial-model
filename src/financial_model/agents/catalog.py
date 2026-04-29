from __future__ import annotations

from collections import defaultdict

from financial_model.runtime.protocols import Agent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents_by_run_type: dict[str, list[Agent]] = defaultdict(list)

    def register(self, run_type: str, agent: Agent) -> None:
        self._agents_by_run_type[run_type].append(agent)

    def get_agents(self, run_type: str) -> list[Agent]:
        return list(self._agents_by_run_type.get(run_type, []))
