# AGENTS/README Context Reduction Refactor Plan (2026-04-23)

## Goal

Reduce always-loaded prompt weight from `AGENTS.md`, `README.md`, and related instruction files without losing critical behavioral guarantees.

## Current Findings

### 1. `AGENTS.md` is carrying too much always-load detail

Current file size is modest in lines, but disproportionately expensive because it is loaded every response and includes a large procedural section for grepai usage.

Key observations:

- Roughly half of `AGENTS.md` is dedicated to grepai usage details, examples, workflow, and CLI syntax.
- The grepai section mixes:
  - normative policy (`use grepai first`)
  - operational fallback (`if grepai fails, use Grep/Glob`)
  - user education/examples (`grepai search ...`, `grepai trace ...`)
- Only the first two bullets above need to live in an always-load bootstrap file.

### 2. `README.md` duplicates agent-facing rules already expressed elsewhere

`README.md` currently serves three roles at once:

- project overview and repo map
- branch/worktree workflow reference
- detailed AI/agent operating instructions

That third role causes prompt bloat because `README.md` is also always loaded.

Notable duplication with `AGENTS.md` and related docs:

- “Fix the Cause; Don’t Work Around It” appears in both `AGENTS.md` and `README.md`
- parallel-safety concepts are summarized in `README.md` and `AGENTS.md`, while the canonical detail already exists in `docs/agents/parallel-safety.md`
- agent workflow/process instructions in `README.md` overlap with bootstrap/process rules in `AGENTS.md`

### 3. Skills are underused for task-triggered guidance

Current project skill inventory is narrow (`run-mud-server` in `.opencode/skills/`). This means detailed procedures are being stuffed into always-loaded docs instead of loaded only when relevant.

### 4. MCP guidance is incomplete and misplaced

Current `AGENTS.md` says subagents can use MCP tools directly, but it does not actually teach:

- how to choose workspace/project parameters for grepai
- when to use grepai search vs RPG/trace tools
- how to reason about local vs remote MCPs
- how to recover from common MCP failure modes

This is another sign that procedural tool guidance belongs in narrower docs/skills, not in the bootstrap file.

## Refactor Principles

### What MUST stay in `AGENTS.md`

`AGENTS.md` should remain a thin bootstrap/control file only.

Keep:

- mandatory load order (`AGENTS.md` + `README.md`)
- non-negotiable anti-guessing / causal-evidence rule
- required response metadata/format declarations
- minimal worktree declaration requirements
- minimal subagent override rules
- short grepai-first mandate
- short pointer to canonical docs for details

Do **not** keep examples, workflows, extended tool tutorials, or long “when to use X” prose if it can be deferred.

### What SHOULD stay in `README.md`

`README.md` should become a thin project map.

Keep:

- project overview
- repository structure / branch map
- branch-specific MANIFESTO pointers
- high-level workflow rules
- links to canonical docs

Move detailed agent-operating instructions out unless they are essential for first-contact orientation.

### What SHOULD move to narrower docs or skills

Move detailed, task-triggered, or tool-specific procedures into:

- `docs/agents/*.md` for canonical operational references
- `.opencode/skills/*/SKILL.md` for truly procedural, trigger-based workflows

## Proposed File/Responsibility Layout

### A. `AGENTS.md` → thin bootstrap

Target responsibilities:

1. mandatory load order
2. anti-guessing / causal evidence rule
3. response declaration requirements
4. minimal subagent exception rules
5. grepai-first policy in 3-5 lines
6. pointers to canonical docs:
   - `docs/agents/parallel-safety.md`
   - `docs/agents/grepai.md`
   - `docs/agents/mcp-tooling.md`

### B. `README.md` → thin project map

Target responsibilities:

1. project/repo overview
2. worktree and repo layout
3. branch/workflow map
4. links to canonical agent docs

Remove or heavily shorten the current AI-agent instruction block.

### C. New `docs/agents/grepai.md`

Move from `AGENTS.md`:

