"""Model-based graders — require an Anthropic async client."""
from __future__ import annotations

import json
import re

import anthropic

META_GRADER_SYSTEM = """\
You are an expert exam quality assessor for a professional certification exam on Claude AI architecture.

Evaluate the multiple-choice question on FIVE dimensions (0–2 points each):
1. scenario_grounding  — References named tools, metrics, or constraints specific to the provided scenario (not generic Claude knowledge)
2. tradeoff_reasoning  — Answering requires weighing design tradeoffs, not recalling a definition
3. distractor_quality  — All 3 wrong answers are plausible to a candidate with incomplete knowledge (no joke answers, no "all of the above")
4. explanation_completeness — States WHY the correct answer is right AND briefly why each wrong answer is wrong
5. single_correct_answer    — Exactly ONE answer is clearly the best; no ties or ambiguous cases

Scoring per dimension: 0 = fails, 1 = partially meets, 2 = fully meets

Total: 0–10. Normalise to 1–5 scale by dividing by 2.

Respond ONLY with this JSON (no markdown, no extra text):
{"score": <1-5 float>, "dimensions": {"scenario_grounding": <0-2>, "tradeoff_reasoning": <0-2>, "distractor_quality": <0-2>, "explanation_completeness": <0-2>, "single_correct_answer": <0-2>}, "critique": "<one sentence identifying the weakest dimension>"}
"""

CALIBRATION_AUDIT_SYSTEM = """\
You are a calibration auditor for an AI quality evaluator used in a certification exam system.

You will receive a multiple-choice exam question and the quality evaluator's assessment of it.
Your job: determine whether the evaluator's score and reasoning are ACCURATE.

Consider:
- Does the evaluator's score match the actual quality of the question?
- Are criteria_met/criteria_failed accurate given the question content?
- Is the feedback specific and actionable (not vague)?

Respond ONLY with this JSON (no markdown):
{"evaluation_is_accurate": <true|false>, "score_seems_correct": <true|false>, "reasoning_quality": "<good|ok|poor>", "issue": "<null or one sentence describing the main problem with the evaluation>"}
"""


def _extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON object found in: {text[:200]}")


async def grade_with_meta_grader(
    client: anthropic.AsyncAnthropic,
    question: dict,
    model: str,
) -> dict:
    """
    Independent dimensional quality assessment using a 5-criterion rubric.
    Does NOT use the built-in quality evaluator prompt — this is a separate grader.
    """
    opts = question.get("options", {})
    prompt = (
        f"Scenario: {question.get('scenario_name', 'Unknown')}\n"
        f"Domain: {question.get('domain_name', 'Unknown')}\n\n"
        f"Question: {question.get('question', '')}\n\n"
        f"A) {opts.get('A', '')}\n"
        f"B) {opts.get('B', '')}\n"
        f"C) {opts.get('C', '')}\n"
        f"D) {opts.get('D', '')}\n\n"
        f"Correct: {question.get('correct', '')}\n"
        f"Explanation: {question.get('explanation', '')}"
    )

    response = await client.messages.create(
        model=model,
        max_tokens=350,
        system=META_GRADER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    try:
        result = _extract_json(text)
        score_raw = result.get("score", 0)
        result["score"] = round(float(score_raw), 2)
        return result
    except Exception as exc:
        return {"score": None, "error": str(exc), "raw": text}


async def audit_quality_evaluation(
    client: anthropic.AsyncAnthropic,
    question: dict,
    eval_result: dict,
    model: str,
) -> dict:
    """
    Meta-audit: assess whether the quality evaluator's score and rationale are accurate.
    Used in the calibration eval to detect systematic over- or under-scoring.
    """
    opts = question.get("options", {})
    prompt = (
        f"=== QUESTION EVALUATED ===\n"
        f"Scenario: {question.get('scenario_name', '')}\n\n"
        f"{question.get('question', '')}\n\n"
        f"A) {opts.get('A', '')}\n"
        f"B) {opts.get('B', '')}\n"
        f"C) {opts.get('C', '')}\n"
        f"D) {opts.get('D', '')}\n\n"
        f"Correct: {question.get('correct', '')}\n\n"
        f"=== EVALUATOR'S ASSESSMENT ===\n"
        f"Score: {eval_result.get('score', 'N/A')} / 5\n"
        f"Feedback: {eval_result.get('feedback', '')}\n"
        f"Criteria met: {eval_result.get('criteria_met', [])}\n"
        f"Criteria failed: {eval_result.get('criteria_failed', [])}"
    )

    response = await client.messages.create(
        model=model,
        max_tokens=200,
        system=CALIBRATION_AUDIT_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    try:
        result = _extract_json(text)
        return result
    except Exception as exc:
        return {"evaluation_is_accurate": None, "error": str(exc), "raw": text}
