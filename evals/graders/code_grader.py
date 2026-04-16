"""Deterministic, code-based graders — no API calls."""
from __future__ import annotations


def grade_generation(output: dict) -> dict:
    """
    Structural validation of a generated question dict.
    Returns per-criterion booleans and a top-level overall_pass.
    """
    opts = output.get("options", {})
    question = output.get("question", "")
    explanation = output.get("explanation", "")
    correct = output.get("correct", "")

    checks: dict[str, bool] = {}

    checks["has_question"] = bool(question.strip())
    checks["question_min_length"] = len(question.strip()) >= 60
    checks["question_is_interrogative"] = question.strip().endswith("?")

    checks["has_all_options"] = all(bool(opts.get(k, "").strip()) for k in ("A", "B", "C", "D"))
    checks["four_distinct_options"] = len(
        {opts.get(k, "").strip().lower() for k in ("A", "B", "C", "D") if opts.get(k, "").strip()}
    ) == 4

    checks["valid_correct_letter"] = correct in ("A", "B", "C", "D")
    checks["correct_option_exists"] = bool(opts.get(correct, "").strip()) if correct in ("A", "B", "C", "D") else False

    checks["has_explanation"] = len(explanation.strip()) >= 50
    explanation_lower = explanation.lower()
    checks["explanation_addresses_distractors"] = (
        sum(
            1 for phrase in ("option a", "option b", "option c", "option d", "choice a", "choice b", "because", "incorrect", "wrong", "not")
            if phrase in explanation_lower
        ) >= 2
    )
    checks["explanation_min_length"] = len(explanation.strip()) >= 100

    checks["no_all_of_the_above"] = not any(
        "all of the above" in opts.get(k, "").lower() for k in ("A", "B", "C", "D")
    )
    checks["no_none_of_the_above"] = not any(
        "none of the above" in opts.get(k, "").lower() for k in ("A", "B", "C", "D")
    )

    checks["overall_pass"] = all([
        checks["has_question"],
        checks["question_min_length"],
        checks["has_all_options"],
        checks["four_distinct_options"],
        checks["valid_correct_letter"],
        checks["correct_option_exists"],
        checks["has_explanation"],
        checks["explanation_min_length"],
        checks["no_all_of_the_above"],
    ])

    _graded = {k: v for k, v in checks.items() if k != "overall_pass"}
    checks["score"] = sum(1 for v in _graded.values() if v is True)
    checks["max_score"] = len(_graded)

    return checks


def grade_keyword_grounding(question_text: str, options_combined: str, scenario_keywords: list[str]) -> dict:
    """
    Heuristic check: does the generated question reference scenario-specific terms?
    Returns match details and a passes_grounding flag.
    """
    haystack = (question_text + " " + options_combined).lower()
    matched = [kw for kw in scenario_keywords if kw.lower() in haystack]

    return {
        "keywords_checked": scenario_keywords,
        "keywords_matched": matched,
        "match_count": len(matched),
        "match_rate": round(len(matched) / len(scenario_keywords), 2) if scenario_keywords else 0.0,
        "passes_grounding": len(matched) >= 1,
    }


def grade_quality_eval_output(eval_output: dict, expected_range: tuple[int, int]) -> dict:
    """
    Code-grade the quality evaluator's JSON output.
    Checks structural validity and whether the score lands in the expected range.
    """
    score = eval_output.get("score")
    lo, hi = expected_range

    in_range = isinstance(score, int) and lo <= score <= hi
    direction = (
        "correct" if in_range
        else "too_high" if isinstance(score, int) and score > hi
        else "too_low" if isinstance(score, int) and score < lo
        else "invalid"
    )

    return {
        "has_score": score is not None,
        "has_feedback": bool(eval_output.get("feedback", "").strip()),
        "has_criteria_met": isinstance(eval_output.get("criteria_met"), list),
        "has_criteria_failed": isinstance(eval_output.get("criteria_failed"), list),
        "score_value": score,
        "expected_range": list(expected_range),
        "score_in_expected_range": in_range,
        "score_direction": direction,
        "overall_pass": in_range,
    }


def summarize_generation_results(cases: list[dict]) -> dict:
    """Aggregate code-grading results across all generation cases."""
    if not cases:
        return {}

    structural_passes = [c["code_grade"]["overall_pass"] for c in cases]
    grounding_passes = [c["keyword_grade"]["passes_grounding"] for c in cases if "keyword_grade" in c]
    quality_scores = [c["quality_eval"]["score"] for c in cases if c.get("quality_eval", {}).get("score") is not None]
    meta_scores = [c["meta_grade"]["score"] for c in cases if c.get("meta_grade", {}).get("score") is not None]

    return {
        "total_cases": len(cases),
        "structural_pass_rate": round(sum(structural_passes) / len(structural_passes), 3),
        "keyword_grounding_rate": round(sum(grounding_passes) / len(grounding_passes), 3) if grounding_passes else None,
        "mean_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None,
        "mean_meta_score": round(sum(meta_scores) / len(meta_scores), 2) if meta_scores else None,
        "quality_score_distribution": {
            str(i): quality_scores.count(i) for i in range(1, 6)
        } if quality_scores else {},
    }


def summarize_calibration_results(cases: list[dict]) -> dict:
    """Aggregate calibration eval results, broken down by quality label."""
    if not cases:
        return {}

    by_label: dict[str, list[bool]] = {}
    for c in cases:
        label = c.get("label", "unknown")
        passed = c.get("code_grade", {}).get("overall_pass", False)
        by_label.setdefault(label, []).append(passed)

    all_passes = [v for vals in by_label.values() for v in vals]
    return {
        "total_cases": len(cases),
        "overall_accuracy": round(sum(all_passes) / len(all_passes), 3) if all_passes else 0.0,
        "by_label": {
            label: {
                "n": len(results),
                "accuracy": round(sum(results) / len(results), 3),
            }
            for label, results in by_label.items()
        },
    }
