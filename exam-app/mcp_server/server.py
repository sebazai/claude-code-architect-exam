"""
Claude Certified Architect – Foundations Exam MCP Server.

Runs inside Claude Code. All LLM inference is delegated back to the Claude Code
host via MCP Sampling (ctx.sample()) — no ANTHROPIC_API_KEY required.

Exam structure:
  - 60 questions · 120 minutes user-active time
  - 4 scenarios randomly selected from 6
  - 15 questions per scenario
  - Score 100–1,000  (passing ≥ 720)

Tool flow:
  start_exam → get_next_question (×60) → submit_answer (×60) → get_results
"""
from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timezone

from mcp.server.fastmcp import Context, FastMCP

from .evals import (
    GENERATION_SYSTEM,
    QUALITY_EVAL_SYSTEM,
    QUALITY_THRESHOLD,
    MAX_RETRIES,
    QualityResult,
    build_generation_prompt,
    build_quality_prompt,
    parse_quality_result,
    parse_question,
)
from .exam_content import (
    DOMAINS,
    SAMPLE_QUESTIONS,
    SCENARIOS,
    SCENARIOS_PER_EXAM,
    TOTAL_QUESTIONS,
    QUESTIONS_PER_SCENARIO,
    get_domain_question_distribution,
)
from .hooks import post_evaluate_hook, post_generate_hook
from .scoring import calculate_scaled_score, domain_breakdown, format_time, is_passing
from .session import AnswerRecord, ExamSession, Question, get_session, reset_session, set_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "claude-architect-exam",
    instructions="""
This MCP server runs the Claude Certified Architect – Foundations practice exam.

EXAM RULES:
• 60 questions across 4 randomly-selected scenarios (15 questions each)
• 120 minutes of user-active time (generation and evaluation time excluded)
• Score 100–1,000; passing score ≥ 720
• Multiple choice: select A, B, C, or D

HOW TO RUN THE EXAM:
1. Call start_exam — initialises a session and reveals the selected scenarios
2. Call get_next_question — generates question 1 (do NOT answer yet; present it to the user)
3. Wait for the user to choose A / B / C / D
4. Call submit_answer with the question_id and their choice
5. Show the correct/incorrect result and explanation to the user
6. Repeat steps 2-5 for all 60 questions
7. Call get_results after the final answer for the final score

IMPORTANT DISPLAY RULES:
• Always show scenario context before the first question of each new scenario
• Show question text and all 4 labelled options clearly
• After submit_answer: show ✓ CORRECT or ✗ INCORRECT, the correct answer, and the full explanation
• Show time remaining (user-active minutes) after each answer
• Do NOT call get_next_question until the user has answered the current question
""",
)

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _select_domain_for_slot(
    slot: int,
    scenario_primary_domains: list[int],
    domain_distribution: list[int],
) -> int:
    """
    Pick a domain for this question slot.
    Prefers the scenario's primary domains; falls back to the weighted distribution.
    """
    slot_domain = domain_distribution[slot % len(domain_distribution)]
    # If the slot domain is in the scenario's primary domains, use it
    if slot_domain in scenario_primary_domains:
        return slot_domain
    # Otherwise use the first primary domain for this scenario
    return scenario_primary_domains[0]


def _get_few_shot_examples(domain_id: int, n: int = 2) -> list[dict]:
    """
    Return up to n sample questions for the target domain.
    Attaches scenario/domain name for prompt rendering.
    """
    matching = [q for q in SAMPLE_QUESTIONS if q["domain_id"] == domain_id]
    if not matching:
        matching = SAMPLE_QUESTIONS  # fallback: any sample
    selected = matching[:n]
    result = []
    for q in selected:
        enriched = dict(q)
        enriched["scenario_name"] = SCENARIOS[q["scenario_id"]]["name"]
        enriched["domain_name"] = DOMAINS[q["domain_id"]]["name"]
        result.append(enriched)
    return result


async def _sample_question(ctx: Context, prompt: str) -> dict:
    """Make a sampling request to generate a question. Returns parsed question dict."""
    result = await ctx.sample(prompt, system_prompt=GENERATION_SYSTEM, max_tokens=1500)
    return parse_question(result.text)


async def _sample_quality(ctx: Context, question: dict) -> QualityResult:
    """Make a sampling request to evaluate question quality."""
    prompt = build_quality_prompt(question)
    result = await ctx.sample(prompt, system_prompt=QUALITY_EVAL_SYSTEM, max_tokens=400)
    return parse_quality_result(result.text)


