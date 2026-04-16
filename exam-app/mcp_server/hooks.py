"""
Post-sampling hooks.

These mirror the Agent SDK's PostToolUse hook pattern: they intercept after
a sampling result is returned, before the data is passed back to the caller.
They are called explicitly within tool handlers (not at the MCP framework level).
"""
from __future__ import annotations

import logging

from .session import ExamSession

logger = logging.getLogger(__name__)


def post_generate_hook(question: dict, quality_score: int, session: ExamSession) -> None:
    """
    Called after a question has been generated and quality-evaluated.

    Mirrors PostToolUse: intercepts after the sampling call completes,
    validates/logs the result before it is appended to the session.

    Logs:
      - question number, scenario, domain, quality score
      - whether quality threshold was met or a retry was triggered
    """
    q_num = len(session.questions) + 1
    entry = (
        f"[GENERATE] Q{q_num} "
        f"scenario={question.get('scenario_id', '?')} "
        f"domain={question.get('domain_id', '?')} "
        f"quality={quality_score}/5"
    )
    session.log(entry)
    logger.info(entry)

    if quality_score < 3:
        warn = f"[GENERATE] Q{q_num} quality below threshold ({quality_score}/5) — retry was triggered"
        session.log(warn)
        logger.warning(warn)


def post_evaluate_hook(
    question_id: str,
    question_number: int,
    selected: str,
    is_correct: bool,
    user_seconds: float,
    session: ExamSession,
) -> None:
    """
    Called after an answer has been evaluated.

    Logs the result for downstream analysis of answer patterns and timing.
    """
    result_str = "CORRECT" if is_correct else "INCORRECT"
    entry = (
        f"[EVALUATE] Q{question_number} ({question_id}) "
        f"selected={selected} → {result_str} "
        f"user_time={user_seconds:.1f}s"
    )
    session.log(entry)
    logger.info(entry)
