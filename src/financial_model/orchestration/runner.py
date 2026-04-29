from __future__ import annotations

from dataclasses import dataclass, field

from financial_model.config import Settings
from financial_model.deliverables.service import DeliverableBuilder, DeliverableService
from financial_model.domain.models import NoteType, PromotionResult, RunStatus, TriggerRequest
from financial_model.memory.promotion import PromotionPipeline
from financial_model.memory.working_memory import WorkingMemory
from financial_model.runtime.protocols import Agent, GovernedRepository


@dataclass(slots=True)
class AgentExecution:
    agent_name: str
    agent_run_id: str
    output_summary: str
    promotion_results: list[PromotionResult] = field(default_factory=list)
    generated_report_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RunExecutionResult:
    run_id: str
    status: str
    agent_executions: list[AgentExecution] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class RunOrchestrator:
    def __init__(
        self,
        repository: GovernedRepository,
        promotion_pipeline: PromotionPipeline,
        deliverable_service: DeliverableService | None = None,
        settings: Settings | None = None,
    ):
        self.repository = repository
        self.promotion_pipeline = promotion_pipeline
        self.deliverable_service = deliverable_service
        self.settings = settings

    def run(
        self,
        trigger_request: TriggerRequest,
        agents: list[Agent],
        deliverable_builders: list[DeliverableBuilder] | None = None,
    ) -> RunExecutionResult:
        run_id = self.repository.create_cron_run(
            trigger_type=trigger_request.trigger_type.value,
            run_type=trigger_request.run_type,
            config_json=trigger_request.config_json,
        )
        self.repository.update_cron_run_status(run_id, RunStatus.RUNNING.value)
        self.repository.create_snapshot(run_id, "pre_run", self.promotion_pipeline.shared_memory.snapshot())

        executions: list[AgentExecution] = []
        errors: list[str] = []

        try:
            max_agents = self.settings.max_agents_per_run if self.settings else len(agents)
            for agent in agents[:max_agents]:
                execution = self._run_agent(run_id, agent)
                executions.append(execution)

            for builder in deliverable_builders or []:
                execution = self._run_deliverable_builder(run_id, builder)
                executions.append(execution)
        except Exception as exc:
            errors.append(f"run_exception:{type(exc).__name__}:{exc}")
            self.repository.update_cron_run_status(
                run_id,
                RunStatus.FAILED.value,
                error_json={"errors": errors},
            )
            raise

        final_status = RunStatus.SUCCEEDED.value if not errors else RunStatus.FAILED.value
        self.repository.create_snapshot(run_id, "post_run", self.promotion_pipeline.shared_memory.snapshot())
        self.repository.update_cron_run_status(
            run_id,
            final_status,
            error_json={"errors": errors} if errors else None,
        )
        return RunExecutionResult(run_id=run_id, status=final_status, agent_executions=executions, errors=errors)

    def _run_agent(self, run_id: str, agent: Agent) -> AgentExecution:
        context = self.promotion_pipeline.shared_memory.get_context()
        agent_run_id = self.repository.create_agent_run(
            run_id=run_id,
            agent_name=agent.name,
            agent_role=agent.role,
            input_context_json=context.as_dict(),
        )
        self.repository.update_agent_run(agent_run_id, "running")
        working_memory = WorkingMemory(self.repository, run_id, agent_run_id, agent.name)

        try:
            summary = agent.run(context)
            for observation in summary.observations:
                self.repository.record_raw_agent_event(
                    run_id=run_id,
                    agent_run_id=agent_run_id,
                    source_type=observation.source_type,
                    source_name=agent.name,
                    event_type=observation.event_type,
                    raw_text=observation.text,
                    payload_json=observation.payload_json,
                    entity_type=observation.entity_type,
                    entity_id=observation.entity_id,
                    confidence=observation.confidence,
                    evidence_refs_json=[
                        {
                            "source_type": ref.source_type,
                            "source_name": ref.source_name,
                            "locator": ref.locator,
                            "metadata": ref.metadata,
                        }
                        for ref in observation.evidence_refs
                    ],
                )
                note_type = NoteType.TOOL_RESULT if observation.source_type == "tool" else NoteType.AGENT
                working_memory.add_note(observation.text, note_type)

            for note in summary.working_notes:
                working_memory.add_note(note.raw_text, note.note_type, note.source_ref)

            promotion_results = self.promotion_pipeline.run(working_memory, trigger="agent_run")
            self.repository.update_agent_run(
                agent_run_id,
                "succeeded",
                output_summary=summary.output_summary,
                token_usage_json=summary.token_usage_json,
                cost_estimate=summary.cost_estimate,
            )
            return AgentExecution(
                agent_name=agent.name,
                agent_run_id=agent_run_id,
                output_summary=summary.output_summary,
                promotion_results=promotion_results,
            )
        except Exception as exc:
            self.repository.update_agent_run(
                agent_run_id,
                "failed",
                error_json={"error_type": type(exc).__name__, "message": str(exc)},
            )
            raise

    def _run_deliverable_builder(self, run_id: str, builder: DeliverableBuilder) -> AgentExecution:
        if self.deliverable_service is None:
            raise ValueError("Deliverable builders require a DeliverableService.")

        context = self.promotion_pipeline.shared_memory.get_context()
        agent_run_id = self.repository.create_agent_run(
            run_id=run_id,
            agent_name=builder.name,
            agent_role=builder.role,
            input_context_json=context.as_dict(),
        )
        self.repository.update_agent_run(agent_run_id, "running")
        working_memory = WorkingMemory(self.repository, run_id, agent_run_id, builder.name)

        try:
            draft = builder.build(context)
            report_id, _snapshot_id, reference_note = self.deliverable_service.persist_draft(
                draft,
                run_id=run_id,
                generated_by_agent_run_id=agent_run_id,
            )
            working_memory.add_note(reference_note, NoteType.SYSTEM, source_ref=f"report:{report_id}")
            promotion_results = self.promotion_pipeline.run(working_memory, trigger="deliverable_generation")
            self.repository.update_agent_run(
                agent_run_id,
                "succeeded",
                output_summary=f"Generated {draft.deliverable_type}: {draft.title}",
            )
            return AgentExecution(
                agent_name=builder.name,
                agent_run_id=agent_run_id,
                output_summary=f"Generated {draft.deliverable_type}: {draft.title}",
                promotion_results=promotion_results,
                generated_report_ids=[report_id],
            )
        except Exception as exc:
            self.repository.update_agent_run(
                agent_run_id,
                "failed",
                error_json={"error_type": type(exc).__name__, "message": str(exc)},
            )
            raise
