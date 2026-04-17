"""
Exam content encoded from the Claude Certified Architect – Foundations exam guide PDF.

Exam structure (real exam):
  - 60 questions, 120 minutes
  - 4 scenarios randomly selected from up to 13
  - 15 questions per scenario
  - Score: 100–1000 (passing: 720)
  - Multiple choice: 1 correct + 3 distractors

Note: The official exam guide lists 6 scenarios, but the real exam draws from a larger
pool of up to 13 scenarios. Scenarios 1–6 match the exam guide; 7–13 are additional
scenarios reported by candidates that are within the Foundations domain scope.
"""

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

SCENARIOS: dict[int, dict] = {
    1: {
        "name": "Customer Support Resolution Agent",
        "description": (
            "You are building a customer support resolution agent using the Claude Agent SDK. "
            "The agent handles high-ambiguity requests like returns, billing disputes, and account issues. "
            "It has access to your backend systems through custom Model Context Protocol (MCP) tools: "
            "get_customer, lookup_order, process_refund, escalate_to_human. "
            "Your target is 80%+ first-contact resolution while knowing when to escalate."
        ),
        "primary_domains": [1, 2, 5],
    },
    2: {
        "name": "Code Generation with Claude Code",
        "description": (
            "You are using Claude Code to accelerate software development. Your team uses it for code "
            "generation, refactoring, debugging, and documentation. You need to integrate it into your "
            "development workflow with custom slash commands, CLAUDE.md configurations, and understand "
            "when to use plan mode vs direct execution."
        ),
        "primary_domains": [3, 5],
    },
    3: {
        "name": "Multi-Agent Research System",
        "description": (
            "You are building a multi-agent research system using the Claude Agent SDK. A coordinator agent "
            "delegates to specialized subagents: one searches the web, one analyzes documents, one synthesizes "
            "findings, and one generates reports. The system researches topics and produces comprehensive, "
            "cited reports."
        ),
        "primary_domains": [1, 2, 5],
    },
    4: {
        "name": "Developer Productivity with Claude",
        "description": (
            "You are building developer productivity tools using the Claude Agent SDK. The agent helps "
            "engineers explore unfamiliar codebases, understand legacy systems, generate boilerplate code, "
            "and automate repetitive tasks. It uses the built-in tools (Read, Write, Bash, Grep, Glob) and "
            "integrates with Model Context Protocol (MCP) servers."
        ),
        "primary_domains": [2, 3, 1],
    },
    5: {
        "name": "Claude Code for Continuous Integration",
        "description": (
            "You are integrating Claude Code into your Continuous Integration/Continuous Deployment (CI/CD) "
            "pipeline. The system runs automated code reviews, generates test cases, and provides feedback on "
            "pull requests. You need to design prompts that provide actionable feedback and minimize false positives."
        ),
        "primary_domains": [3, 4],
    },
    6: {
        "name": "Structured Data Extraction",
        "description": (
            "You are building a structured data extraction system using Claude. The system extracts information "
            "from unstructured documents, validates the output using JSON schemas, and maintains high accuracy. "
            "It must handle edge cases gracefully and integrate with downstream systems."
        ),
        "primary_domains": [4, 5],
    },
    # ── Additional scenarios from the real exam pool (not in official guide) ──
    7: {
        "name": "Agentic Tool Design",
        "description": (
            "You are designing the tool layer for a production agentic system built on the Claude Agent SDK. "
            "The system must integrate with multiple backend services via MCP tools, and you are responsible "
            "for tool schema design, error handling conventions, authorization boundaries, and ensuring that "
            "LLM tool selection is reliable and predictable across a suite of 12+ tools."
        ),
        "primary_domains": [2, 1],
    },
    8: {
        "name": "Long Document Processing",
        "description": (
            "You are building a pipeline that processes long-form documents — contracts, research papers, "
            "and technical specifications — using Claude. The system must extract structured data, summarize "
            "sections, and answer questions about content that may exceed a single context window. You need "
            "to manage context effectively, preserve information fidelity across processing stages, and "
            "maintain source attribution throughout."
        ),
        "primary_domains": [5, 4],
    },
    9: {
        "name": "Claude for Operations",
        "description": (
            "You are deploying Claude to support internal operations at scale: incident triage, runbook "
            "execution, and cross-system workflow automation. The agent integrates with monitoring, ticketing, "
            "and communication tools via MCP servers. You must design for reliability, safe autonomous "
            "action, and clear human escalation paths when the agent reaches its authority boundaries."
        ),
        "primary_domains": [1, 2],
    },
    10: {
        "name": "Conversational AI Patterns",
        "description": (
            "You are designing a multi-turn conversational AI product powered by Claude. The system must "
            "maintain coherent context across long sessions, handle ambiguous or conflicting user instructions, "
            "and produce consistently structured responses. You are responsible for prompt architecture, "
            "context window management, persona consistency, and graceful handling of off-topic or adversarial inputs."
        ),
        "primary_domains": [4, 5],
    },
    11: {
        "name": "Agent Skills for Enterprise Knowledge Management",
        "description": (
            "You are building Claude Code skills and CLAUDE.md configurations for an enterprise knowledge "
            "management system. Teams use Claude Code to search, summarize, and cross-reference internal "
            "documentation, wikis, and code repositories. You need to design skills with appropriate context "
            "isolation, configure path-scoped rules for different knowledge domains, and expose MCP resources "
            "to reduce exploratory tool calls."
        ),
        "primary_domains": [3, 2],
    },
    12: {
        "name": "Agent Skills for Developer Tooling",
        "description": (
            "You are building a suite of Claude Code skills and custom slash commands for a platform "
            "engineering team. The skills automate common developer workflows: scaffolding new services, "
            "running compliance checks, generating API documentation, and triaging build failures. You must "
            "configure skill isolation, tool access scoping, and team-wide vs personal command distribution."
        ),
        "primary_domains": [3, 1],
    },
    13: {
        "name": "Agent Skills with Code Execution",
        "description": (
            "You are designing Claude Code skills that involve code generation and execution as part of "
            "automated workflows: running test suites, benchmarking implementations, validating migrations, "
            "and generating reproducible build artifacts. You must manage the safety boundaries of Bash "
            "tool access, design execution feedback loops, and ensure that skills operate correctly in "
            "both interactive and CI/CD non-interactive contexts."
        ),
        "primary_domains": [3, 4],
    },
}

