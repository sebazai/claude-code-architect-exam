"""
In-memory exam session state.

Lives as long as the MCP server process — sufficient for a single exam session.
The session is reset by start_exam and persists through all subsequent tool calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Question:
    id: str                          # "q1" … "q60"
    scenario_id: int
    scenario_name: str
    domain_id: int
    domain_name: str
    question_number: int
    question: str
    options: dict[str, str]          # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct: str                     # "A" | "B" | "C" | "D"
    explanation: str
    quality_score: int = 0           # 1-5 from quality eval
    delivered_at: datetime | None = None  # when get_next_question returned this Q


@dataclass
class AnswerRecord:
    question_id: str
    question_number: int
    scenario_name: str
    domain_name: str
    selected: str
    correct: str
    is_correct: bool
    explanation: str
    user_seconds: float = 0.0  # seconds from question delivery to answer submission


@dataclass
class ExamSession:
    session_id: str
    selected_scenario_ids: list[int] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    answers: list[AnswerRecord] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    log_entries: list[str] = field(default_factory=list)

    # Accumulated user-active seconds (excludes MCP generation/eval time)
    accumulated_user_seconds: float = 0.0

    # Concepts targeted per domain — used to avoid repetition across questions
    tested_concepts: dict[int, list[str]] = field(default_factory=dict)

    # Pre-generated next question (background prefetch)
    prefetch_task: Any = field(default=None, compare=False, repr=False)
    prefetch_result: dict | None = field(default=None)

    @property
    def total_questions(self) -> int:
        from .exam_content import TOTAL_QUESTIONS
        return TOTAL_QUESTIONS

    @property
    def questions_answered(self) -> int:
        return len(self.answers)

    @property
    def questions_generated(self) -> int:
        return len(self.questions)

    @property
    def correct_count(self) -> int:
        return sum(1 for a in self.answers if a.is_correct)

    @property
    def remaining_seconds(self) -> float:
        from .exam_content import EXAM_DURATION_SECONDS
        return max(0.0, EXAM_DURATION_SECONDS - self.accumulated_user_seconds)

    @property
    def is_time_expired(self) -> bool:
        return self.remaining_seconds <= 0

    def get_question_by_id(self, question_id: str) -> Question | None:
        return next((q for q in self.questions if q.id == question_id), None)

    def record_question_delivered(self, question_id: str) -> None:
        """Mark when a question was delivered to the user (start of user thinking time)."""
        q = self.get_question_by_id(question_id)
        if q:
            q.delivered_at = datetime.now(timezone.utc)

    def record_answer(self, record: AnswerRecord) -> None:
        self.accumulated_user_seconds += record.user_seconds
        self.answers.append(record)

    def record_concept_tested(self, domain_id: int, concept: str) -> None:
        self.tested_concepts.setdefault(domain_id, []).append(concept)

    def log(self, entry: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.log_entries.append(f"[{timestamp}] {entry}")


# ---------------------------------------------------------------------------
# Module-level singleton (single active session)
# ---------------------------------------------------------------------------

_active_session: ExamSession | None = None


def get_session() -> ExamSession | None:
    return _active_session


def set_session(session: ExamSession) -> None:
    global _active_session
    _active_session = session


def reset_session() -> None:
    global _active_session
    _active_session = None
