"""
Evals MCP Server — runs inside Claude Code, no ANTHROPIC_API_KEY required.

All LLM inference is delegated to the Claude Code host via MCP Sampling
(ctx.sample()). The exam server uses the claude CLI instead; this server uses sampling.

Available tools:
  list_eval_variants     — show the 3 prompt variants and their descriptions
  run_generation_eval    — test a prompt variant on N generation cases
  run_calibration_eval   — test quality evaluator accuracy on 15 pre-labeled questions
  run_full_eval          — run both evals for all (or selected) variants
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP

# Datasets live alongside this package in the source tree (editable install)
_EVALS_ROOT = Path(__file__).parent.parent

from mcp_server.evals import (  # noqa: E402 (exam-app)
    QUALITY_EVAL_SYSTEM,
    build_quality_prompt,
    parse_quality_result,
    parse_question,
)
from mcp_server.exam_content import DOMAINS, SAMPLE_QUESTIONS, SCENARIOS  # noqa: E402

from graders.code_grader import (  # noqa: E402 (evals)
    grade_generation,
    grade_keyword_grounding,
    grade_quality_eval_output,
    summarize_calibration_results,
    summarize_generation_results,
)
from prompts.variants import PROMPT_VARIANTS  # noqa: E402

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DATASETS_DIR = _EVALS_ROOT / "datasets"

app = FastMCP("claude-architect-evals")

# ---------------------------------------------------------------------------
# Shared sampling helpers
# ---------------------------------------------------------------------------

META_GRADER_SYSTEM = """\
You are an expert exam quality assessor for a professional certification exam on Claude AI architecture.

Evaluate the multiple-choice question on FIVE dimensions (0–2 points each):
1. scenario_grounding  — References named tools, metrics, or constraints specific to the provided scenario
2. tradeoff_reasoning  — Answering requires weighing design tradeoffs, not recalling a definition
3. distractor_quality  — All 3 wrong answers are plausible to a candidate with incomplete knowledge
4. explanation_completeness — States WHY the correct answer is right AND why each wrong answer is wrong
5. single_correct_answer    — Exactly ONE answer is clearly the best

Scoring per dimension: 0 = fails, 1 = partially meets, 2 = fully meets. Total: 0–10. Normalise to 1–5 (total / 2).

Respond ONLY with this JSON (no markdown, no extra text):
{"score": <1-5 float>, "dimensions": {"scenario_grounding": 0-2, "tradeoff_reasoning": 0-2, "distractor_quality": 0-2, "explanation_completeness": 0-2, "single_correct_answer": 0-2}, "critique": "<one sentence>"}
"""

CALIBRATION_AUDIT_SYSTEM = """\
You are a calibration auditor for an AI quality evaluator used in a certification exam system.

Given a multiple-choice question and the quality evaluator's assessment of it, determine if the score and reasoning are ACCURATE.

Consider: Does the score match the actual quality? Are criteria_met/criteria_failed accurate? Is feedback specific?

