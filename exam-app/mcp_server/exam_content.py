"""
Exam content encoded from the Claude Certified Architect – Foundations exam guide PDF.

Exam structure (real exam):
  - 60 questions, 120 minutes
  - 4 scenarios randomly selected from 6
  - 15 questions per scenario
  - Score: 100–1000 (passing: 720)
  - Multiple choice: 1 correct + 3 distractors
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
        ],
        "anti_patterns": [
            "Parsing natural language signals to determine loop termination",
            "Setting arbitrary iteration caps as the primary stopping mechanism",
            "Checking assistant text content as a completion indicator",
            "Relying on prompt instructions alone for deterministic business-rule compliance",
            "Over-narrow task decomposition leading to incomplete coverage of broad research topics",
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
        ],
        "anti_patterns": [
            "Generic error responses ('Operation failed') that prevent intelligent recovery",
            "Silently suppressing errors (returning empty results as success)",
            "Giving synthesis agents access to web search tools (role bleed)",
            "Preferring built-in tools (Grep) over more capable MCP tools with weak descriptions",
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
        ],
        "anti_patterns": [
            "Using batch API for blocking workflows (pre-merge checks) — no latency SLA",
            "Relying on confidence-based filtering instead of explicit categorical criteria",
            "Running three full-PR review passes to require consensus (suppresses intermittent real bugs)",
            "Using tool_choice: 'auto' when you need guaranteed structured output",
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
        ],
        "anti_patterns": [
            "Returning generic error status ('search unavailable') that hides context from coordinator",
            "Silently suppressing errors (returning empty results as success)",
            "Terminating entire workflow on single subagent failure",
            "Aggregate accuracy metrics (97% overall) masking poor performance on specific document types",
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
            "A": "Add explicit escalation criteria to your system prompt with few-shot examples demonstrating when to escalate versus resolve autonomously.",
            "B": "Have the agent self-report a confidence score (1-10) before each response and automatically route requests to humans when confidence falls below a threshold.",
            "C": "Deploy a separate classifier model trained on historical tickets to predict which requests need escalation before the main agent begins processing.",
            "D": "Implement sentiment analysis to detect customer frustration levels and automatically escalate when negative sentiment exceeds a threshold.",
        },
        "correct": "A",
        "explanation": (
            "Adding explicit escalation criteria with few-shot examples directly addresses the root cause: "
            "unclear decision boundaries. This is the proportionate first response before adding infrastructure. "
            "Option B fails because LLM self-reported confidence is poorly calibrated — the agent is already "
            "incorrectly confident on hard cases. Option C is over-engineered, requiring labeled data and ML "
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
            "A": "Enter plan mode to explore the codebase, understand dependencies, and design an implementation approach before making changes.",
            "B": "Start with direct execution and make changes incrementally, letting the implementation reveal the natural service boundaries.",
            "C": "Use direct execution with comprehensive upfront instructions detailing exactly how each service should be structured.",
            "D": "Begin in direct execution mode and only switch to plan mode if you encounter unexpected complexity during implementation.",
        },
        "correct": "A",
        "explanation": (
            "Plan mode is designed for complex tasks involving large-scale changes, multiple valid approaches, "
            "and architectural decisions — exactly what monolith-to-microservices restructuring requires. It "
            "enables safe codebase exploration and design before committing to changes. Option B risks costly "
            "rework when dependencies are discovered late. Option C assumes you already know the right structure "
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
            "A": "Create rule files in .claude/rules/ with YAML frontmatter specifying glob patterns to conditionally apply conventions based on file paths.",
            "B": "Consolidate all conventions in the root CLAUDE.md file under headers for each area, relying on Claude to infer which section applies.",
            "C": "Create skills in .claude/skills/ for each code type that include the relevant conventions in their SKILL.md files.",
            "D": "Place a separate CLAUDE.md file in each subdirectory containing that area's specific conventions.",
        },
        "correct": "A",
        "explanation": (
            "Option A is correct because .claude/rules/ with glob patterns (e.g., **/*.test.tsx) allows "
            "conventions to be automatically applied based on file paths regardless of directory location — "
            "essential for test files spread throughout the codebase. Option B relies on inference rather than "
            "explicit matching, making it unreliable. Option C requires manual skill invocation or relies on "
            "Claude choosing to load them, contradicting the need for deterministic 'automatic' application "
            "based on file paths. Option D can't easily handle files spread across many directories since "
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
            "B": "The coordinator agent's task decomposition is too narrow, resulting in subagent assignments that don't cover all relevant domains of the topic.",
            "C": "The web search agent's queries are not comprehensive enough and need to be expanded to cover more creative industry sectors.",
            "D": "The document analysis agent is filtering out sources related to non-visual creative industries due to overly restrictive relevance criteria.",
        },
        "correct": "B",
        "explanation": (
            "The coordinator's logs reveal the root cause directly: it decomposed 'creative industries' into "
            "only visual arts subtasks (digital art, graphic design, photography), completely omitting music, "
            "writing, and film. The subagents executed their assigned tasks correctly — the problem is what "
            "they were assigned. Options A, C, and D incorrectly blame downstream agents that are working "
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
            "A": "Return structured error context to the coordinator including the failure type, the attempted query, any partial results, and potential alternative approaches.",
            "B": "Implement automatic retry logic with exponential backoff within the subagent, returning a generic 'search unavailable' status only after all retries are exhausted.",
            "C": "Catch the timeout within the subagent and return an empty result set marked as successful.",
            "D": "Propagate the timeout exception directly to a top-level handler that terminates the entire research workflow.",
        },
        "correct": "A",
        "explanation": (
            "Structured error context gives the coordinator the information it needs to make intelligent "
            "recovery decisions — whether to retry with a modified query, try an alternative approach, or "
            "proceed with partial results. Option B's generic status hides valuable context from the "
            "coordinator, preventing informed decisions. Option C suppresses the error by marking failure as "
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
            "A": "Add the -p flag: claude -p \"Analyze this pull request for security issues\"",
            "B": "Set the environment variable CLAUDE_HEADLESS=true before running the command.",
            "C": "Redirect stdin from /dev/null: claude \"Analyze this pull request for security issues\" < /dev/null",
            "D": "Add the --batch flag: claude --batch \"Analyze this pull request for security issues\"",
        },
        "correct": "A",
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
            "A": "Split into focused passes: analyze each file individually for local issues, then run a separate integration-focused pass examining cross-file data flow.",
            "B": "Require developers to split large PRs into smaller submissions of 3-4 files before the automated review runs.",
            "C": "Switch to a higher-tier model with a larger context window to give all 14 files adequate attention in one pass.",
            "D": "Run three independent review passes on the full PR and only flag issues that appear in at least two of the three runs.",
        },
        "correct": "A",
        "explanation": (
            "Splitting reviews into focused passes directly addresses the root cause: attention dilution when "
            "processing many files at once. File-by-file analysis ensures consistent depth, while a separate "
            "integration pass catches cross-file issues. Option B shifts burden to developers without improving "
            "the system. Option C misunderstands that larger context windows don't solve attention quality "
            "issues. Option D would actually suppress detection of real bugs by requiring consensus on issues "
            "that may only be caught intermittently."
        ),
    },
]

# ---------------------------------------------------------------------------
# Exam constants
# ---------------------------------------------------------------------------

TOTAL_QUESTIONS = 60
QUESTIONS_PER_SCENARIO = 15  # 4 scenarios × 15 = 60
EXAM_DURATION_SECONDS = 7200  # 120 minutes
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