# ---------------------------------------------------------------------------
# Domains  (weights must sum to 1.0)
# ---------------------------------------------------------------------------

DOMAINS: dict[int, dict] = {
    1: {
        "name": "Agentic Architecture & Orchestration",
        "weight": 0.27,
        "task_statements": [
            "Design and implement agentic loops for autonomous task execution",
            "Orchestrate multi-agent systems with coordinator-subagent patterns",
            "Configure subagent invocation, context passing, and spawning",
            "Implement multi-step workflows with enforcement and handoff patterns",
            "Apply Agent SDK hooks for tool call interception and data normalization",
            "Design task decomposition strategies for complex workflows",
            "Manage session state, resumption, and forking",
        ],
        "key_concepts": [
            "Agentic loop: send request → inspect stop_reason → execute tool → append result → loop",
            "stop_reason 'tool_use' means continue; stop_reason 'end_turn' means done",
            "Subagents have isolated context — they do NOT inherit the coordinator's conversation history",
            "Hub-and-spoke: coordinator manages all inter-subagent communication, error handling, routing",
            "Task tool is the mechanism for spawning subagents; allowedTools must include 'Task'",
            "Programmatic enforcement (hooks, prerequisite gates) > prompt-based guidance for critical logic",
            "PostToolUse hooks intercept tool results for transformation or compliance enforcement",
            "fork_session creates independent branches from a shared analysis baseline",
            "--resume <session-name> continues a named prior conversation",
            "Prompt chaining: fixed sequential passes for predictable multi-aspect reviews",
            "Dynamic decomposition: adaptive subtasks based on intermediate findings",
            "Parallel subagents: emit multiple Task tool calls in a single coordinator response",
            "Handoff summaries must include: customer ID, root cause, recommended action",
            "Shared vector store: subagents index outputs for semantic retrieval — prevents daisy-chaining full conversation logs",
            "Goal-oriented delegation: give subagents goals and quality criteria, not procedural steps; lets them adapt strategy",
            "Structured intermediate representation: standardize subagent outputs to a common JSON schema (claim, evidence, source, confidence) before synthesis",
            "tool_choice forced name: guarantees a specific tool fires first, enforcing pipeline execution order at the API level",
            "Prompt caching on synthesis subagent: reduces re-send overhead when 80K+ tokens of findings accumulate each turn",
            "Parallelization for latency: coordinator spawns N subagents simultaneously for independent work items (e.g., 12 legal precedents → 6x speedup)",
        ],
        "anti_patterns": [
            "Parsing natural language signals to determine loop termination",
            "Setting arbitrary iteration caps as the primary stopping mechanism",
            "Checking assistant text content as a completion indicator",
            "Relying on prompt instructions alone for deterministic business-rule compliance",
            "Over-narrow task decomposition leading to incomplete coverage of broad research topics",
            "Daisy-chaining full conversation logs between subagents — token costs scale exponentially with pipeline depth",
            "Procedural micromanagement of subagents: step-by-step instructions prevent adaptation on emerging or unexpected topics",
        ],
    },
    2: {
        "name": "Tool Design & MCP Integration",
        "weight": 0.18,
        "task_statements": [
            "Design effective tool interfaces with clear descriptions and boundaries",
            "Implement structured error responses for MCP tools",
            "Distribute tools appropriately across agents and configure tool choice",
            "Integrate MCP servers into Claude Code and agent workflows",
            "Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively",
        ],
        "key_concepts": [
            "Tool descriptions are the PRIMARY mechanism LLMs use for tool selection",
            "Include input formats, example queries, edge cases, and boundary explanations in descriptions",
            "Ambiguous/overlapping descriptions cause misrouting; minimal descriptions lead to unreliable selection",
            "isError flag pattern: communicate tool failures back to the agent",
            "Error categories: transient (timeouts), validation (invalid input), business (policy violations), permission",
            "isRetryable boolean distinguishes retryable from non-retryable errors",
            "Too many tools (e.g., 18 instead of 4-5) degrades tool selection reliability",
            "Scoped tool access: give agents only the tools needed for their role",
            "tool_choice 'auto': model may return text; 'any': must call a tool; forced: must call specific tool",
            "MCP project-level (.mcp.json) for shared team tooling vs user-level (~/.claude.json) for personal",
            "Environment variable expansion in .mcp.json for credential management without committing secrets",
            "MCP resources expose content catalogs to reduce exploratory tool calls",
            "Grep: content search (file contents); Glob: file path pattern matching; Edit: targeted modification",
            "Read + Write as fallback when Edit fails due to non-unique text matches",
            "Broad monolithic custom tools cause LLM to default to built-ins (Grep, Bash); split into granular single-purpose tools",
            "Application-side tool output filtering: extract only relevant fields from verbose API responses before they accumulate in context",
        ],
        "anti_patterns": [
            "Generic error responses ('Operation failed') that prevent intelligent recovery",
            "Silently suppressing errors (returning empty results as success)",
            "Giving synthesis agents access to web search tools (role bleed)",
            "Preferring built-in tools (Grep) over more capable MCP tools with weak descriptions",
            "Providing a broad catch-all custom tool alongside capable built-ins — model will prefer built-ins when descriptions are weak",
        ],
    },
    3: {
        "name": "Claude Code Configuration & Workflows",
        "weight": 0.20,
        "task_statements": [
            "Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization",
            "Create and configure custom slash commands and skills",
            "Apply path-specific rules for conditional convention loading",
            "Determine when to use plan mode vs direct execution",
            "Apply iterative refinement techniques for progressive improvement",
            "Integrate Claude Code into CI/CD pipelines",
        ],
        "key_concepts": [
            "CLAUDE.md hierarchy: user-level (~/.claude/CLAUDE.md) → project-level → directory-level",
            "User-level settings apply only to that user — NOT shared via version control",
            "@import syntax for modular CLAUDE.md (references external files)",
            ".claude/rules/ for topic-specific rule files as alternative to monolithic CLAUDE.md",
            "Project-scoped commands in .claude/commands/ (version-controlled, team-wide)",
            "User-scoped commands in ~/.claude/commands/ (personal, not shared)",
            "Skills in .claude/skills/ with SKILL.md frontmatter: context: fork, allowed-tools, argument-hint",
            "context: fork runs skill in isolated sub-agent context, preventing output from polluting main conversation",
            ".claude/rules/ with YAML frontmatter paths field (glob patterns) for conditional rule activation",
            "Plan mode: for large-scale changes, architectural decisions, multiple valid approaches, multi-file changes",
            "Direct execution: for simple, well-scoped, single-file changes with clear stack traces",
            "-p / --print flag for non-interactive CI mode; --output-format json with --json-schema for structured output",
            "Session context isolation: fresh Claude instance for PR review (not the code author's session)",
            "Concrete input/output examples > prose descriptions for transformation requirements",
            "Interview pattern: Claude asks questions before implementing in unfamiliar domains",
            "Directed exploration: start with imports/base interfaces, then trace specific implementations; generate subtasks dynamically from findings",
            "Session resumption with targeted context update: inform agent which specific files changed — avoid full re-read or ignoring changes",
        ],
        "anti_patterns": [
            "Placing team-wide instructions in user-level CLAUDE.md (teammates won't receive them)",
            "Using skills where always-loaded CLAUDE.md conventions would be more appropriate",
            "Using plan mode for simple single-file bug fixes with clear scope",
            "Running Claude Code in CI without the -p flag (will hang waiting for input)",
        ],
    },
    4: {
        "name": "Prompt Engineering & Structured Output",
        "weight": 0.20,
        "task_statements": [
            "Design prompts with explicit criteria to improve precision and reduce false positives",
            "Apply few-shot prompting to improve output consistency and quality",
            "Enforce structured output using tool use and JSON schemas",
            "Implement validation, retry, and feedback loops for extraction quality",
            "Design efficient batch processing strategies",
            "Design multi-instance and multi-pass review architectures",
        ],
        "key_concepts": [
            "Explicit criteria > vague instructions ('flag only when X contradicts Y' vs 'check accuracy')",
            "General instructions like 'be conservative' or 'only high-confidence' don't improve precision",
            "Few-shot examples: most effective for consistently formatted output when instructions alone fail",
            "Few-shot: 2-4 targeted examples showing reasoning for ambiguous-case handling",
            "tool_use with JSON schema: most reliable for guaranteed schema-compliant output (eliminates syntax errors)",
            "tool_choice 'any': guarantees model calls a tool; forced: ensures specific tool is called first",
            "Strict JSON schemas eliminate syntax errors but NOT semantic errors (values don't sum, wrong field)",
            "Retry-with-error-feedback: append specific validation errors to prompt on retry",
            "Retries ineffective when information is simply absent from source document",
            "Message Batches API: 50% cost savings, up to 24-hour processing, no guaranteed latency SLA",
            "Batch API: appropriate for non-blocking latency-tolerant workloads (overnight reports, nightly audits)",
            "Batch API: NOT appropriate for blocking pre-merge checks",
            "custom_id fields correlate batch request/response pairs",
            "Self-review limitation: model retains reasoning context from generation, less likely to question own decisions",
            "Independent review instances more effective than self-review for subtle issues",
            "Multi-pass review: per-file local passes + cross-file integration pass avoids attention dilution",
            "Nullable/optional fields prevent hallucination when information may be absent",
            "Resilient enum schemas: add catch-all 'other' value + detail string field; avoids fragile enum expansion on every new edge case",
            "Schema redundancy for mathematical consistency: capture both calculated_total and stated_total; flag for human review when they differ",
            "Three-stage prompt evolution: base prompt → explicit null-for-absent instructions → few-shot format normalization examples",
            "Routing tiers: urgent/blocking → real-time Messages API; standard async → Message Batches API (50% cost savings)",
        ],
        "anti_patterns": [
            "Using batch API for blocking workflows (pre-merge checks) — no latency SLA",
            "Relying on confidence-based filtering instead of explicit categorical criteria",
            "Running three full-PR review passes to require consensus (suppresses intermittent real bugs)",
            "Using tool_choice: 'auto' when you need guaranteed structured output",
            "Continuously expanding enums as edge cases arise instead of using a catch-all 'other' value",
        ],
    },
    5: {
        "name": "Context Management & Reliability",
        "weight": 0.15,
        "task_statements": [
            "Manage conversation context to preserve critical information across long interactions",
            "Design effective escalation and ambiguity resolution patterns",
            "Implement error propagation strategies across multi-agent systems",
            "Manage context effectively in large codebase exploration",
            "Design human review workflows and confidence calibration",
            "Preserve information provenance and handle uncertainty in multi-source synthesis",
        ],
        "key_concepts": [
            "Progressive summarization risk: condensing numerical values, dates, customer expectations into vague summaries",
            "'Lost in the middle' effect: models process beginning and end reliably; middle sections may be omitted",
            "Trim verbose tool outputs to only relevant fields before they accumulate in context",
            "Persistent 'case facts' block: transactional facts extracted outside summarized history",
            "Appropriate escalation triggers: customer requests human, policy gaps, inability to make progress",
            "Escalate immediately when customer explicitly demands it — do NOT attempt investigation first",
            "Sentiment-based escalation and self-reported confidence scores are unreliable proxies for complexity",
            "Multiple customer matches: ask for additional identifiers, do NOT select based on heuristics",
            "Structured error context: failure type, attempted query, partial results, alternative approaches",
            "Access failures (timeouts) ≠ valid empty results (successful queries with no matches)",
            "Scratchpad files persist key findings across context boundaries in long sessions",
            "/compact reduces context usage during extended exploration sessions",
            "Structured state persistence for crash recovery: each agent exports state, coordinator loads manifest",
            "Stratified random sampling for measuring error rates in high-confidence extractions",
            "Field-level confidence scores calibrated using labeled validation sets",
            "Source attribution: preserve claim-source mappings through synthesis steps",
            "Conflicting statistics: annotate with source attribution rather than arbitrarily selecting one value",
            "Stale tool_result filtering: on session resumption, remove prior tool_result messages to force fresh data fetch",
            "Session compression: summarize resolved turns into a narrative; preserve full verbatim history only for the active unresolved issue",
            "Application-layer intercept for zero-tolerance compliance: block tool calls server-side; remove model discretion for hard policy limits",
        ],
        "anti_patterns": [
            "Returning generic error status ('search unavailable') that hides context from coordinator",
            "Silently suppressing errors (returning empty results as success)",
            "Terminating entire workflow on single subagent failure",
            "Aggregate accuracy metrics (97% overall) masking poor performance on specific document types",
            "Trusting emphatic system-prompt instructions for zero-tolerance limits — 3% failure rate persists even with 'CRITICAL: NEVER' phrasing",
        ],
    },
}

