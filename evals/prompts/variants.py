"""
Three prompt variants for the question generation eval.

v1 — Baseline: current production prompt from exam-app/mcp_server/evals.py (unchanged)
v2 — Anti-Generic: injects an explicit scenario-grounding constraint block
v3 — Chain-of-Thought: asks the model to reason about the tradeoff before generating JSON
"""
from __future__ import annotations

from mcp_server.evals import (
    GENERATION_SYSTEM,
    GENERATION_TEMPLATE,
    build_generation_prompt as _build_v1,
)

# ---------------------------------------------------------------------------
# Shared example formatter (mirrors build_generation_prompt internals)
# ---------------------------------------------------------------------------

def _format_examples(few_shot_examples: list[dict]) -> str:
    return "\n\n".join(
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


def _format_feedback(retry_feedback: str) -> str:
    if not retry_feedback:
        return ""
    return f"\n\n⚠️  PREVIOUS ATTEMPT WAS REJECTED — please address these issues:\n{retry_feedback}"


def _base_format_args(scenario: dict, domain: dict, few_shot_examples: list[dict], retry_feedback: str) -> dict:
    return dict(
        scenario_name=scenario["name"],
        scenario_description=scenario["description"],
        domain_name=domain["name"],
        task_statements="\n".join(f"• {ts}" for ts in domain["task_statements"]),
        key_concepts="\n".join(f"• {kc}" for kc in domain["key_concepts"]),
        anti_patterns="\n".join(f"• {ap}" for ap in domain.get("anti_patterns", [])),
        few_shot_examples=_format_examples(few_shot_examples),
        retry_feedback=_format_feedback(retry_feedback),
    )


# ---------------------------------------------------------------------------
# V2 — Anti-Generic Constraint
# Inserts an explicit block that forbids scenario-agnostic questions.
# ---------------------------------------------------------------------------

_ANTI_GENERIC_BLOCK = """\
═══ ANTI-GENERIC CONSTRAINT ═══
Your question MUST be answerable differently depending on this specific scenario.
Reference at least ONE of:
  • Named tools from this scenario (e.g., if the scenario mentions process_refund, use it)
  • Specific SLAs, metrics, or numbers stated in the scenario description
  • Named agents, subsystems, or workflow steps unique to this scenario
A question that could appear in a generic Claude tutorial without modification → REJECT and rewrite.

"""

GENERATION_TEMPLATE_V2 = GENERATION_TEMPLATE.replace(
    "═══ REQUIREMENTS ═══",
    _ANTI_GENERIC_BLOCK + "═══ REQUIREMENTS ═══",
)


def build_generation_prompt_v2(
    scenario: dict,
    domain: dict,
    few_shot_examples: list[dict],
    retry_feedback: str = "",
) -> str:
    return GENERATION_TEMPLATE_V2.format(**_base_format_args(scenario, domain, few_shot_examples, retry_feedback))


# ---------------------------------------------------------------------------
# V3 — Chain-of-Thought before JSON
# Asks the model to reason inside <thinking> tags before generating.
# ---------------------------------------------------------------------------

GENERATION_TEMPLATE_V3 = GENERATION_TEMPLATE.replace(
    "Respond with ONLY this JSON (no markdown, no extra text):",
    """\
Before writing the JSON, think through the question design inside <thinking> tags:
  1. What is the core TRADEOFF that this domain and scenario make concrete?
  2. Which anti-pattern from the list would a partial-knowledge candidate fall into?
  3. How will each of the 3 distractors exploit that partial-knowledge gap?

After </thinking>, output ONLY the JSON object below (no other text):""",
)


def build_generation_prompt_v3(
    scenario: dict,
    domain: dict,
    few_shot_examples: list[dict],
    retry_feedback: str = "",
) -> str:
    return GENERATION_TEMPLATE_V3.format(**_base_format_args(scenario, domain, few_shot_examples, retry_feedback))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PROMPT_VARIANTS: dict[str, dict] = {
    "v1": {
        "name": "Baseline",
        "description": "Current production prompt from evals.py (unchanged)",
        "system": GENERATION_SYSTEM,
        "build_prompt": _build_v1,
    },
    "v2": {
        "name": "Anti-Generic",
        "description": "Adds explicit anti-generic constraint requiring scenario-specific grounding",
        "system": GENERATION_SYSTEM,
        "build_prompt": build_generation_prompt_v2,
    },
    "v3": {
        "name": "Chain-of-Thought",
        "description": "Adds <thinking> step for tradeoff reasoning before JSON generation",
        "system": GENERATION_SYSTEM,
        "build_prompt": build_generation_prompt_v3,
    },
}
