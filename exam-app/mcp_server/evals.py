"""
Prompts and parsers for the exam generation → quality-evaluation loop.

The MCP server invokes Claude via the ``claude`` CLI for each pass (see ``server.py``).

Implements the validation-retry-with-feedback loop described in Domain 4
(Task Statement 4.4: Implement validation, retry, and feedback loops).

Flow:
  1. Generate question via sampling (in server.py)
  2. Call eval_question_quality() → quality score 1-5
  3. If score < QUALITY_THRESHOLD: inject feedback into prompt → retry
  4. Repeat up to MAX_RETRIES times; accept best result after exhaustion
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

QUALITY_THRESHOLD = 3   # Minimum acceptable score (1-5)
MAX_RETRIES = 2         # Max regeneration attempts before accepting best result

# ---------------------------------------------------------------------------
# Quality evaluation prompt
# ---------------------------------------------------------------------------

QUALITY_EVAL_SYSTEM = (
    "You are an expert evaluator for the Claude Certified Architect – Foundations "
    "certification exam. Evaluate exam questions for quality and alignment with the "
    "exam's standards. Respond ONLY with valid JSON — no prose, no markdown fences."
)

QUALITY_EVAL_TEMPLATE = """\
Evaluate this exam question on a scale of 1-5 against the criteria below.

CRITERIA:
1 = Poor: Generic (not tied to scenario), or distractors are obviously wrong
2 = Below average: Vague, or multiple plausible correct answers exist
3 = Acceptable: Scenario-specific, one clear correct answer, plausible distractors
4 = Good: Tests practical judgment; all distractors would fool a candidate with incomplete knowledge
5 = Excellent: Matches sample-question quality — requires tradeoff reasoning; explanation distinguishes correct from each distractor

CHECKLIST (assess each):
- Is the question specific to the provided scenario context (not generic Claude knowledge)?
- Is there exactly ONE clearly correct answer?
- Are all three distractors plausible to someone with incomplete knowledge?
- Does it require practical judgment / tradeoff reasoning (not pure memorization)?
- Is the explanation thorough: explains WHY the correct answer is right AND why each distractor is wrong?

QUESTION TO EVALUATE:
Scenario: {scenario_name}
Domain: {domain_name}

{question}

A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}

Correct: {correct}
Explanation: {explanation}

Respond with ONLY this JSON (no markdown, no extra text):
{{"score": <1-5>, "feedback": "<one-sentence issue summary if score < 4, else 'Meets quality bar'>", "criteria_met": ["..."], "criteria_failed": ["..."]}}
"""

# ---------------------------------------------------------------------------
# Generation prompt
# ---------------------------------------------------------------------------

GENERATION_SYSTEM = (
    "You are generating scenario-based multiple-choice exam questions for the "
    "Claude Certified Architect – Foundations certification. "
    "Questions must require practical judgment about Claude architecture tradeoffs — "
    "not factual recall. Respond ONLY with valid JSON."
)

GENERATION_TEMPLATE = """\
Generate ONE new multiple-choice exam question grounded in the scenario and domain below.

═══ SCENARIO CONTEXT ═══
{scenario_name}

{scenario_description}

═══ TARGET DOMAIN: {domain_name} ═══

Key task statements for this domain:
{task_statements}

Key concepts candidates must understand:
{key_concepts}

Common anti-patterns that distractors should exploit:
{anti_patterns}

═══ STYLE REFERENCE ═══
Study these examples to understand QUESTION STRUCTURE and REASONING DEPTH only.
Do NOT reuse their root causes, correct answers, or anti-patterns.
Your question must test a concept not present in any example below.

{few_shot_examples}
{target_concept_block}{already_tested_block}
═══ REQUIREMENTS ═══
- Ground the question in the scenario above (reference specific tools, metrics, or constraints from it)
- Test practical judgment about a TRADEOFF — not a fact
- Exactly 4 options (A, B, C, D); ONE correct
- Three distractors must be plausible to a candidate with INCOMPLETE knowledge
  (use anti-patterns listed above to craft realistic distractors)
- The question stem must describe a concrete, observable symptom (a metric, log finding, or
  user-visible failure) — not a generic design question
- Each distractor must exploit a DIFFERENT anti-pattern from the list above; name the
  anti-pattern it represents in the explanation
- The explanation must state WHY the correct answer is right AND briefly why each distractor is wrong