# ---------------------------------------------------------------------------
# Sample questions from the PDF (all 12) — used as few-shot examples
# ---------------------------------------------------------------------------

SAMPLE_QUESTIONS: list[dict] = [
    # ── Scenario 1: Customer Support Resolution Agent ──────────────────────
    {
        "scenario_id": 1,
        "domain_id": 1,
        "question": (
            "Production data shows that in 12% of cases, your agent skips get_customer entirely "
            "and calls lookup_order using only the customer's stated name, occasionally leading to "
            "misidentified accounts and incorrect refunds. What change would most effectively "
            "address this reliability issue?"
        ),
        "options": {
            "A": "Add a programmatic prerequisite that blocks lookup_order and process_refund calls until get_customer has returned a verified customer ID.",
            "B": "Enhance the system prompt to state that customer verification via get_customer is mandatory before any order operations.",
            "C": "Add few-shot examples showing the agent always calling get_customer first, even when customers volunteer order details.",
            "D": "Implement a routing classifier that analyzes each request and enables only the subset of tools appropriate for that request type.",
        },
        "correct": "A",
        "explanation": (
            "When a specific tool sequence is required for critical business logic (like verifying customer "
            "identity before processing refunds), programmatic enforcement provides deterministic guarantees "
            "that prompt-based approaches cannot. Options B and C rely on probabilistic LLM compliance, which "
            "is insufficient when errors have financial consequences. Option D addresses tool availability "
            "rather than tool ordering, which is not the actual problem."
        ),
    },
    {
        "scenario_id": 1,
        "domain_id": 2,
        "question": (
            "Production logs show the agent frequently calls get_customer when users ask about orders "
            "(e.g., 'check my order #12345'), instead of calling lookup_order. Both tools have minimal "
            "descriptions ('Retrieves customer information' / 'Retrieves order details') and accept similar "
            "identifier formats. What's the most effective first step to improve tool selection reliability?"
        ),
        "options": {
            "A": "Add few-shot examples to the system prompt demonstrating correct tool selection patterns, with 5-8 examples showing order-related queries routing to lookup_order.",
            "B": "Expand each tool's description to include input formats it handles, example queries, edge cases, and boundaries explaining when to use it versus similar tools.",
            "C": "Implement a routing layer that parses user input before each turn and pre-selects the appropriate tool based on detected keywords and identifier patterns.",
            "D": "Consolidate both tools into a single lookup_entity tool that accepts any identifier and internally determines which backend to query.",
        },
        "correct": "B",
        "explanation": (
            "Tool descriptions are the primary mechanism LLMs use for tool selection. When descriptions are "
            "minimal, models lack the context to differentiate between similar tools. Option B directly addresses "
            "this root cause with a low-effort, high-leverage fix. Few-shot examples (A) add token overhead "
            "without fixing the underlying issue. A routing layer (C) is over-engineered and bypasses the LLM's "
            "natural language understanding. Consolidating tools (D) is a valid architectural choice but requires "
            "more effort than a 'first step' warrants when the immediate problem is inadequate descriptions."
        ),
    },
    {
        "scenario_id": 1,
        "domain_id": 5,
        "question": (
            "Your agent achieves 55% first-contact resolution, well below the 80% target. Logs show it "
            "escalates straightforward cases (standard damage replacements with photo evidence) while "
            "attempting to autonomously handle complex situations requiring policy exceptions. What's the "
            "most effective way to improve escalation calibration?"
        ),
        "options": {
            "A": "Deploy a separate classifier model trained on historical tickets to predict which requests need escalation before the main agent begins processing.",
            "B": "Have the agent self-report a confidence score (1-10) before each response and automatically route requests to humans when confidence falls below a threshold.",
            "C": "Add explicit escalation criteria to your system prompt with few-shot examples demonstrating when to escalate versus resolve autonomously.",
            "D": "Implement sentiment analysis to detect customer frustration levels and automatically escalate when negative sentiment exceeds a threshold.",
        },
        "correct": "C",
        "explanation": (
            "Adding explicit escalation criteria with few-shot examples directly addresses the root cause: "
            "unclear decision boundaries. This is the proportionate first response before adding infrastructure. "
            "Option B fails because LLM self-reported confidence is poorly calibrated — the agent is already "
            "incorrectly confident on hard cases. Option A is over-engineered, requiring labeled data and ML "
            "infrastructure when prompt optimization hasn't been tried. Option D solves a different problem "
            "entirely; sentiment doesn't correlate with case complexity, which is the actual issue."
        ),
    },
    # ── Scenario 2: Code Generation with Claude Code ───────────────────────
    {
        "scenario_id": 2,
        "domain_id": 3,
        "question": (
            "You want to create a custom /review slash command that runs your team's standard code review "
            "checklist. This command should be available to every developer when they clone or pull the "
            "repository. Where should you create this command file?"
        ),
        "options": {
            "A": "In the .claude/commands/ directory in the project repository.",
            "B": "In ~/.claude/commands/ in each developer's home directory.",
            "C": "In the CLAUDE.md file at the project root.",
            "D": "In a .claude/config.json file with a commands array.",
        },
        "correct": "A",
        "explanation": (
            "Project-scoped custom slash commands should be stored in the .claude/commands/ directory within "
            "the repository. These commands are version-controlled and automatically available to all developers "
            "when they clone or pull the repo. Option B (~/.claude/commands/) is for personal commands that "
            "aren't shared via version control. Option C (CLAUDE.md) is for project instructions and context, "
            "not command definitions. Option D describes a configuration mechanism that doesn't exist in Claude Code."
        ),
    },
    {
        "scenario_id": 2,
        "domain_id": 3,
        "question": (
            "You've been assigned to restructure the team's monolithic application into microservices. This "
            "will involve changes across dozens of files and requires decisions about service boundaries and "
            "module dependencies. Which approach should you take?"
        ),
        "options": {
            "A": "Use direct execution with comprehensive upfront instructions detailing exactly how each service should be structured.",
            "B": "Start with direct execution and make changes incrementally, letting the implementation reveal the natural service boundaries.",
            "C": "Enter plan mode to explore the codebase, understand dependencies, and design an implementation approach before making changes.",
            "D": "Begin in direct execution mode and only switch to plan mode if you encounter unexpected complexity during implementation.",
        },
        "correct": "C",
        "explanation": (
            "Plan mode is designed for complex tasks involving large-scale changes, multiple valid approaches, "
            "and architectural decisions — exactly what monolith-to-microservices restructuring requires. It "
            "enables safe codebase exploration and design before committing to changes. Option B risks costly "
            "rework when dependencies are discovered late. Option A assumes you already know the right structure "
            "without exploring the code. Option D ignores that the complexity is already stated in the "
            "requirements, not something that might emerge later."
        ),
    },
    {
        "scenario_id": 2,
        "domain_id": 3,
        "question": (
            "Your codebase has distinct areas with different coding conventions: React components use functional "
            "style with hooks, API handlers use async/await with specific error handling, and database models "
            "follow a repository pattern. Test files are spread throughout the codebase alongside the code they "
            "test (e.g., Button.test.tsx next to Button.tsx), and you want all tests to follow the same "
            "conventions regardless of location. What's the most maintainable way to ensure Claude automatically "
            "applies the correct conventions when generating code?"
        ),
        "options": {
            "A": "Place a separate CLAUDE.md file in each subdirectory containing that area's specific conventions.",
            "B": "Consolidate all conventions in the root CLAUDE.md file under headers for each area, relying on Claude to infer which section applies.",
            "C": "Create skills in .claude/skills/ for each code type that include the relevant conventions in their SKILL.md files.",
            "D": "Create rule files in .claude/rules/ with YAML frontmatter specifying glob patterns to conditionally apply conventions based on file paths.",
        },
        "correct": "D",
        "explanation": (
            "Option D is correct because .claude/rules/ with glob patterns (e.g., **/*.test.tsx) allows "
            "conventions to be automatically applied based on file paths regardless of directory location — "
            "essential for test files spread throughout the codebase. Option B relies on inference rather than "
            "explicit matching, making it unreliable. Option C requires manual skill invocation or relies on "
            "Claude choosing to load them, contradicting the need for deterministic 'automatic' application "
            "based on file paths. Option A can't easily handle files spread across many directories since "
            "CLAUDE.md files are directory-bound."
        ),
    },
    # ── Scenario 3: Multi-Agent Research System ────────────────────────────
    {
        "scenario_id": 3,
        "domain_id": 1,
        "question": (
            "After running the system on the topic 'impact of AI on creative industries,' you observe that "
            "each subagent completes successfully: the web search agent finds relevant articles, the document "
            "analysis agent summarizes papers correctly, and the synthesis agent produces coherent output. "
            "However, the final reports cover only visual arts, completely missing music, writing, and film "
            "production. When you examine the coordinator's logs, you see it decomposed the topic into three "
            "subtasks: 'AI in digital art creation,' 'AI in graphic design,' and 'AI in photography.' "
            "What is the most likely root cause?"
        ),
        "options": {
            "A": "The synthesis agent lacks instructions for identifying coverage gaps in the findings it receives from other agents.",
            "B": "The web search agent's queries are not comprehensive enough and need to be expanded to cover more creative industry sectors.",
            "C": "The document analysis agent is filtering out sources related to non-visual creative industries due to overly restrictive relevance criteria.",
            "D": "The coordinator agent's task decomposition is too narrow, resulting in subagent assignments that don't cover all relevant domains of the topic.",
        },
        "correct": "D",
        "explanation": (
            "The coordinator's logs reveal the root cause directly: it decomposed 'creative industries' into "
            "only visual arts subtasks (digital art, graphic design, photography), completely omitting music, "
            "writing, and film. The subagents executed their assigned tasks correctly — the problem is what "
            "they were assigned. Options A, B, and C incorrectly blame downstream agents that are working "
            "correctly within their assigned scope."
        ),
    },
    {
        "scenario_id": 3,
        "domain_id": 5,
        "question": (
            "The web search subagent times out while researching a complex topic. You need to design how this "
            "failure information flows back to the coordinator agent. Which error propagation approach best "
            "enables intelligent recovery?"
        ),
        "options": {
            "A": "Catch the timeout within the subagent and return an empty result set marked as successful.",
            "B": "Implement automatic retry logic with exponential backoff within the subagent, returning a generic 'search unavailable' status only after all retries are exhausted.",
            "C": "Return structured error context to the coordinator including the failure type, the attempted query, any partial results, and potential alternative approaches.",
            "D": "Propagate the timeout exception directly to a top-level handler that terminates the entire research workflow.",
        },
        "correct": "C",
        "explanation": (
            "Structured error context gives the coordinator the information it needs to make intelligent "
            "recovery decisions — whether to retry with a modified query, try an alternative approach, or "
            "proceed with partial results. Option B's generic status hides valuable context from the "
            "coordinator, preventing informed decisions. Option A suppresses the error by marking failure as "
            "success, which prevents any recovery and risks incomplete research outputs. Option D terminates "
            "the entire workflow unnecessarily when recovery strategies could succeed."
        ),
    },
    {
        "scenario_id": 3,
        "domain_id": 2,
        "question": (
            "During testing, you observe that the synthesis agent frequently needs to verify specific claims "
            "while combining findings. Currently, when verification is needed, the synthesis agent returns "
            "control to the coordinator, which invokes the web search agent, then re-invokes synthesis with "
            "results. This adds 2-3 round trips per task and increases latency by 40%. Your evaluation shows "
            "that 85% of these verifications are simple fact-checks (dates, names, statistics) while 15% "
            "require deeper investigation. What's the most effective approach to reduce overhead while "
            "maintaining system reliability?"
        ),
        "options": {
            "A": "Give the synthesis agent a scoped verify_fact tool for simple lookups, while complex verifications continue delegating to the web search agent through the coordinator.",
            "B": "Have the synthesis agent accumulate all verification needs and return them as a batch to the coordinator at the end of its pass, which then sends them all to the web search agent at once.",
            "C": "Give the synthesis agent access to all web search tools so it can handle any verification need directly without round-trips through the coordinator.",
            "D": "Have the web search agent proactively cache extra context around each source during initial research, anticipating what the synthesis agent might need to verify.",
        },
        "correct": "A",
        "explanation": (
            "Option A applies the principle of least privilege by giving the synthesis agent only what it needs "
            "for the 85% common case (simple fact verification) while preserving the existing coordination "
            "pattern for complex cases. Option B's batching approach creates blocking dependencies since "
            "synthesis steps may depend on earlier verified facts. Option C over-provisions the synthesis "
            "agent, violating separation of concerns. Option D relies on speculative caching that cannot "
            "reliably predict what the synthesis agent will need to verify."
        ),
    },
    # ── Scenario 5: Claude Code for Continuous Integration ─────────────────
    {
        "scenario_id": 5,
        "domain_id": 3,
        "question": (
            "Your pipeline script runs claude \"Analyze this pull request for security issues\" but the job "
            "hangs indefinitely. Logs indicate Claude Code is waiting for interactive input. What's the "
            "correct approach to run Claude Code in an automated pipeline?"
        ),
        "options": {
            "A": "Redirect stdin from /dev/null: claude \"Analyze this pull request for security issues\" < /dev/null",
            "B": "Set the environment variable CLAUDE_HEADLESS=true before running the command.",
            "C": "Add the -p flag: claude -p \"Analyze this pull request for security issues\"",
            "D": "Add the --batch flag: claude --batch \"Analyze this pull request for security issues\"",
        },
        "correct": "C",
        "explanation": (
            "The -p (or --print) flag is the documented way to run Claude Code in non-interactive mode. It "
            "processes the prompt, outputs the result to stdout, and exits without waiting for user input — "
            "exactly what CI/CD pipelines require. The other options reference non-existent features "
            "(CLAUDE_HEADLESS environment variable, --batch flag) or use Unix workarounds that don't properly "
            "address Claude Code's command syntax."
        ),
    },
    {
        "scenario_id": 5,
        "domain_id": 4,
        "question": (
            "Your team wants to reduce API costs for automated analysis. Currently, real-time Claude calls "
            "power two workflows: (1) a blocking pre-merge check that must complete before developers can merge, "
            "and (2) a technical debt report generated overnight for review the next morning. Your manager "
            "proposes switching both to the Message Batches API for its 50% cost savings. How should you "
            "evaluate this proposal?"
        ),
        "options": {
            "A": "Use batch processing for the technical debt reports only; keep real-time calls for pre-merge checks.",
            "B": "Switch both workflows to batch processing with status polling to check for completion.",
            "C": "Keep real-time calls for both workflows to avoid batch result ordering issues.",
            "D": "Switch both to batch processing with a timeout fallback to real-time if batches take too long.",
        },
        "correct": "A",
        "explanation": (
            "The Message Batches API offers 50% cost savings but has processing times up to 24 hours with no "
            "guaranteed latency SLA. This makes it unsuitable for blocking pre-merge checks where developers "
            "wait for results, but ideal for overnight batch jobs like technical debt reports. Option B is "
            "wrong because relying on 'often faster' completion isn't acceptable for blocking workflows. "
            "Option C reflects a misconception — batch results can be correlated using custom_id fields. "
            "Option D adds unnecessary complexity when the simpler solution is matching each API to its "
            "appropriate use case."
        ),
    },
    {
        "scenario_id": 5,
        "domain_id": 4,
        "question": (
            "A pull request modifies 14 files across the stock tracking module. Your single-pass review "
            "analyzing all files together produces inconsistent results: detailed feedback for some files but "
            "superficial comments for others, obvious bugs missed, and contradictory feedback — flagging a "
            "pattern as problematic in one file while approving identical code elsewhere in the same PR. "
            "How should you restructure the review?"
        ),
        "options": {
            "A": "Run three independent review passes on the full PR and only flag issues that appear in at least two of the three runs.",
            "B": "Require developers to split large PRs into smaller submissions of 3-4 files before the automated review runs.",
            "C": "Switch to a higher-tier model with a larger context window to give all 14 files adequate attention in one pass.",
            "D": "Split into focused passes: analyze each file individually for local issues, then run a separate integration-focused pass examining cross-file data flow.",
        },
        "correct": "D",
        "explanation": (
            "Splitting reviews into focused passes directly addresses the root cause: attention dilution when "
            "processing many files at once. File-by-file analysis ensures consistent depth, while a separate "
            "integration pass catches cross-file issues. Option B shifts burden to developers without improving "
            "the system. Option C misunderstands that larger context windows don't solve attention quality "
            "issues. Option A would actually suppress detection of real bugs by requiring consensus on issues "
            "that may only be caught intermittently."
        ),
    },
    # ── Additional questions derived from The Architect's Playbook ────────────
    {
        "scenario_id": 3,
        "domain_id": 1,
        "question": (
            "Your multi-agent research pipeline processes 50 topics simultaneously. Each synthesis agent "
            "receives the full conversation log of every prior web search agent run before it begins work. "
            "After scaling to 50 concurrent topics, synthesis agent API costs have increased 40x relative "
            "to the web search agents. What is the most likely cause and correct architectural fix?"
        ),
        "options": {
            "A": "The synthesis agent's context window is too small; upgrade to a model with a larger context window to absorb the accumulated logs.",
            "B": "Daisy-chaining full conversation logs between subagents scales token costs exponentially; have subagents index outputs into a shared vector store so synthesis agents retrieve only semantically relevant findings.",
            "C": "The web search agent is returning too many results per query; add a hard cap of 10 results to reduce the volume passed downstream.",
            "D": "The synthesis agent should summarize each web search result immediately upon receipt to prevent log accumulation.",
        },
        "correct": "B",
        "explanation": (
            "Passing full conversation logs between subagents causes token cost to grow exponentially as "
            "each subsequent agent accumulates all prior agents' histories. The correct architectural pattern "
            "is to decouple state from invocation: subagents write outputs to a shared vector store and "
            "downstream agents retrieve only semantically relevant findings. This also prevents state loss on "
            "pipeline crashes. Option A treats a scaling design problem as a model capability problem. "
            "Option C reduces result quality without addressing the root cause. Option D requires each "
            "subagent to summarize data it may not have full context to compress correctly."
        ),
    },
    {
        "scenario_id": 3,
        "domain_id": 1,
        "question": (
            "Your document analysis pipeline must always extract metadata before calling a citation enrichment "
            "tool (the enrichment tool requires the extracted DOI as an input parameter). In testing, the agent "
            "occasionally calls the enrichment tool first, causing downstream failures. You have already added "
            "a system prompt instruction 'Always call extract_metadata before lookup_citations.' The failures "
            "persist at a 5% rate. What is the most reliable fix?"
        ),
        "options": {
            "A": "Strengthen the system prompt instruction to 'CRITICAL: You MUST call extract_metadata before lookup_citations in every case, no exceptions.'",
            "B": "Add 3-5 few-shot examples to the system prompt demonstrating the correct tool call order.",
            "C": "Set tool_choice to force the extract_metadata tool on the first API call, guaranteeing metadata extraction happens before any enrichment call.",
            "D": "Merge extract_metadata and lookup_citations into a single combined tool that enforces the internal ordering.",
        },
        "correct": "C",
        "explanation": (
            "When a specific execution order is required for correctness, the API's tool_choice constraint "
            "provides deterministic enforcement — the model cannot skip or reorder the forced tool call. "
            "Options A and B are both prompt-based approaches; the 5% failure rate demonstrates that prompt "
            "instructions are insufficient for deterministic ordering requirements. Option D solves the "
            "ordering problem but creates a monolithic tool that cannot be independently reused and fails "
            "entirely if either component errors, rather than allowing partial recovery."
        ),
    },
    {
        "scenario_id": 1,
        "domain_id": 5,
        "question": (
            "Your customer support agent handles multi-hour ticket resolutions. When a session resumes after "
            "a 4-hour delay, agents tell customers 'your order is still in transit' based on a tool result "
            "fetched hours ago — even though the order was delivered 2 hours ago. Adding a system prompt "
            "instruction 'always re-verify order status on resumption' reduces but does not eliminate the "
            "problem. What is the correct architectural fix?"
        ),
        "options": {
            "A": "Summarize all previous tool results into a single status block at the top of the resumed session so the agent references only the summary.",
            "B": "On session resumption, programmatically filter out all previous tool_result messages from the conversation history, forcing the agent to re-fetch current data when needed.",
            "C": "Set a 30-minute TTL in the system prompt; instruct the agent to treat any tool result older than 30 minutes as expired.",
            "D": "Restart the session from scratch on every resumption with only the customer ID, discarding prior conversation history.",
        },
        "correct": "B",
        "explanation": (
            "Filtering stale tool_result messages at the application layer is the architectural fix — it "
            "removes the source of stale data rather than trying to instruct the model to ignore it. The "
            "agent retains valuable human/assistant conversation turns (customer history, prior agreements) "
            "while being forced to make fresh tool calls for any current state it needs. Option A risks "
            "compressing stale data into the summary. Option C relies on prompt-based TTL enforcement, which "
            "is probabilistic and already shown to be insufficient at 100%. Option D discards all valuable "
            "prior context unnecessarily."
        ),
    },
    {
        "scenario_id": 6,
        "domain_id": 4,
        "question": (
            "Your property document extraction system uses an enum schema for property_type: "
            "['house', 'apartment', 'condo', 'townhouse']. After deployment, 8% of documents fail "
            "validation with types like 'studio', 'converted warehouse', and 'live-work loft'. "
            "Your team proposes continuously expanding the enum as new types are encountered. "
            "What is the correct long-term architectural approach?"
        ),
        "options": {
            "A": "Switch property_type from an enum to a free-text string field to eliminate all validation failures.",
            "B": "Increase the retry limit so the model attempts to remap novel types to the closest known enum value on each retry.",
            "C": "Add a pre-processing classifier that normalizes any novel property type to the closest existing enum value before extraction.",
            "D": "Add a catch-all 'other' value to the enum paired with a property_type_detail string field, making the schema resilient to novel types without requiring ongoing expansion.",
        },
        "correct": "D",
        "explanation": (
            "Continuously expanding enums is a fragile anti-pattern — the schema breaks on every new edge "
            "case encountered in production. The resilient pattern adds a catch-all 'other' value paired "
            "with a detail string field: novel types are captured accurately rather than rejected or "
            "incorrectly mapped, validation always passes, and the detail field preserves the original "
            "value for downstream handling or human review. Option A loses the schema enforcement benefits "
            "that structured extraction provides. Option C introduces a preprocessing step that silently "
            "corrupts data semantics by forcing incorrect mappings. Option B has the same data corruption "
            "problem as C and adds unnecessary latency."
        ),
    },
    {
        "scenario_id": 3,
        "domain_id": 1,
        "question": (
            "Your coordinator agent provides its web search subagent with step-by-step instructions: "
            "'Step 1: Search for X. Step 2: Open the top 3 results. Step 3: Extract the author and date.' "
            "When researching an emerging topic with few established sources, the subagent exhausts all "
            "three prescribed steps without finding useful content and stops, despite relevant material "
            "being available through alternative search strategies. What is the root cause and correct fix?"
        ),
        "options": {
            "A": "The subagent's context window is too small to hold multiple search results simultaneously; increase max_tokens.",
            "B": "Procedural step-by-step instructions make subagents rigid; replace with goal-oriented delegation specifying research goals and quality criteria so the subagent can determine its own search strategy.",
            "C": "The subagent needs access to additional search tools to cover alternative source types.",
            "D": "Add a retry loop in the coordinator that re-invokes the subagent with different prescribed search terms when no results are found.",
        },
        "correct": "B",
        "explanation": (
            "Procedural micromanagement causes subagents to fail rigidly when their prescribed steps don't "
            "match the search landscape — they have no latitude to adapt. Goal-oriented delegation "
            "('find comprehensive coverage of X; prioritize recency and source diversity') lets the "
            "specialized subagent determine its own search strategy, which is especially critical for "
            "emerging topics where no fixed procedure works reliably. Option C adds tools without fixing "
            "the rigidity. Option D adds retry infrastructure but continues to prescribe steps rather "
            "than goals — the subagent will keep failing the same way with different search terms. "
            "Option A misdiagnoses a strategy problem as a capacity problem."
        ),
    },
    {
        "scenario_id": 1,
        "domain_id": 5,
        "question": (
            "After 48 turns covering three separate issues (a refund inquiry, a subscription question, "
            "and an active payment dispute), your support agent starts showing context pressure: it "
            "references the resolved refund case when answering questions about the payment dispute, "
            "and loses track of the payment dispute details mid-conversation. The first two issues "
            "are fully resolved. What is the correct context management strategy?"
        ),
        "options": {
            "A": "Use /compact to compress the entire 48-turn conversation into a dense summary that the agent references going forward.",
            "B": "Start a fresh session for the active payment dispute, providing only the customer ID as context.",
            "C": "Summarize the resolved refund and subscription turns into a brief narrative description, while preserving the full verbatim message history for the active, unresolved payment dispute.",
            "D": "Switch to a higher-tier model with a larger context window that can hold the entire 48-turn history without compression.",
        },
        "correct": "C",
        "explanation": (
            "Context compression should be surgical. Summarizing only the fully resolved turns frees "
            "context space while preserving their key outcomes (e.g., 'refund approved for $120, "
            "subscription downgraded to basic'). The active unresolved payment dispute retains its "
            "full verbatim history so the agent can reason accurately about the current issue without "
            "losing nuance. Option A applies uniform compression and risks losing critical details "
            "in the active dispute. Option B discards all prior context including important customer "
            "history from the resolved issues. Option D treats an architecture problem as a model "
            "capability problem — larger context windows don't solve attention dilution."
        ),
    },
]