async def _generate_question_with_retry(
    ctx: Context,
    scenario: dict,
    domain: dict,
    few_shot_examples: list[dict],
) -> tuple[dict, int]:
    """
    Agentic generation loop:
      generate → quality eval → retry-with-feedback if score < threshold
    Returns (question_dict, final_quality_score).
    """
    feedback = ""
    best_question: dict | None = None
    best_score = 0

    for attempt in range(MAX_RETRIES + 1):
        prompt = build_generation_prompt(scenario, domain, few_shot_examples, retry_feedback=feedback)
        try:
            question = await _sample_question(ctx, prompt)
        except ValueError as exc:
            logger.warning("Attempt %d: question parse failed: %s", attempt + 1, exc)
            feedback = f"Parsing failed ({exc}). Ensure the response is valid JSON with the exact structure shown."
            continue

        quality = await _sample_quality(ctx, {**question, "scenario_name": scenario["name"], "domain_name": domain["name"]})

        if quality.score > best_score:
            best_question = question
            best_score = quality.score

        if quality.score >= QUALITY_THRESHOLD:
            return question, quality.score

        # Build retry feedback from the evaluation
        issues = quality.feedback
        if quality.criteria_failed:
            issues += " Failed criteria: " + "; ".join(quality.criteria_failed)
        feedback = issues
        logger.info("Attempt %d quality=%d/5 — retrying: %s", attempt + 1, quality.score, issues)

    # Exhausted retries — return best attempt
    if best_question is None:
        raise RuntimeError("Failed to generate a parseable question after all retries.")
    return best_question, best_score


# ---------------------------------------------------------------------------
# MCP Resources
# ---------------------------------------------------------------------------


@mcp.resource("exam://scenarios")
def resource_all_scenarios() -> str:
    """Overview of all 6 available exam scenarios."""
    return json.dumps(
        [
            {"id": sid, "name": s["name"], "primary_domains": s["primary_domains"]}
            for sid, s in SCENARIOS.items()
        ],
        indent=2,
    )


@mcp.resource("exam://scenario/{scenario_id}")
def resource_scenario(scenario_id: int) -> str:
    """Full description and domain focus for a specific scenario."""
    if scenario_id not in SCENARIOS:
        return json.dumps({"error": f"Scenario {scenario_id} not found."})
    return json.dumps(SCENARIOS[scenario_id], indent=2)


@mcp.resource("exam://domains")
def resource_all_domains() -> str:
    """All domain names and their exam weight."""
    return json.dumps(
        [
            {"id": did, "name": d["name"], "weight_pct": f"{int(d['weight'] * 100)}%"}
            for did, d in DOMAINS.items()
        ],
        indent=2,
    )


@mcp.resource("exam://session/log")
def resource_session_log() -> str:
    """
    Generation and evaluation log for the current session.
    Useful for observing hook activity and quality-eval retries.
    """
    session = get_session()
    if not session:
        return "No active session."
    return "\n".join(session.log_entries) if session.log_entries else "(empty log)"


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def start_exam() -> str:
    """
    Initialize a new exam session.

    Randomly selects 4 of the 6 available scenarios and prepares
    60 question slots (15 per scenario). Returns the exam overview.

    Call this once before get_next_question.
    """
    reset_session()
    session = ExamSession(session_id=f"exam-{random.randint(1000, 9999)}")
    session.selected_scenario_ids = random.sample(list(SCENARIOS.keys()), SCENARIOS_PER_EXAM)
    set_session(session)

    session.log("Exam session started.")
    session.log(f"Selected scenarios: {session.selected_scenario_ids}")

    selected_names = [SCENARIOS[sid]["name"] for sid in session.selected_scenario_ids]

    return json.dumps(
        {
            "session_id": session.session_id,
            "total_questions": TOTAL_QUESTIONS,
            "questions_per_scenario": QUESTIONS_PER_SCENARIO,
            "exam_duration_minutes": 120,
            "passing_score": 720,
            "score_range": "100–1000",
            "selected_scenarios": [
                {"number": i + 1, "name": name}
                for i, name in enumerate(selected_names)
            ],
            "domain_weights": {
                d["name"]: f"{int(d['weight'] * 100)}%"
                for d in DOMAINS.values()
            },
            "note": (
                "Timer runs only while the user is reading/answering questions. "
                "Generation and evaluation time is excluded from the 120-minute limit."
            ),
            "next_step": "Call get_next_question to receive question 1.",
        },
        indent=2,
    )