- grepai usage rationale
- when to use grepai vs Grep/Glob
- CLI examples
- query-writing tips
- trace usage examples
- workflow examples

Add missing practical guidance:

- how to choose workspace/project fields for grepai MCP calls
- what to do when grepai returns empty results
- how to distinguish semantic search from exact-match search
- call graph usage guidance for modifications

### D. New `docs/agents/mcp-tooling.md`

Purpose:

- centralize MCP usage guidance currently only implied in `AGENTS.md`
- document grepai, tymemud-builder, context7, and other project MCPs
- provide guidance for local-vs-remote MCP expectations and parameter selection

This should be a reference doc, not always loaded.

### E. Possible new skills

#### 1. `grepai-investigation`

Recommended as a skill **only if** it is used for deeper procedural workflows, not as the sole place where grepai is mentioned.

Important: do **not** move the entire grepai mandate to a skill. If that happens, agents may stop preferring grepai by default.

Best split:

- `AGENTS.md`: “Use grepai first for semantic exploration; see docs/agents/grepai.md for details.”
- skill: only for deeper, multi-step grepai investigation patterns

#### 2. `mcp-investigation` or `mcp-tool-selection`

Potential skill for:

- choosing among grepai / builder / context7 / web tools
- troubleshooting MCP failures
- deciding between semantic search and direct tool use

This is more plausible than putting all MCP guidance in `AGENTS.md`.

## Specific Cuts Recommended

### `AGENTS.md`

#### Keep in place

- lines 1-12 style bootstrap header/load rule
- fix-the-cause / no-guessing rules
- declaration requirements
- condensed parallel-safety pointer
- condensed subagent rules

#### Replace with pointer

Current grepai block should be reduced to something like:

> Use grepai as the primary semantic search tool for code exploration.
> Use Grep/Glob only for exact text or filename patterns.
> If grepai fails or returns nothing useful, say so and fall back.
> Detailed usage: `docs/agents/grepai.md`.

### `README.md`

#### Keep in place

- project overview
- repo structure
- branch-specific docs pointers
- high-level workflow rules
- links to canonical docs

#### Remove or shorten

- duplicated “Fix the Cause” prose
- detailed agent operational checklist
- detailed documentation/memory-bank/changelog prose that can move to a dedicated workflow doc

### `docs/agents/parallel-safety.md`

Already correctly positioned as a canonical detail doc. No need to move this into a skill. The right change is to reduce repeated summaries elsewhere.

## Risks of Moving Too Much

### Risk 1: Skills are not always loaded

If all grepai guidance is moved into a skill, agents may stop consistently choosing grepai first. The mandatory policy needs to remain in `AGENTS.md`.

### Risk 2: Bootstrap files become too skeletal

If `AGENTS.md` loses the subagent override or anti-guessing rules, behavior quality may regress sharply. Those rules should stay.

### Risk 3: MCP guidance disappears into obscure docs

If MCP usage details are moved out without a clear pointer from `AGENTS.md`, agents may know tools exist but still use them incorrectly.

## Recommended Refactor Sequence

1. Create `docs/agents/grepai.md`
2. Create `docs/agents/mcp-tooling.md`
3. Reduce `AGENTS.md` grepai section to a short mandate + pointers
4. Remove duplicate “Fix the Cause” prose from one canonical file
5. Trim `README.md` AI-agent instructions to project-map essentials + pointers
6. Optionally add one skill for deep grepai investigation patterns

## Expected Outcome

If done carefully, this should reduce always-loaded instruction weight while preserving the most important behavior rules.

Biggest likely wins:

- lower per-turn context from `AGENTS.md`
- less duplication between `AGENTS.md` and `README.md`
- better MCP/grepai guidance quality in dedicated docs
- fewer examples/tutorials loaded on turns that do not need them

## Scope Clarification

This plan is advisory only. It does not yet modify `AGENTS.md`, `README.md`, or any docs besides this plan file.
