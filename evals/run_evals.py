#!/usr/bin/env python3
"""
Evaluation pipeline for the Claude Certified Architect exam simulator prompts.

Evaluates two things:
  1. Generation eval   — 3 prompt variants × N test cases; grades structural validity,
                         keyword grounding, quality score (via quality evaluator),
                         and meta-grade (via independent dimensional rubric).
  2. Calibration eval  — 15 pre-labeled questions (good/mediocre/bad); tests whether
                         the quality evaluator's scores land in the expected ranges.

Usage:
    python run_evals.py [options]

    --model MODEL          Model for generation + quality eval  [default: claude-sonnet-4-6]
    --grader-model MODEL   Model for meta-grader + calibration audit  [default: same as --model]
    --variants v1,v2,v3    Comma-separated variant keys to run  [default: v1,v2,v3]
    --eval-type TYPE       generation | calibration | all        [default: all]
    --n-gen N              Limit generation cases (1-10)         [default: 10]
    --output-dir DIR       Directory for results JSON            [default: ./results]
    --skip-meta            Skip expensive meta-grader calls

Environment:
    ANTHROPIC_API_KEY  — required
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "exam-app"))

from mcp_server.exam_content import DOMAINS, SAMPLE_QUESTIONS, SCENARIOS  # noqa: E402
from mcp_server.evals import (  # noqa: E402
    QUALITY_EVAL_SYSTEM,
    build_quality_prompt,
    parse_quality_result,
    parse_question,
)

from graders.code_grader import (  # noqa: E402
    grade_generation,
    grade_keyword_grounding,
    grade_quality_eval_output,
    summarize_calibration_results,
    summarize_generation_results,
)
from graders.model_grader import audit_quality_evaluation, grade_with_meta_grader  # noqa: E402
from prompts.variants import PROMPT_VARIANTS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATASETS_DIR = Path(__file__).parent / "datasets"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_few_shot_examples(domain_id: int, n: int = 2) -> list[dict]:
    """Mirror of server.py _get_few_shot_examples — selects n samples for domain."""
    matching = [q for q in SAMPLE_QUESTIONS if q["domain_id"] == domain_id]
    selected = matching[:n] if len(matching) >= n else matching
    return [
        {
            **q,
            "scenario_name": SCENARIOS[q["scenario_id"]]["name"],
            "domain_name": DOMAINS[q["domain_id"]]["name"],
        }
        for q in selected
    ]


def _strip_thinking(text: str) -> str:
    """Remove <thinking>...</thinking> blocks before JSON parsing (for v3)."""
    return re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL).strip()


async def _generate_question(
    client: anthropic.AsyncAnthropic,
    prompt: str,
    system: str,
    model: str,
) -> tuple[dict | None, str]:
    """Call the generation API and parse the question. Returns (question_dict, raw_text)."""
    response = await client.messages.create(
        model=model,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    cleaned = _strip_thinking(raw)
    try:
        return parse_question(cleaned), raw
    except Exception as exc:
        log.warning("Parse error: %s", exc)
        return None, raw


async def _run_quality_eval(
    client: anthropic.AsyncAnthropic,
    question: dict,
    model: str,
) -> dict:
    """Run the built-in quality evaluator on a question dict."""
    prompt = build_quality_prompt(question)
    response = await client.messages.create(
        model=model,
        max_tokens=400,
        system=QUALITY_EVAL_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    result = parse_quality_result(raw)
    return {
        "score": result.score,
        "feedback": result.feedback,
        "criteria_met": result.criteria_met,
        "criteria_failed": result.criteria_failed,
    }


# ---------------------------------------------------------------------------
# Generation eval
# ---------------------------------------------------------------------------

async def _eval_one_generation_case(
    client: anthropic.AsyncAnthropic,
    case: dict,
    variant: dict,
    model: str,
    grader_model: str,
    skip_meta: bool,
) -> dict:
    scenario = SCENARIOS[case["scenario_id"]]
    domain = DOMAINS[case["domain_id"]]
    few_shot = _get_few_shot_examples(case["domain_id"])

    prompt = variant["build_prompt"](scenario, domain, few_shot)
    question, raw = await _generate_question(client, prompt, variant["system"], model)

    result: dict = {
        "case_id": case["id"],
        "scenario": scenario["name"],
        "domain": domain["name"],
        "generation_success": question is not None,
        "raw_output": raw,
    }

    if question is None:
        result["code_grade"] = {"overall_pass": False, "error": "parse_failure"}
        result["keyword_grade"] = {"passes_grounding": False}
        result["quality_eval"] = {"score": None}
        result["meta_grade"] = {"score": None}
        return result

    # Enrich with names for graders
    question["scenario_name"] = scenario["name"]
    question["domain_name"] = domain["name"]
    result["question"] = question

    # Code grade (sync)
    result["code_grade"] = grade_generation(question)

    # Keyword grounding check (sync)
    all_options = " ".join(question.get("options", {}).values())
    result["keyword_grade"] = grade_keyword_grounding(
        question.get("question", ""), all_options, case.get("scenario_keywords", [])
    )

    # Model grading — run quality eval and meta-grader concurrently
    tasks = [_run_quality_eval(client, question, model)]
    if not skip_meta:
        tasks.append(grade_with_meta_grader(client, question, grader_model))

    grades = await asyncio.gather(*tasks, return_exceptions=True)

    result["quality_eval"] = grades[0] if not isinstance(grades[0], Exception) else {"score": None, "error": str(grades[0])}
    result["meta_grade"] = grades[1] if len(grades) > 1 and not isinstance(grades[1], Exception) else {"score": None}

    return result


async def run_generation_eval(
    client: anthropic.AsyncAnthropic,
    cases: list[dict],
    args: argparse.Namespace,
) -> dict:
    cases = cases[: args.n_gen]
    variants_to_run = [v.strip() for v in args.variants.split(",")]
    results: dict = {}

    for variant_key in variants_to_run:
        if variant_key not in PROMPT_VARIANTS:
            log.warning("Unknown variant %r — skipping", variant_key)
            continue

        variant = PROMPT_VARIANTS[variant_key]
        log.info("Running generation eval: variant=%s (%s), n=%d", variant_key, variant["name"], len(cases))

        case_tasks = [
            _eval_one_generation_case(
                client, case, variant, args.model, args.grader_model, args.skip_meta
            )
            for case in cases
        ]
        case_results = await asyncio.gather(*case_tasks, return_exceptions=True)

        processed = []
        for i, r in enumerate(case_results):
            if isinstance(r, Exception):
                log.error("Case %s failed: %s", cases[i]["id"], r)
                processed.append({"case_id": cases[i]["id"], "error": str(r)})
            else:
                processed.append(r)

        results[variant_key] = {
            "variant_name": variant["name"],
            "variant_description": variant["description"],
            "cases": processed,
            "summary": summarize_generation_results(processed),
        }

    return results


# ---------------------------------------------------------------------------
# Calibration eval
# ---------------------------------------------------------------------------

async def _eval_one_calibration_case(
    client: anthropic.AsyncAnthropic,
    case: dict,
    model: str,
    grader_model: str,
    skip_meta: bool,
) -> dict:
    # Build a question dict compatible with build_quality_prompt
    question = {
        "scenario_name": case["scenario_name"],
        "domain_name": case["domain_name"],
        "question": case["question"],
        "options": case["options"],
        "correct": case["correct"],
        "explanation": case.get("explanation", ""),
    }

    expected_range: tuple[int, int] = tuple(case["expected_score_range"])  # type: ignore[assignment]

    # Run quality evaluator
    quality_result = await _run_quality_eval(client, question, model)

    # Code grade: is score in expected range?
    code_grade = grade_quality_eval_output(quality_result, expected_range)

    result: dict = {
        "case_id": case["id"],
        "label": case["label"],
        "expected_score_range": list(expected_range),
        "quality_eval": quality_result,
        "code_grade": code_grade,
    }

    # Optional meta-audit
    if not skip_meta:
        audit = await audit_quality_evaluation(client, question, quality_result, grader_model)
        result["audit"] = audit

    return result


async def run_calibration_eval(
    client: anthropic.AsyncAnthropic,
    cases: list[dict],
    args: argparse.Namespace,
) -> dict:
    log.info("Running calibration eval: n=%d", len(cases))

    tasks = [
        _eval_one_calibration_case(client, case, args.model, args.grader_model, args.skip_meta)
        for case in cases
    ]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    processed = []
    for i, r in enumerate(raw_results):
        if isinstance(r, Exception):
            log.error("Calibration case %s failed: %s", cases[i]["id"], r)
            processed.append({"case_id": cases[i]["id"], "error": str(r)})
        else:
            processed.append(r)

    return {
        "cases": processed,
        "summary": summarize_calibration_results(processed),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_generation_report(gen_results: dict) -> None:
    print("\n" + "=" * 70)
    print("GENERATION EVAL RESULTS")
    print("=" * 70)
    for variant_key, vdata in gen_results.items():
        s = vdata.get("summary", {})
        print(f"\n  Variant {variant_key}: {vdata.get('variant_name')} — {vdata.get('variant_description')}")
        print(f"    Cases run            : {s.get('total_cases')}")
        print(f"    Structural pass rate : {s.get('structural_pass_rate', 'N/A'):.0%}")
        print(f"    Keyword grounding    : {s.get('keyword_grounding_rate', 'N/A'):.0%}")
        print(f"    Mean quality score   : {s.get('mean_quality_score', 'N/A')}")
        print(f"    Mean meta score      : {s.get('mean_meta_score', 'N/A')}")
        dist = s.get("quality_score_distribution", {})
        if dist:
            dist_str = "  ".join(f"{k}:{v}" for k, v in sorted(dist.items()))
            print(f"    Quality distribution : {dist_str}")

    # Side-by-side comparison
    if len(gen_results) > 1:
        print("\n  --- Variant comparison (mean quality score) ---")
        for k, vdata in gen_results.items():
            score = vdata.get("summary", {}).get("mean_quality_score", "N/A")
            print(f"    {k} ({vdata.get('variant_name'):15s}) : {score}")


def _print_calibration_report(cal_results: dict) -> None:
    print("\n" + "=" * 70)
    print("CALIBRATION EVAL RESULTS")
    print("=" * 70)
    s = cal_results.get("summary", {})
    print(f"\n  Total cases          : {s.get('total_cases')}")
    print(f"  Overall accuracy     : {s.get('overall_accuracy', 0):.0%}  (score in expected range)")
    by_label = s.get("by_label", {})
    for label in ("good", "mediocre", "bad"):
        if label in by_label:
            d = by_label[label]
            print(f"  {label:10s} ({d['n']} cases) : {d['accuracy']:.0%} accuracy")

    # Per-case detail
    print("\n  Per-case details:")
    for c in cal_results.get("cases", []):
        qe = c.get("quality_eval", {})
        cg = c.get("code_grade", {})
        marker = "✓" if cg.get("overall_pass") else "✗"
        audit_flag = ""
        if "audit" in c:
            audit_flag = " [audit: " + ("✓" if c["audit"].get("evaluation_is_accurate") else "✗ INACCURATE") + "]"
        print(
            f"    {marker} {c['case_id']:20s}  label={c.get('label','?'):8s}  "
            f"score={qe.get('score','?')}/5  "
            f"expected={c.get('expected_score_range')}  "
            f"direction={cg.get('score_direction','?')}"
            f"{audit_flag}"
        )


def print_report(report: dict) -> None:
    print("\n" + "=" * 70)
    print(f"EVAL RUN  {report['timestamp']}")
    print(f"Model: {report['model']}  |  Grader: {report['grader_model']}")
    print("=" * 70)

    if "generation_eval" in report:
        _print_generation_report(report["generation_eval"])

    if "calibration_eval" in report:
        _print_calibration_report(report["calibration_eval"])

    print("\n" + "=" * 70)


def save_report(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = report["timestamp"].replace(":", "-").replace(".", "-")
    path = output_dir / f"eval_{ts}.json"
    path.write_text(json.dumps(report, indent=2, default=str))
    log.info("Results saved to %s", path)
    return path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="claude-sonnet-4-6", help="Model for generation + quality eval")
    p.add_argument("--grader-model", default=None, help="Model for meta-grader (defaults to --model)")
    p.add_argument("--variants", default="v1,v2,v3", help="Comma-separated variant keys")
    p.add_argument("--eval-type", choices=["generation", "calibration", "all"], default="all")
    p.add_argument("--n-gen", type=int, default=10, help="Number of generation cases to run (max 10)")
    p.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "results")
    p.add_argument("--skip-meta", action="store_true", help="Skip meta-grader API calls (faster, cheaper)")
    return p.parse_args()


async def async_main() -> None:
    args = parse_args()
    if args.grader_model is None:
        args.grader_model = args.model

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.AsyncAnthropic(api_key=api_key)

    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "grader_model": args.grader_model,
        "eval_type": args.eval_type,
        "variants": args.variants,
        "n_gen": args.n_gen,
        "skip_meta": args.skip_meta,
    }

    if args.eval_type in ("generation", "all"):
        gen_cases = json.loads((DATASETS_DIR / "generation_cases.json").read_text())
        report["generation_eval"] = await run_generation_eval(client, gen_cases, args)

    if args.eval_type in ("calibration", "all"):
        cal_cases = json.loads((DATASETS_DIR / "quality_calibration.json").read_text())
        report["calibration_eval"] = await run_calibration_eval(client, cal_cases, args)

    print_report(report)
    out_path = save_report(report, args.output_dir)
    print(f"\nFull results: {out_path}")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
