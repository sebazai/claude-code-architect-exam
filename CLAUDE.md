# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a study and reference repository for the **Claude Certified Architect – Foundations** certification exam. The primary resource is `claude_certified_architect_instructions.pdf`, which covers production-grade Claude architecture patterns.

## Exam Domain Weights

| Domain | Weight |
|--------|--------|
| Agentic Architecture & Orchestration | 27% |
| Tool Design & MCP Integration | 18% |
| Claude Code Configuration & Workflows | 20% |
| Prompt Engineering & Structured Output | 20% |
| Context Management & Reliability | 15% |

## Key Architecture Principles from the Guide

These are recurring decision-making themes the exam tests:

- **Programmatic enforcement over prompt-based guidance** — for critical business logic, use code-level controls rather than relying on prompt instructions
- **Explicit criteria over vague instructions** — specificity reduces false positives and hallucination
- **Structured error context in multi-agent systems** — subagents must propagate enough information for coordinators to recover intelligently
- **Tool descriptions are the primary mechanism for tool selection** — descriptions carry more weight than tool names
- **Multi-pass reviews** — avoid attention dilution by splitting concerns across passes
- **Context management** — use structured fact extraction and scratchpad files rather than growing raw conversation context

## Claude API Patterns (in-scope for exam)

- Agentic loops driven by `stop_reason` (`"tool_use"` vs `"end_turn"`)
- `tool_use` content blocks with JSON Schema validation
- Message Batches API for cost-optimized batch processing (~50% savings)
- Coordinator–subagent multi-agent orchestration
- Human-in-the-loop workflows with confidence calibration

## Claude Code Configuration (in-scope for exam)

- `CLAUDE.md` — project context and team standards; supports hierarchical files per directory
- `.claude/rules/` — YAML files with glob patterns for conditional, path-scoped rule activation
- `.claude/commands/` — project-scoped custom slash commands
- `.claude/skills/` — skills with `SKILL.md` frontmatter (`context`, `allowed-tools`, `argument-hint`)
- `.mcp.json` — project-level MCP server configuration
- `~/.claude.json` — user-level MCP server configuration

## MCP Tool Design (in-scope for exam)

- Tool schemas are JSON Schema; descriptions drive LLM tool selection
- Resource catalogs for exposing contextual data
- Server-level vs tool-level authorization patterns

## Exam Simulator App (`exam-app/`)

An interactive MCP-based exam simulator that runs entirely inside Claude Code — no `ANTHROPIC_API_KEY` needed. All LLM inference is delegated to the Claude Code host via MCP Sampling (`ctx.sample()`).

### Running locally (requires `mcp[cli]>=1.6`)

```bash
pip install -e exam-app -e evals
```

The `.mcp.json` in `exam-app/` registers both the exam server and the evals server. Open Claude Code **from the `exam-app/` directory** (or symlink `exam-app/.mcp.json` to the repo root) so Claude Code picks them up automatically.

Then in Claude Code chat: **"Start the Claude Certified Architect exam"** (full: 60 questions / 120 min) or ask to use **`start_exam_mini`** for a shorter run (20 questions / 40 min, 4 scenarios × 5 questions).

### Running in the devcontainer (recommended — OS-agnostic, sandboxed)

Open the repo in VS Code → **"Reopen in Container"** (requires Docker + Dev Containers extension).

The devcontainer:
- Builds from `.devcontainer/Dockerfile` (Python 3.12-slim + Node.js + Claude Code CLI)
- Runs as a non-root user for security sandboxing
- Auto-installs `exam-app` and `evals` packages on `postCreateCommand`
- Bind-mounts `exam-app/.mcp.json` to `/workspace/.mcp.json` so Claude Code finds both MCP servers

### Architecture

```
Claude Code (host/client)
  │  connected to
  ▼
exam-app/mcp_server/server.py   ← FastMCP server
  ├── start_exam                → full exam: 4 random scenarios, 60 Q (15 per scenario), 120 min active time
  ├── start_exam_mini           → same flow: 4 scenarios × 5 Q = 20 total; 40 min active time (linear scale vs full)
  ├── get_next_question         → agentic loop: generate → quality eval → retry if score < 3
  ├── submit_answer             → records answer + user thinking time; returns verdict + explanation
  ├── get_results               → scaled score 100–1000, domain breakdown, per-question summary
  └── exam_status               → non-advancing status check
```

Key modules:
- `exam_content.py` — all 6 scenarios, 5 domains, 12 sample Q&A (few-shot examples for generation prompts)
- `evals.py` — `GENERATION_TEMPLATE`, `QUALITY_EVAL_TEMPLATE`, retry-with-feedback loop (`QUALITY_THRESHOLD=3`, `MAX_RETRIES=2`)
- `session.py` — in-memory `ExamSession`; user-active timer pauses during MCP generation/evaluation
- `hooks.py` — `post_generate_hook` / `post_evaluate_hook` (mirrors Agent SDK PostToolUse pattern)
- `scoring.py` — linear 100–1000 scale; passing ≥ 720

The session log is readable as MCP resource `exam://session/log`.

## Eval Pipeline (`evals/`)

A prompt evaluation pipeline for the exam simulator's generation and quality-evaluation prompts.

### Architecture

```
evals/
├── evals_server/server.py          ← FastMCP server (claude-architect-evals)
│     runs via MCP sampling — no ANTHROPIC_API_KEY needed
├── graders/
│   ├── code_grader.py              ← deterministic structural checks
│   └── model_grader.py             ← model-based graders (for CLI use)
├── prompts/variants.py             ← 3 prompt variants (v1/v2/v3)
├── datasets/
│   ├── generation_cases.json       ← 10 scenario×domain test cases
│   └── quality_calibration.json    ← 15 pre-labeled questions (good/mediocre/bad)
└── run_evals.py                    ← CLI runner (requires ANTHROPIC_API_KEY)
```

Both the exam server and the evals server are registered in `exam-app/.mcp.json` (bind-mounted as `/workspace/.mcp.json`).

### Running via MCP (recommended — no API key)

Invoke from Claude Code chat:

```
Run the generation eval for variant v2 with 5 cases
Run the calibration eval
Run the full eval comparing v1, v2, and v3
```

Tools: `list_eval_variants`, `run_generation_eval`, `run_calibration_eval`, `run_full_eval`

### Running via CLI (requires ANTHROPIC_API_KEY)

```bash
cd evals
python run_evals.py --eval-type calibration --skip-meta
python run_evals.py --variants v1,v2 --n-gen 5
```

### Prompt variants

- `v1` — baseline (current production prompt)
- `v2` — anti-generic constraint block added
- `v3` — `<thinking>` chain-of-thought step before JSON generation

### When modifying prompts

After changing `exam-app/mcp_server/evals.py` (generation or quality-eval prompts):
1. Run `run_calibration_eval` to check quality evaluator accuracy hasn't regressed
2. Run `run_generation_eval` on all 3 variants to benchmark the change
3. Compare `mean_quality_score` and `keyword_grounding_rate` across variants

## Out of Scope

The exam does not cover: fine-tuning, embeddings, RAG, non-Claude models, infrastructure provisioning, frontend/mobile UI, raw HTTP API details, or Anthropic's internal systems.