@mcp.tool()
async def get_next_question(ctx: Context) -> str:
    """
    Generate the next exam question using MCP Sampling.

    Internally runs an agentic quality-eval loop:
      generate → evaluate quality → retry-with-feedback if score < 3

    The user timer is paused while this tool runs.
    Present the returned question and options to the user, then wait for their answer.
    """
    session = get_session()
    if not session:
        return json.dumps({"error": "No active session. Call start_exam first."})

    if session.is_time_expired:
        return json.dumps(
            {
                "error": "Time expired.",
                "message": "Your 120 minutes of active exam time have elapsed. Call get_results.",
            }
        )

    question_number = session.questions_generated + 1
    if question_number > TOTAL_QUESTIONS:
        return json.dumps(
            {"error": "All questions have been generated. Call get_results after answering them."}
        )

    # Determine scenario and domain for this slot
    scenario_idx = (question_number - 1) // QUESTIONS_PER_SCENARIO
    scenario_id = session.selected_scenario_ids[scenario_idx]
    scenario = SCENARIOS[scenario_id]

    slot_within_scenario = (question_number - 1) % QUESTIONS_PER_SCENARIO
    domain_distribution = get_domain_question_distribution(QUESTIONS_PER_SCENARIO)
    domain_id = _select_domain_for_slot(
        slot_within_scenario, scenario["primary_domains"], domain_distribution
    )
    domain = DOMAINS[domain_id]

    few_shot_examples = _get_few_shot_examples(domain_id, n=2)

    session.log(f"Generating Q{question_number}: scenario={scenario_id} domain={domain_id}")

    # Agentic generation + quality-eval loop
    question_data, quality_score = await _generate_question_with_retry(
        ctx, scenario, domain, few_shot_examples
    )

    question_id = f"q{question_number}"
    question = Question(
        id=question_id,
        scenario_id=scenario_id,
        scenario_name=scenario["name"],
        domain_id=domain_id,
        domain_name=domain["name"],
        question_number=question_number,
        question=question_data["question"],
        options=question_data["options"],
        correct=question_data["correct"],
        explanation=question_data["explanation"],
        quality_score=quality_score,
    )

    # PostToolUse hook: validate and log
    post_generate_hook(
        {
            "scenario_id": scenario_id,
            "domain_id": domain_id,
        },
        quality_score,
        session,
    )

    session.questions.append(question)

    # Mark delivery time — user active time begins now
    question.delivered_at = datetime.now(timezone.utc)

    is_first_in_scenario = slot_within_scenario == 0
    remaining_minutes = int(session.remaining_seconds / 60)

    return json.dumps(
        {
            "question_id": question_id,
            "question_number": question_number,
            "total_questions": TOTAL_QUESTIONS,
            "progress": f"{question_number}/{TOTAL_QUESTIONS}",
            "time_remaining": f"{remaining_minutes} minutes",
            "scenario": scenario["name"],
            "scenario_description": scenario["description"] if is_first_in_scenario else None,
            "domain": domain["name"],
            "question": question.question,
            "options": question.options,
            "instructions": "Select A, B, C, or D. Call submit_answer with question_id and your choice.",
        },
        indent=2,
    )