Respond with ONLY this JSON (no markdown, no extra text):
{{
  "question": "...",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "correct": "A" | "B" | "C" | "D",
  "explanation": "..."
}}
{retry_feedback}
"""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class QualityResult:
    score: int
    feedback: str
    criteria_met: list[str] = field(default_factory=list)
    criteria_failed: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """
    Robustly extract the first JSON object from a string.
    Handles markdown fences and leading/trailing prose.
    """
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    # Find the first { … } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON object found in sampling response:\n{text[:300]}")


def build_generation_prompt(
    scenario: dict,
    domain: dict,
    few_shot_examples: list[dict],
    retry_feedback: str = "",
    target_concept: str = "",
    already_tested: list[str] | None = None,
) -> str:
    """Construct the full question-generation prompt."""
    examples_text = "\n\n".join(
        f"EXAMPLE {i + 1}:\n"
        f"Scenario: {ex['scenario_name']}\n"
        f"Domain: {ex['domain_name']}\n\n"
        f"{ex['question']}\n\n"
        f"A) {ex['options']['A']}\n"
        f"B) {ex['options']['B']}\n"
        f"C) {ex['options']['C']}\n"
        f"D) {ex['options']['D']}\n\n"
        f"Correct: {ex['correct']}\n"
        f"Explanation: {ex['explanation']}"
        for i, ex in enumerate(few_shot_examples)
    )

    if target_concept:
        target_concept_block = (
            f"\n═══ TARGET CONCEPT ═══\n"
            f"Build your question around this specific concept:\n"
            f"  {target_concept}\n\n"
            f"Your scenario symptom, correct answer, and distractors must all be grounded in this concept.\n"
        )
    else:
        target_concept_block = ""

    if already_tested:
        tested_lines = "\n".join(f"• {c}" for c in already_tested)
        already_tested_block = (
            f"\n═══ DO NOT RE-TEST ═══\n"
            f"These concepts have already been covered in this exam session.\n"
            f"Do NOT test any of them, even indirectly:\n"
            f"{tested_lines}\n"
        )
    else:
        already_tested_block = ""

    feedback_block = ""
    if retry_feedback:
        feedback_block = (
            f"\n\n⚠️  PREVIOUS ATTEMPT WAS REJECTED — please address these issues:\n{retry_feedback}"
        )

    return GENERATION_TEMPLATE.format(
        scenario_name=scenario["name"],
        scenario_description=scenario["description"],
        domain_name=domain["name"],
        task_statements="\n".join(f"• {ts}" for ts in domain["task_statements"]),
        key_concepts="\n".join(f"• {kc}" for kc in domain["key_concepts"]),
        anti_patterns="\n".join(f"• {ap}" for ap in domain.get("anti_patterns", [])),
        few_shot_examples=examples_text,
        target_concept_block=target_concept_block,
        already_tested_block=already_tested_block,
        retry_feedback=feedback_block,
    )


def build_quality_prompt(question: dict) -> str:
    """Construct the quality-evaluation prompt for a generated question."""
    opts = question.get("options", {})
    return QUALITY_EVAL_TEMPLATE.format(
        scenario_name=question.get("scenario_name", ""),
        domain_name=question.get("domain_name", ""),
        question=question.get("question", ""),
        option_a=opts.get("A", ""),
        option_b=opts.get("B", ""),
        option_c=opts.get("C", ""),
        option_d=opts.get("D", ""),
        correct=question.get("correct", ""),
        explanation=question.get("explanation", ""),
    )


def parse_quality_result(text: str) -> QualityResult:
    """Parse sampling response into a QualityResult, with graceful fallback."""
    try:
        data = _extract_json(text)
        return QualityResult(
            score=int(data.get("score", 1)),
            feedback=data.get("feedback", ""),
            criteria_met=data.get("criteria_met", []),
            criteria_failed=data.get("criteria_failed", []),
        )
    except Exception as exc:
        logger.warning("Failed to parse quality result: %s — raw: %s", exc, text[:200])
        return QualityResult(score=1, feedback=f"Parse error: {exc}")


def parse_question(text: str, fallback_correct: str = "A") -> dict:
    """Parse sampling response into a question dict, with graceful fallback."""
    try:
        data = _extract_json(text)
        # Normalise correct to uppercase single letter
        correct = str(data.get("correct", fallback_correct)).strip().upper()
        if correct not in ("A", "B", "C", "D"):
            correct = fallback_correct
        return {
            "question": str(data.get("question", "")),
            "options": {
                "A": str(data.get("options", {}).get("A", "")),
                "B": str(data.get("options", {}).get("B", "")),
                "C": str(data.get("options", {}).get("C", "")),
                "D": str(data.get("options", {}).get("D", "")),
            },
            "correct": correct,
            "explanation": str(data.get("explanation", "")),
        }
    except Exception as exc:
        logger.warning("Failed to parse generated question: %s — raw: %s", exc, text[:200])
        raise ValueError(f"Could not parse generated question: {exc}") from exc
