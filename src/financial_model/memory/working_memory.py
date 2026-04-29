from __future__ import annotations

from financial_model.domain.models import NoteType, WorkingMemoryNote
from financial_model.runtime.protocols import GovernedRepository


class WorkingMemory:
    def __init__(self, repository: GovernedRepository, run_id: str, agent_run_id: str, source_agent: str):
        self.repository = repository
        self.run_id = run_id
        self.agent_run_id = agent_run_id
        self.source_agent = source_agent

    def add_note(self, text: str, note_type: NoteType = NoteType.AGENT, source_ref: str | None = None) -> WorkingMemoryNote:
        note = WorkingMemoryNote(
            run_id=self.run_id,
            agent_run_id=self.agent_run_id,
            source_agent=self.source_agent,
            note_type=note_type,
            raw_text=text,
            source_ref=source_ref,
        )
        return self.repository.add_working_memory_note(note)

    def add_tool_result_note(self, tool_name: str, result_summary: str, source_ref: str | None = None) -> WorkingMemoryNote:
        return self.add_note(
            text=f"[tool:{tool_name}] {result_summary}",
            note_type=NoteType.TOOL_RESULT,
            source_ref=source_ref,
        )

    def get_promotion_candidates(self) -> list[WorkingMemoryNote]:
        return self.repository.list_unprocessed_notes(self.run_id, self.agent_run_id)

    def mark_promoted(self, notes: list[WorkingMemoryNote]) -> None:
        for note in notes:
            if note.note_id:
                self.repository.mark_note_processed(note.note_id)
