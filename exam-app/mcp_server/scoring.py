"""
Scaled scoring: maps raw correct-answer count to a 100–1,000 score.
Passing threshold: 720 (from the official exam guide).
"""
from __future__ import annotations

from .exam_content import (
    DOMAINS,
    PASSING_SCORE,
    SCORE_MAX,
    SCORE_MIN,
    TOTAL_QUESTIONS,
)


def calculate_scaled_score(correct: int, total: int = TOTAL_QUESTIONS) -> int:
    """
    Linear interpolation from SCORE_MIN (0 correct) to SCORE_MAX (all correct).
    Matches the exam's 100–1,000 scaled scoring model.
    """
    if total == 0:
        return SCORE_MIN
    ratio = correct / total
    return round(SCORE_MIN + ratio * (SCORE_MAX - SCORE_MIN))


def is_passing(score: int) -> bool:
    return score >= PASSING_SCORE


def domain_breakdown(answers: list, questions: list) -> list[dict]:
    """
    Returns per-domain accuracy — useful for identifying weak areas.

    Args:
        answers:   list of AnswerRecord objects
        questions: list of Question objects

    Returns:
        List of dicts with domain name, correct count, total count, accuracy %.
    """
    from .session import AnswerRecord, Question

    # Build a lookup from question_id → domain_id
    qid_to_domain: dict[str, int] = {q.id: q.domain_id for q in questions}  # type: ignore[union-attr]

    domain_correct: dict[int, int] = {d: 0 for d in DOMAINS}
    domain_total: dict[int, int] = {d: 0 for d in DOMAINS}

    for a in answers:
        domain_id = qid_to_domain.get(a.question_id)
        if domain_id:
            domain_total[domain_id] += 1
            if a.is_correct:
                domain_correct[domain_id] += 1

    result = []
    for domain_id, domain in DOMAINS.items():
        total = domain_total[domain_id]
        correct = domain_correct[domain_id]
        result.append(
            {
                "domain": domain["name"],
                "correct": correct,
                "total": total,
                "accuracy": f"{round(correct / total * 100) if total else 0}%",
            }
        )
    return result


def format_time(seconds: float) -> str:
    """Convert seconds to MM:SS display string."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"