Respond ONLY with this JSON:
{"evaluation_is_accurate": <true|false>, "score_seems_correct": <true|false>, "reasoning_quality": "<good|ok|poor>", "issue": "<null or one sentence>"}
"""


def _get_few_shot_examples(domain_id: int, n: int = 2) -> list[dict]:
    matching = [q for q in SAMPLE_QUESTIONS if q["domain_id"] == domain_id]
    selected = matching[:n]
    return [
        {**q, "scenario_name": SCENARIOS[q["scenario_id"]]["name"], "domain_name": DOMAINS[q["domain_id"]]["name"]}
        for q in selected
    ]


import re

from mcp import types as mcp_types


def _strip_thinking(text: str) -> str:
    return re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL).strip()


def _make_message(prompt: str) -> list[mcp_types.SamplingMessage]:
    return [mcp_types.SamplingMessage(
        role="user",
        content=mcp_types.TextContent(type="text", text=prompt),
    )]


def _result_text(result: mcp_types.CreateMessageResult) -> str:
    content = result.content
    if hasattr(content, "text"):
        return content.text
    return str(content)


async def _sample_generation(ctx: Context, prompt: str, system: str) -> tuple[dict | None, str]:
    result = await ctx.session.create_message(_make_message(prompt), system_prompt=system, max_tokens=1500)
    raw = _result_text(result)
    cleaned = _strip_thinking(raw)
    try:
        return parse_question(cleaned), raw
    except Exception as exc:
        log.warning("Question parse error: %s", exc)
        return None, raw


async def _sample_quality_eval(ctx: Context, question: dict) -> dict:
    prompt = build_quality_prompt(question)
    result = await ctx.session.create_message(_make_message(prompt), system_prompt=QUALITY_EVAL_SYSTEM, max_tokens=400)
    r = parse_quality_result(_result_text(result))
    return {"score": r.score, "feedback": r.feedback, "criteria_met": r.criteria_met, "criteria_failed": r.criteria_failed}


async def _sample_meta_grade(ctx: Context, question: dict) -> dict:
    opts = question.get("options", {})
    prompt = (
        f"Scenario: {question.get('scenario_name', 'Unknown')}\n"
        f"Domain: {question.get('domain_name', 'Unknown')}\n\n"
        f"Question: {question.get('question', '')}\n\n"
        f"A) {opts.get('A', '')}\nB) {opts.get('B', '')}\n"
        f"C) {opts.get('C', '')}\nD) {opts.get('D', '')}\n\n"
        f"Correct: {question.get('correct', '')}\n"
        f"Explanation: {question.get('explanation', '')}"
    )
    result = await ctx.session.create_message(_make_message(prompt), system_prompt=META_GRADER_SYSTEM, max_tokens=350)
    try:
        import json as _json
        text = re.sub(r"```(?:json)?\s*", "", _result_text(result)).strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        data = _json.loads(match.group()) if match else {}
        data["score"] = round(float(data.get("score", 0)), 2)
        return data
    except Exception as exc:
        return {"score": None, "error": str(exc)}


async def _sample_audit(ctx: Context, question: dict, eval_result: dict) -> dict:
    opts = question.get("options", {})
    prompt = (
        f"=== QUESTION ===\nScenario: {question.get('scenario_name', '')}\n\n"
        f"{question.get('question', '')}\n\n"
        f"A) {opts.get('A', '')}\nB) {opts.get('B', '')}\n"
        f"C) {opts.get('C', '')}\nD) {opts.get('D', '')}\n\n"
        f"Correct: {question.get('correct', '')}\n\n"
        f"=== EVALUATOR ASSESSMENT ===\n"
        f"Score: {eval_result.get('score', 'N/A')}/5\n"
        f"Feedback: {eval_result.get('feedback', '')}\n"
        f"Criteria met: {eval_result.get('criteria_met', [])}\n"
        f"Criteria failed: {eval_result.get('criteria_failed', [])}"
    )
    result = await ctx.session.create_message(_make_message(prompt), system_prompt=CALIBRATION_AUDIT_SYSTEM, max_tokens=200)
    try:
        import json as _json
        text = re.sub(r"```(?:json)?\s*", "", _result_text(result)).strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return _json.loads(match.group()) if match else {}
    except Exception as exc:
        return {"evaluation_is_accurate": None, "error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: list_eval_variants
# ---------------------------------------------------------------------------

@app.tool()
async def list_eval_variants(ctx: Context) -> str:
    """List available prompt variants for the generation eval."""
    variants = {
        key: {"name": v["name"], "description": v["description"]}
        for key, v in PROMPT_VARIANTS.items()
    }
    return json.dumps(variants, indent=2)


# ---------------------------------------------------------------------------
# Tool: run_generation_eval
# ---------------------------------------------------------------------------

@app.tool()
async def run_generation_eval(
    ctx: Context,
    variant: str = "v1",
    n_cases: int = 3,
    include_meta_grade: bool = True,
) -> str:
    """
    Run the generation eval for one prompt variant using MCP sampling.

    Generates questions for N test cases, then grades each with:
    - Code grader: structural validity + keyword grounding
    - Quality evaluator: built-in 1-5 rubric (via sampling)
    - Meta-grader: independent 5-dimension rubric (via sampling, optional)

    Args:
        variant: Prompt variant key — 'v1' (baseline), 'v2' (anti-generic), or 'v3' (chain-of-thought)
        n_cases: Number of generation test cases to run (1–10, default 3)
        include_meta_grade: Whether to run the independent meta-grader (default True)

    Returns JSON with per-case results and aggregate summary.
    """
    if variant not in PROMPT_VARIANTS:
        return json.dumps({"error": f"Unknown variant '{variant}'. Valid: {list(PROMPT_VARIANTS)}"})

    n_cases = max(1, min(10, n_cases))
    gen_cases = json.loads((DATASETS_DIR / "generation_cases.json").read_text())[:n_cases]
    v = PROMPT_VARIANTS[variant]

    log.info("Generation eval: variant=%s n=%d meta=%s", variant, n_cases, include_meta_grade)

    results = []
    for case in gen_cases:
        scenario = SCENARIOS[case["scenario_id"]]
        domain = DOMAINS[case["domain_id"]]
        few_shot = _get_few_shot_examples(case["domain_id"])

        prompt = v["build_prompt"](scenario, domain, few_shot)
        question, raw = await _sample_generation(ctx, prompt, v["system"])

        entry: dict = {
            "case_id": case["id"],
            "scenario": scenario["name"],
            "domain": domain["name"],
            "generation_success": question is not None,
        }

        if question is None:
            entry["code_grade"] = {"overall_pass": False, "error": "parse_failure"}
            entry["keyword_grade"] = {"passes_grounding": False}
            entry["quality_eval"] = {"score": None}
            entry["meta_grade"] = {"score": None}
            results.append(entry)
            continue

        question["scenario_name"] = scenario["name"]
        question["domain_name"] = domain["name"]
        entry["question"] = question

        # Code grading (sync)
        entry["code_grade"] = grade_generation(question)
        all_opts = " ".join(question.get("options", {}).values())
        entry["keyword_grade"] = grade_keyword_grounding(
            question.get("question", ""), all_opts, case.get("scenario_keywords", [])
        )

        # Quality eval via sampling
        entry["quality_eval"] = await _sample_quality_eval(ctx, question)

        # Meta-grade via sampling (optional)
        if include_meta_grade:
            entry["meta_grade"] = await _sample_meta_grade(ctx, question)
        else:
            entry["meta_grade"] = {"score": None, "skipped": True}

        results.append(entry)

    return json.dumps({
        "variant": variant,
        "variant_name": v["name"],
        "variant_description": v["description"],
        "cases": results,
        "summary": summarize_generation_results(results),
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool: run_calibration_eval
# ---------------------------------------------------------------------------

@app.tool()
async def run_calibration_eval(
    ctx: Context,
    include_audit: bool = True,
) -> str:
    """
    Run the quality evaluator calibration eval using MCP sampling.

    Tests 15 pre-labeled questions (5 good, 5 mediocre, 5 bad) through the
    quality evaluator, then checks whether scores land in the expected range.
    Optionally runs a meta-audit of each evaluation's accuracy.

    Args:
        include_audit: Whether to run the meta-audit grader (default True)

    Returns JSON with per-case results, accuracy by label, and overall accuracy.
    """
    cal_cases = json.loads((DATASETS_DIR / "quality_calibration.json").read_text())
    log.info("Calibration eval: n=%d audit=%s", len(cal_cases), include_audit)

    results = []
    for case in cal_cases:
        question = {
            "scenario_name": case["scenario_name"],
            "domain_name": case["domain_name"],
            "question": case["question"],
            "options": case["options"],
            "correct": case["correct"],
            "explanation": case.get("explanation", ""),
        }
        expected_range = tuple(case["expected_score_range"])

        quality_result = await _sample_quality_eval(ctx, question)
        code_grade = grade_quality_eval_output(quality_result, expected_range)

        entry: dict = {
            "case_id": case["id"],
            "label": case["label"],
            "expected_score_range": list(expected_range),
            "quality_eval": quality_result,
            "code_grade": code_grade,
        }

        if include_audit:
            entry["audit"] = await _sample_audit(ctx, question, quality_result)

        results.append(entry)

    return json.dumps({
        "cases": results,
        "summary": summarize_calibration_results(results),
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool: run_full_eval
# ---------------------------------------------------------------------------

@app.tool()
async def run_full_eval(
    ctx: Context,
    variants: str = "v1,v2,v3",
    n_gen: int = 3,
    include_meta_grade: bool = True,
    include_audit: bool = True,
) -> str:
    """
    Run the complete eval pipeline: generation eval for all variants + calibration eval.

    This combines run_generation_eval (for each variant) and run_calibration_eval
    into a single report for side-by-side prompt comparison.

    Args:
        variants: Comma-separated variant keys, e.g. 'v1,v2,v3' or 'v1,v2'
        n_gen: Generation cases per variant (1–10, default 3 for speed)
        include_meta_grade: Run independent meta-grader on generated questions
        include_audit: Run meta-audit on quality evaluator results

    Returns comprehensive JSON report with all results and comparative summary.
    """
    variant_keys = [v.strip() for v in variants.split(",") if v.strip() in PROMPT_VARIANTS]
    if not variant_keys:
        return json.dumps({"error": f"No valid variants found in '{variants}'. Valid: {list(PROMPT_VARIANTS)}"})

    gen_results: dict = {}
    for key in variant_keys:
        raw = await run_generation_eval(ctx, variant=key, n_cases=n_gen, include_meta_grade=include_meta_grade)
        gen_results[key] = json.loads(raw)

    cal_raw = await run_calibration_eval(ctx, include_audit=include_audit)
    cal_results = json.loads(cal_raw)

    # Build comparative summary
    comparison = {
        key: {
            "variant_name": gen_results[key].get("variant_name"),
            "structural_pass_rate": gen_results[key].get("summary", {}).get("structural_pass_rate"),
            "keyword_grounding_rate": gen_results[key].get("summary", {}).get("keyword_grounding_rate"),
            "mean_quality_score": gen_results[key].get("summary", {}).get("mean_quality_score"),
            "mean_meta_score": gen_results[key].get("summary", {}).get("mean_meta_score"),
        }
        for key in variant_keys
    }

    return json.dumps({
        "generation_eval": gen_results,
        "calibration_eval": cal_results,
        "comparison": comparison,
    }, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
