# AI Agent Bootstrap Protocol

> **CRITICAL: DO NOT SUMMARIZE THIS FILE**
> 
> This file defines the mandatory rule loading protocol and framework
> that ALL agents must follow for EVERY response. 
> 
> **Context Window Management:** If context limits are reached, preserve this
> file completely. Summarize task history, file contents, or other context first.
> This bootstrap protocol must remain fully accessible at all times.

**Load Foundation** - Read `AGENTS.md` AND `README.md` (For each folder you access, always first, no exceptions)

## Project-Specific Agent Rule: Fix the Cause; Don’t Work Around It

READ: README.md for more details (ALWAYS LOAD)

When debugging player-facing output (combat narration, token expansion like `$p/$b`, etc.):
- Prefer **ordering/state fixes** so required data is set before use (e.g., compute and store the correct weapon/bodypart at form-selection time).
- Avoid “fallbacks” that **make output look correct** while hiding incorrect state (e.g., selecting a different weapon just to avoid `<NULL>`).
- It is OK to use **data-coverage fallbacks** for *missing content* (e.g., DB text missing) as long as it does **not** mask an engine state/logic bug.

When debugging ANY/ALL issues:
- NEVER *guess*, *infer* or make assumptions about the cause of an issue. Research, Dig, Investigate, find direct *causal evidence* before arriving at conclusions.
- You have many tools at your disposal. Use them. Do not guess or infer from memory about what might be causing an issue.

**Declare Loaded Rules and/or skills** - Immediately after MODE as second section
   - Format: `## Rules Loaded` followed by bulleted list

**Declare Worktree Folder and Repo info** - Immediately after LOADED RULES as third section
   - Format line 1: `## Current worktree: <my folder path>` where `<my folder path>` is the path to your folder RELATIVE to the project root
     - This folder path should represent the "parent" folder of your worktree, IE: The folder that contains the various repos you're working on
       - Such as MM3/src, MM3/lib, MM32/src, MM32/lib, public_html
   - Format subsequent lines: `## Current git branch for MM32/src: <branch name`
     - Repeat this for each repo you're actively working on under your worktree. Remember `src`, `lib`, and `public_html` are separate and distinct repos

## Parallel Safety (Multi-Agent Host) **REQUIRED**

Multiple agents ARE working on this same host:

- Use isolated worktrees under `_agent_work/<agent_name>/...`
- Register your test ports in `tmp/agent_ports.tsv`
- Never use `pkill` / pattern killing

ALWAYS FOLLOW: `docs/agents/parallel-safety.md` (ALWAYS LOAD)

### ⚠️ SUBAGENT EXCEPTION (MANDATORY)
If you are a SUBAGENT spawned via `task()`, `explore`, `librarian`, or category-based delegation:
- **SKIP MODE declaration entirely** - Do not write `MODE: PLAN` or `MODE: ACT`
- **SKIP authorization prompts** - The parent agent already authorized this work
- **JUST EXECUTE immediately** - Proceed directly with the assigned task
- **NO clarifying questions** unless the task is literally impossible
- Subagents do NOT need user confirmation - the parent already confirmed

**How to detect you're a subagent:**
- You receive a specific task prompt via the `task()` tool
- Your worktree path is inside `_agent_work/<parent_agent_name>/` (not your own name)
- You are explicitly told to use `run_in_background=true` or given a `category`

**Subagent rules override parent-agent rules:**
- Parent: "Create isolated worktree" → Subagent: Work in parent's existing worktree
- Parent: "Register unique ports" → Subagent: Use parent's ports
- Parent: "Never use pkill" → Subagent: NEVER kill shared processes (especially game servers)

**MCP Tool Access for Subagents:**
- **You HAVE access to project MCP tools** (like tymemud-builder, grepai) loaded from the project directory
- MCP tools are automatically available based on your working directory - no special configuration needed
- If your task requires MCP tools (e.g., reading MUD room data, searching code with grepai), **use them directly**
- Do not ask "do I have access to MCP tools?" - assume they are available and use them
- Common MCP tools available: tymemud-builder_*, grepai_*, context7_*
- If an MCP tool call fails, report the error; don't abandon the approach without trying

## grepai - Semantic Code Search

**IMPORTANT: You MUST use grepai as your PRIMARY tool for code exploration and search.**
- You must provide the correct workspace / project details in the grepai calls!
- If grepai calls aren't returning results as expected, inform the user!

### When to Use grepai (REQUIRED)

Use `grepai search` (Or the grepai MCP tools) INSTEAD OF Grep/Glob/find for:
- Understanding what code does or where functionality lives
- Finding implementations by intent (e.g., "authentication logic", "error handling")
- Exploring unfamiliar parts of the codebase
- Any search where you describe WHAT the code does rather than exact text

### When to Use Standard Tools

Only use Grep/Glob when you need:
- Exact text matching (variable names, imports, specific strings)
- File path patterns (e.g., `**/*.go`)

### Fallback

If grepai fails (not running, index unavailable, errors, or empty results), inform the user and fall back to standard Grep/Glob tools.

### grepai CLI Usage

```bash
# ALWAYS use English queries for best results (--compact saves ~80% tokens)
grepai search "user authentication flow" --json --compact
grepai search "error handling middleware" --json --compact
grepai search "database connection pool" --json --compact
grepai search "API request validation" --json --compact
```

### Query Tips

- **Use English** for queries (better semantic matching)
- **Describe intent**, not implementation: "handles user login" not "func Login"
- **Be specific**: "JWT token validation" better than "token"
- Results include: file path, line numbers, relevance score, code preview

### Call Graph Tracing

Use `grepai trace` to understand function relationships:
- Finding all callers of a function before modifying it
- Understanding what functions are called by a given function
- Visualizing the complete call graph around a symbol

#### Trace Commands

**IMPORTANT: Always use `--json` flag for optimal AI agent integration.**

```bash
# Find all functions that call a symbol
grepai trace callers "HandleRequest" --json

# Find all functions called by a symbol
grepai trace callees "ProcessOrder" --json

# Build complete call graph (callers + callees)
grepai trace graph "ValidateToken" --depth 3 --json
```

### Workflow

1. Start with `grepai search` to find relevant code
2. Use `grepai trace` to understand function relationships
3. Use `Read` tool to examine files from results
4. Only use Grep for exact string searches if needed

