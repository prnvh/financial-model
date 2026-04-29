from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from financial_model.domain.models import AgentObservation, AgentRunSummary, SharedMemoryContext


class BaseAgent(ABC):
    name: str
    role: str

    @abstractmethod
    def run(self, context: SharedMemoryContext) -> AgentRunSummary:
        raise NotImplementedError


@dataclass(slots=True)
class StaticObservationAgent(BaseAgent):
    name: str
    role: str
    observations: list[AgentObservation]
    output_summary: str

    def run(self, context: SharedMemoryContext) -> AgentRunSummary:
        return AgentRunSummary(
            output_summary=self.output_summary,
            observations=list(self.observations),
        )
