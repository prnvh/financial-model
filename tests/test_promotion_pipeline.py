from __future__ import annotations

import unittest

from financial_model.config import Settings
from financial_model.domain.models import LedgerEvent
from financial_model.memory import (
    FinancialInterpreter,
    Inputter,
    PromotionPipeline,
    Resolver,
    SharedMemory,
    SharedMemoryWriter,
    Validator,
    WorkingMemory,
)

from tests.fakes import InMemoryRepository


class PromotionPipelineTests(unittest.TestCase):
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
            settings=Settings(
                database_url="postgresql://example",
                max_pending_replay_rounds=3,
                max_pending_replay_items=25,
            ),
        )

    def test_commits_explicit_portfolio_risk_note(self) -> None:
        self.repository.project_portfolio_item(
            LedgerEvent(
                source_agent="seed",
                bucket="portfolio.item",
                target_id="item_tcs",
                operation="upsert",
                payload_json={"name": "Tata Consultancy Services", "symbol": "TCS", "status": "watchlist"},
                event_id="seed",
            )
        )

        run_id = self.repository.create_cron_run("manual", "portfolio_review", {})
        agent_run_id = self.repository.create_agent_run(run_id, "risk_update_agent", "risk", {}, None)
        wm = WorkingMemory(self.repository, run_id, agent_run_id, "risk_update_agent")
        wm.add_note("Risk: TCS has earnings tomorrow, avoid fresh swing entries until the event passes.")

        results = self.pipeline.run(wm)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].decision.value, "accept")
        self.assertEqual(len(self.repository.ledger_events), 1)
        self.assertEqual(len(self.repository.portfolio_notes), 1)
        note = next(iter(self.repository.portfolio_notes.values()))
        self.assertEqual(note["note_type"], "risk")
        self.assertEqual(note["status"], "active")

    def test_pending_issue_resolution_replays_after_issue_commit(self) -> None:
        run_id = self.repository.create_cron_run("manual", "pending_replay", {})
        agent_run_id = self.repository.create_agent_run(run_id, "issue_agent", "issue", {}, None)
        wm = WorkingMemory(self.repository, run_id, agent_run_id, "issue_agent")
        wm.add_note(
            '{"decision":"accept","bucket":"system.issue","target_id":"issue_market_data_outage","operation":"resolve","payload":{},"reference_text":"market data outage","rationale":"resolve existing outage"}'
        )
        first_results = self.pipeline.run(wm)

        self.assertEqual(first_results[0].decision.value, "provisional")
        self.assertEqual(len(self.repository.pending_events), 1)

        agent_run_id_2 = self.repository.create_agent_run(run_id, "issue_agent_2", "issue", {}, None)
        wm2 = WorkingMemory(self.repository, run_id, agent_run_id_2, "issue_agent_2")
        wm2.add_note(
            '{"decision":"accept","bucket":"system.issue","target_id":"issue_market_data_outage","operation":"upsert","payload":{"title":"Market data outage","description":"Blocking price ingestion for the morning session","severity":"high"},"rationale":"create tracked outage"}'
        )
        second_results = self.pipeline.run(wm2)

        self.assertEqual(second_results[0].decision.value, "accept")
        issue = self.repository.system_issues["issue_market_data_outage"]
        self.assertEqual(issue["status"], "resolved")
        pending = next(iter(self.repository.pending_events.values()))
        self.assertEqual(pending.status, "committed")


if __name__ == "__main__":
    unittest.main()
