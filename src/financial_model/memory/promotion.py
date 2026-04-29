from __future__ import annotations

from financial_model.config import Settings
from financial_model.domain.models import PromotionDecision, PromotionResult, ResolutionDecision, WriteDecision
from financial_model.memory.inputter import Inputter
from financial_model.memory.pending_memory import PendingMemoryQueue
from financial_model.memory.shared_memory import SharedMemory
from financial_model.memory.validator import ValidationError, Validator
from financial_model.memory.working_memory import WorkingMemory
from financial_model.runtime.protocols import GovernedRepository, Interpreter


class PromotionPipeline:
    def __init__(
        self,
        repository: GovernedRepository,
        interpreter: Interpreter,
        validator: Validator,
        inputter: Inputter,
        shared_memory: SharedMemory,
        resolver,
        settings: Settings | None = None,
        pending_queue: PendingMemoryQueue | None = None,
    ):
        self.repository = repository
        self.interpreter = interpreter
        self.validator = validator
        self.inputter = inputter
        self.shared_memory = shared_memory
        self.resolver = resolver
        self.settings = settings
        self.pending_queue = pending_queue or PendingMemoryQueue(repository)

    def run(self, working_memory: WorkingMemory, trigger: str = "end_of_step") -> list[PromotionResult]:
        notes = working_memory.get_promotion_candidates()
        results: list[PromotionResult] = []

        for note in notes:
            context = self.shared_memory.get_context()
            result = self._process_note(note, context)
            results.append(result)
            if note.note_id:
                self.repository.mark_note_processed(note.note_id)
            if result.decision == PromotionDecision.ACCEPT:
                self._drain_pending_after_commit(working_memory.source_agent)

        return results

    def retry_pending(self, agent_name: str = "system") -> list[PromotionResult]:
        max_items = self.settings.max_pending_replay_items if self.settings else 25
        results: list[PromotionResult] = []

        for pending in self.pending_queue.get_retryable(limit=max_items):
            context = self.shared_memory.get_context()
            write_request = self.pending_queue.rebuild_write_request(pending)
            try:
                resolved = self.resolver.resolve(write_request, pending.raw_input or "", context)
            except Exception as exc:
                reason = f"retry_resolver_exception:{type(exc).__name__}:{exc}"
                self.pending_queue.mark_on_hold(pending.pending_id or "", reason)
                results.append(PromotionResult(pending.raw_input or "", PromotionDecision.ERROR, reason, bucket=pending.bucket))
                continue

            if resolved.decision == ResolutionDecision.REJECT:
                self.pending_queue.mark_rejected(pending.pending_id or "", resolved.resolution_reason)
                results.append(
                    PromotionResult(
                        pending.raw_input or "",
                        PromotionDecision.REJECT,
                        resolved.resolution_reason,
                        bucket=pending.bucket,
                    )
                )
                continue

            if resolved.decision == ResolutionDecision.PROVISIONAL:
                self.pending_queue.mark_on_hold(pending.pending_id or "", resolved.resolution_reason)
                results.append(
                    PromotionResult(
                        pending.raw_input or "",
                        PromotionDecision.PROVISIONAL,
                        resolved.resolution_reason,
                        event_id=pending.pending_id,
                        bucket=pending.bucket,
                    )
                )
                continue

            try:
                self.validator.validate_resolved(resolved, context)
                event_id = self.inputter.write_resolved(
                    resolved,
                    source_agent=agent_name,
                    raw_input=pending.raw_input or "",
                    write_request=write_request,
                )
            except ValidationError as exc:
                reason = f"retry_validation_error:{exc}"
                self.pending_queue.mark_on_hold(pending.pending_id or "", reason)
                results.append(PromotionResult(pending.raw_input or "", PromotionDecision.INVALID, reason, bucket=pending.bucket))
                continue
            except Exception as exc:
                reason = f"retry_inputter_exception:{type(exc).__name__}:{exc}"
                self.pending_queue.mark_on_hold(pending.pending_id or "", reason)
                results.append(PromotionResult(pending.raw_input or "", PromotionDecision.ERROR, reason, bucket=pending.bucket))
                continue

            self.pending_queue.mark_committed(pending.pending_id or "", event_id, resolved.resolution_reason)
            results.append(
                PromotionResult(
                    pending.raw_input or "",
                    PromotionDecision.ACCEPT,
                    resolved.resolution_reason,
                    event_id=event_id,
                    bucket=resolved.bucket,
                    target_id=resolved.resolved_target_id,
                )
            )

        return results

    def _process_note(self, note, context) -> PromotionResult:
        try:
            write_request = self.interpreter.interpret(note.raw_text, note.source_agent, context)
        except Exception as exc:
            self.repository.create_promotion_attempt(
                note_id=note.note_id or "",
                run_id=note.run_id,
                source_agent=note.source_agent,
                attempt_status="failed",
                error_json={"stage": "interpreter", "error_type": type(exc).__name__, "message": str(exc)},
            )
            return PromotionResult(note.raw_text, PromotionDecision.ERROR, f"interpreter_exception:{exc}")

        if write_request.decision == WriteDecision.REJECT:
            self.repository.create_promotion_attempt(
                note_id=note.note_id or "",
                run_id=note.run_id,
                source_agent=note.source_agent,
                attempt_status="rejected",
                interpreter_decision="reject",
                write_request_json=self._write_request_json(write_request),
            )
            return PromotionResult(note.raw_text, PromotionDecision.REJECT, write_request.rationale)

        try:
            resolved = self.resolver.resolve(write_request, note.raw_text, context)
        except Exception as exc:
            self.repository.create_promotion_attempt(
                note_id=note.note_id or "",
                run_id=note.run_id,
                source_agent=note.source_agent,
                attempt_status="failed",
                interpreter_decision="accept",
                bucket=write_request.bucket,
                operation=write_request.operation,
                target_id=write_request.target_id,
                write_request_json=self._write_request_json(write_request),
                error_json={"stage": "resolver", "error_type": type(exc).__name__, "message": str(exc)},
            )
            return PromotionResult(note.raw_text, PromotionDecision.ERROR, f"resolver_exception:{exc}", bucket=write_request.bucket)

        if resolved.decision == ResolutionDecision.REJECT:
            self.repository.create_promotion_attempt(
                note_id=note.note_id or "",
                run_id=note.run_id,
                source_agent=note.source_agent,
                attempt_status="rejected",
                interpreter_decision="accept",
                resolver_decision="reject",
                bucket=write_request.bucket,
                operation=write_request.operation,
                target_id=write_request.target_id,
                write_request_json=self._write_request_json(write_request),
                resolved_write_json=self._resolved_write_json(resolved),
            )
            return PromotionResult(note.raw_text, PromotionDecision.REJECT, resolved.resolution_reason, bucket=write_request.bucket)

        if resolved.decision == ResolutionDecision.PROVISIONAL:
            pending_id = self.inputter.write_provisional(resolved, note.source_agent, note.raw_text, write_request)
            self.repository.create_promotion_attempt(
                note_id=note.note_id or "",
                run_id=note.run_id,
                source_agent=note.source_agent,
                attempt_status="provisional",
                interpreter_decision="accept",
                resolver_decision="provisional",
                bucket=resolved.bucket,
                operation=resolved.operation,
                target_id=write_request.target_id,
                write_request_json=self._write_request_json(write_request),
                resolved_write_json=self._resolved_write_json(resolved),
            )
            return PromotionResult(
                note.raw_text,
                PromotionDecision.PROVISIONAL,
                resolved.resolution_reason,
                event_id=pending_id,
                bucket=resolved.bucket,
            )

        try:
            self.validator.validate_resolved(resolved, context)
        except ValidationError as exc:
            self.repository.create_promotion_attempt(
                note_id=note.note_id or "",
                run_id=note.run_id,
                source_agent=note.source_agent,
                attempt_status="failed",
                interpreter_decision="accept",
                resolver_decision="commit",
                validator_decision="fail",
                bucket=resolved.bucket,
                operation=resolved.operation,
                target_id=resolved.resolved_target_id,
                write_request_json=self._write_request_json(write_request),
                resolved_write_json=self._resolved_write_json(resolved),
                validator_errors_json={"message": str(exc)},
            )
            return PromotionResult(note.raw_text, PromotionDecision.INVALID, f"validation_error:{exc}", bucket=resolved.bucket)

        event_id = self.inputter.write_resolved(
            resolved,
            source_agent=note.source_agent,
            raw_input=note.raw_text,
            write_request=write_request,
        )
        self.repository.create_promotion_attempt(
            note_id=note.note_id or "",
            run_id=note.run_id,
            source_agent=note.source_agent,
            attempt_status="committed",
            interpreter_decision="accept",
            resolver_decision="commit",
            validator_decision="pass",
            bucket=resolved.bucket,
            operation=resolved.operation,
            target_id=resolved.resolved_target_id,
            write_request_json=self._write_request_json(write_request),
            resolved_write_json=self._resolved_write_json(resolved),
        )
        return PromotionResult(
            note.raw_text,
            PromotionDecision.ACCEPT,
            resolved.resolution_reason,
            event_id=event_id,
            bucket=resolved.bucket,
            target_id=resolved.resolved_target_id,
        )

    def _drain_pending_after_commit(self, agent_name: str) -> None:
        max_rounds = self.settings.max_pending_replay_rounds if self.settings else 3
        for _ in range(max_rounds):
            results = self.retry_pending(agent_name)
            if not any(result.decision == PromotionDecision.ACCEPT for result in results):
                break

    def _write_request_json(self, write_request) -> dict:
        return {
            "decision": write_request.decision.value,
            "rationale": write_request.rationale,
            "bucket": write_request.bucket,
            "target_id": write_request.target_id,
            "operation": write_request.operation,
            "payload": write_request.payload,
            "reference_text": write_request.reference_text,
            "candidate_aliases": list(write_request.candidate_aliases or []),
            "confidence": write_request.confidence,
        }

    def _resolved_write_json(self, resolved) -> dict:
        return {
            "decision": resolved.decision.value,
            "resolution_reason": resolved.resolution_reason,
            "bucket": resolved.bucket,
            "operation": resolved.operation,
            "resolved_target_id": resolved.resolved_target_id,
            "matched_target_id": resolved.matched_target_id,
            "payload": resolved.payload,
            "reference_text": resolved.reference_text,
            "candidate_matches": list(resolved.candidate_matches),
        }