@mcp.tool()
async def submit_answer(question_id: str, answer: str) -> str:
    """
    Submit the user's answer for a question.

    Args:
        question_id: The question_id returned by get_next_question (e.g. "q1").
        answer: The user's choice: A, B, C, or D.

    Returns correct/incorrect verdict, the correct answer, and a full explanation.
    The user's active time for this question is recorded and deducted from the 120-minute budget.
    """
    session = get_session()
    if not session:
        return json.dumps({"error": "No active session. Call start_exam first."})

    answer = answer.upper().strip()
    if answer not in ("A", "B", "C", "D"):
        return json.dumps({"error": "Answer must be A, B, C, or D."})

    question = session.get_question_by_id(question_id)
    if not question:
        return json.dumps({"error": f"Question '{question_id}' not found. Did you call get_next_question?"})

    # Check if already answered
    already_answered = any(a.question_id == question_id for a in session.answers)
    if already_answered:
        return json.dumps({"error": f"Question '{question_id}' has already been answered."})

    # Calculate user-active seconds for this question
    user_seconds = 0.0
    if question.delivered_at:
        elapsed = datetime.now(timezone.utc) - question.delivered_at
        user_seconds = elapsed.total_seconds()

    is_correct = answer == question.correct
    verdict = "✓ CORRECT" if is_correct else "✗ INCORRECT"

    record = AnswerRecord(
        question_id=question_id,
        question_number=question.question_number,
        scenario_name=question.scenario_name,
        domain_name=question.domain_name,
        selected=answer,
        correct=question.correct,
        is_correct=is_correct,
        explanation=question.explanation,
        user_seconds=user_seconds,
    )
    session.record_answer(record)

    # PostToolUse hook: log evaluation result
    post_evaluate_hook(
        question_id=question_id,
        question_number=question.question_number,
        selected=answer,
        is_correct=is_correct,
        user_seconds=user_seconds,
        session=session,
    )

    questions_remaining = TOTAL_QUESTIONS - session.questions_answered
    remaining_minutes = int(session.remaining_seconds / 60)
    running_score = calculate_scaled_score(session.correct_count, session.questions_answered)

    response: dict = {
        "verdict": verdict,
        "question_id": question_id,
        "question_number": question.question_number,
        "your_answer": answer,
        "correct_answer": question.correct,
        "is_correct": is_correct,
        "explanation": question.explanation,
        "running_stats": {
            "correct_so_far": session.correct_count,
            "answered_so_far": session.questions_answered,
            "projected_score": running_score,
        },
        "time_remaining": f"{remaining_minutes} minutes",
        "questions_remaining": questions_remaining,
    }

    if session.is_time_expired:
        response["warning"] = "Time has expired. Call get_results for your final score."
        response["next_step"] = "Call get_results."
    elif questions_remaining > 0:
        response["next_step"] = "Call get_next_question for the next question."
    else:
        response["next_step"] = "All questions answered. Call get_results for your final score."

    return json.dumps(response, indent=2)


@mcp.tool()
async def get_results() -> str:
    """
    Calculate and return the final exam results.

    Returns the scaled score (100–1,000), pass/fail status, per-domain breakdown,
    and a per-question summary so the user can review all their answers.

    Call this after all 60 questions are answered (or when time expires).
    """
    session = get_session()
    if not session:
        return json.dumps({"error": "No active session. Call start_exam first."})

    if session.questions_answered == 0:
        return json.dumps({"error": "No questions answered yet."})

    correct = session.correct_count
    total_answered = session.questions_answered
    score = calculate_scaled_score(correct, TOTAL_QUESTIONS)
    passed = is_passing(score)

    time_used = format_time(session.accumulated_user_seconds)
    time_remaining = format_time(session.remaining_seconds)

    breakdown = domain_breakdown(session.answers, session.questions)

    per_question = [
        {
            "q": a.question_number,
            "scenario": a.scenario_name,
            "domain": a.domain_name,
            "selected": a.selected,
            "correct": a.correct,
            "result": "✓" if a.is_correct else "✗",
        }
        for a in session.answers
    ]

    return json.dumps(
        {
            "result": "PASS ✓" if passed else "FAIL ✗",
            "score": score,
            "passing_score": 720,
            "passed": passed,
            "correct_answers": correct,
            "total_questions": TOTAL_QUESTIONS,
            "questions_answered": total_answered,
            "time_used": time_used,
            "time_remaining": time_remaining,
            "domain_breakdown": breakdown,
            "per_question_summary": per_question,
            "session_log": "Read resource exam://session/log for generation/evaluation activity.",
        },
        indent=2,
    )


@mcp.tool()
async def exam_status() -> str:
    """
    Return the current exam status without advancing the exam.
    Useful for checking progress mid-exam.
    """
    session = get_session()
    if not session:
        return json.dumps({"status": "No active session. Call start_exam to begin."})

    remaining_minutes = int(session.remaining_seconds / 60)
    remaining_seconds_part = int(session.remaining_seconds % 60)

    return json.dumps(
        {
            "session_id": session.session_id,
            "questions_generated": session.questions_generated,
            "questions_answered": session.questions_answered,
            "total_questions": TOTAL_QUESTIONS,
            "correct_so_far": session.correct_count,
            "time_remaining": f"{remaining_minutes}m {remaining_seconds_part}s",
            "time_expired": session.is_time_expired,
            "scenarios": [SCENARIOS[sid]["name"] for sid in session.selected_scenario_ids],
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
