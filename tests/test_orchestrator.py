from __future__ import annotations

import unittest

from financial_model.agents import StaticObservationAgent
from financial_model.config import Settings
from financial_model.deliverables import DeliverableBuilder, DeliverableService
from financial_model.domain.models import AgentObservation, TriggerRequest
from financial_model.memory import FinancialInterpreter, Inputter, PromotionPipeline, Resolver, SharedMemory, SharedMemoryWriter, Validator
from financial_model.orchestration import RunOrchestrator

from tests.fakes import InMemoryRepository


class OrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryRepository()
        self.shared_memory = SharedMemory(self.repository)
        self.pipeline = PromotionPipeline(
            repository=self.repository,
            interpreter=FinancialInterpreter(),
            validator=Validator(),
            inputter=Inputter(self.repository, SharedMemoryWriter(self.repository)),
            shared_memory=self.shared_memory,
            resolver=Resolver(),
            settings=Settings(database_url="postgresql://example"),
        )
        self.deliverable_service = DeliverableService(self.repository, self.shared_memory)
        self.orchestrator = RunOrchestrator(
            repository=self.repository,
            promotion_pipeline=self.pipeline,
            deliverable_service=self.deliverable_service,
            settings=Settings(database_url="postgresql://example"),
        )

    def test_orchestrator_runs_agent_and_promotes_daily_brief_reference(self) -> None:
        agent = StaticObservationAgent(
            name="portfolio_seed_agent",
            role="portfolio_state",
            output_summary="Seeded one portfolio item.",
            observations=[
                AgentObservation(
                    text='{"decision":"accept","bucket":"portfolio.item","target_id":"item_tcs","operation":"upsert","payload":{"name":"Tata Consultancy Services","symbol":"TCS","status":"watchlist"},"rationale":"seed portfolio item"}'
                )
            ],
        )
        builder = DeliverableBuilder(
            name="daily_brief_builder",
            role="deliverable_builder",
            build=lambda context: self.deliverable_service.build_daily_brief(context, title="Desk Brief"),
        )

        result = self.orchestrator.run(
            TriggerRequest(run_type="daily_news_scan"),
            agents=[agent],
            deliverable_builders=[builder],
        )

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(len(self.repository.reports), 1)
        self.assertEqual(len(self.repository.deliverable_refs), 1)
        deliverable_ref = next(iter(self.repository.deliverable_refs.values()))
        self.assertEqual(deliverable_ref["deliverable_type"], "daily_brief")
        self.assertEqual(deliverable_ref["status"], "draft")


if __name__ == "__main__":
    unittest.main()