# ---------------------------------------------------------------------------
# Exam constants
# ---------------------------------------------------------------------------

TOTAL_QUESTIONS = 60
QUESTIONS_PER_SCENARIO = 15  # 4 scenarios × 15 = 60
EXAM_DURATION_SECONDS = 7200  # 120 minutes

# Short practice exam: same 4-scenario flow, 5 questions per scenario (20 total), time scaled linearly vs full exam
MINI_TOTAL_QUESTIONS = 20
MINI_QUESTIONS_PER_SCENARIO = 5  # 4 scenarios × 5 = 20
MINI_EXAM_DURATION_SECONDS = int(EXAM_DURATION_SECONDS * MINI_TOTAL_QUESTIONS / TOTAL_QUESTIONS)

PASSING_SCORE = 720
SCORE_MIN = 100
SCORE_MAX = 1000
SCENARIOS_PER_EXAM = 4


def get_domain_question_distribution(n_questions: int = QUESTIONS_PER_SCENARIO) -> list[int]:
    """
    Returns a list of domain IDs for n_questions, distributed proportionally
    to domain weights (approximately). Used to assign a domain to each question slot.
    """
    distribution: list[int] = []
    for domain_id, domain in DOMAINS.items():
        count = round(domain["weight"] * n_questions)
        distribution.extend([domain_id] * count)
    # Pad or trim to exactly n_questions
    while len(distribution) < n_questions:
        distribution.append(1)  # pad with domain 1 (highest weight)
    return distribution[:n_questions]
