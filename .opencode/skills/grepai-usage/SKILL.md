---
name: grepai-usage
description: Use grepai correctly in this repo with verified CLI patterns, workspace/project scoping, and fallback guidance. Use this when you need semantic code search or call tracing.
license: MIT
compatibility: opencode
metadata:
  purpose: grepai-guidance
  project: tymemud
  agent: any
---

# grepai Usage

## Purpose

Use this skill when you need detailed grepai guidance beyond the short bootstrap rule in `AGENTS.md`.

This skill is based on commands verified locally in this repo, not guessed syntax.

## Preferred Path

Inside OpenCode, **prefer grepai MCP tools first**.

Use CLI examples in this skill as:

- fallback when MCP is unavailable
- a way to verify syntax/behavior locally
- a way to understand how MCP parameters map to grepai concepts

## Bootstrap Rule Boundary

`AGENTS.md` should continue to keep the mandatory short rule:

- use grepai first for semantic exploration
- use Grep/Glob for exact text or filename matching
- fall back explicitly if grepai is weak or unavailable

This skill holds the operational detail that does not need to be loaded every turn.

## Preferred MCP Usage

### Primary grepai MCP tools

Prefer these MCP tools when available:

- `grepai_grepai_search`
- `grepai_grepai_trace_callers`
- `grepai_grepai_trace_callees`
- `grepai_grepai_trace_graph`
- `grepai_grepai_index_status`

### MCP parameter conventions that matter in this repo

These are the repo-specific details that MCP schemas alone do not tell you:

- workspace name should normally be `tymemud`
- root project is `tymemud`
- `_agent_work` trees are indexed as separate projects, e.g.:
  - `wld_editor_api_agent`
  - `ubermap_agent`
- search-style tools use `projects` (plural)
- trace-style tools use `project` (singular)
- narrow `path` aggressively when you know the active subtree

### MCP-first patterns

#### Semantic search

Use `grepai_grepai_search` with:

- `workspace: "tymemud"`
- `projects: "tymemud"` for root project questions
- `projects: "wld_editor_api_agent"` (or another worktree project) for `_agent_work` questions
- `path` when you know the subtree, such as `MM32/src`
- `query` in English and intent-based

Examples of good MCP search inputs:

- query: `builder port authentication flow`
- query: `room history serialization`
- query: `statusport request validation`

#### Tracing

Use trace MCP tools with:

- `workspace: "tymemud"`
- singular `project`
- `symbol` for the function/symbol name
- `depth` for graph traversal

Observed behavior from live MCP calls:

- MCP trace responses reported `mode: "fast"`
- unlike the CLI, the MCP trace tool surface here does **not** expose an explicit `mode` parameter

Examples of good MCP trace inputs:

- callers of `room_history_new_entry` in `wld_editor_api_agent`
- graph for `status_tx_begin` in `wld_editor_api_agent`

### MCP result-quality warnings

Two repo-specific pitfalls still apply when using MCP:

1. grepai may return valid-but-unhelpful results.
   - An empty callers result is still a successful tool call.
   - Treat it as “no useful trace result found yet”, not as a syntax failure.

2. grepai may return indexed sibling paths you do not want.
   - We observed results from `MM32/src.BROKEN...` alongside active code.
   - Narrow project/path and inspect returned paths carefully.

## Verified CLI Shape

These command shapes were verified locally:

### Top-level help

```bash
grepai --help
grepai search --help
grepai trace callers --help
grepai trace graph --help
```

### Search

Verified working examples:

```bash
# Root project search
grepai search "builder port authentication flow" --json --compact --workspace tymemud --project tymemud

# Scoped agent-worktree search
grepai search "room history serialization" --json --compact --workspace tymemud --project wld_editor_api_agent --path MM32/src
```

Important details verified from help/output:

- query is positional: `grepai search "..."`
- `--workspace` takes the workspace name
- `--project` takes one indexed project name
- `--path` narrows results within that project scope
- `--json` and `--compact` both work together

### Trace

Verified working examples:

```bash
# Help
grepai trace callers --help
grepai trace graph --help

# Valid JSON response, no callers found is still a valid result
grepai trace callers "room_history_new_entry" --json --workspace tymemud --project wld_editor_api_agent --mode precise

# Verified graph result on known symbol
grepai trace graph "status_tx_begin" --json --workspace tymemud --project wld_editor_api_agent --mode precise --depth 1
```

Important details verified from help/output:

- symbol is positional after the subcommand
- `callers`, `callees`, and `graph` are separate subcommands
- `--mode` accepts `fast` or `precise`
- `--depth` applies to `graph`
- `--project` is singular for trace commands in the CLI help

## Workspace and Project Names

Verified patterns from this repo:

- workspace name: `tymemud`
- root project name: `tymemud`
- `_agent_work` trees are indexed as separate projects, e.g.:
- `wld_editor_api_agent`
- `ubermap_agent`

Use the narrowest project that still answers the question.

## Critical Root Distinction

Do **not** confuse the OpenCode repo root with the grepai project root.

- OpenCode project/root in this session is the top-level repo: `tymemud`
- grepai workspace is also `tymemud`
- but grepai projects inside that workspace are things like:
  - `tymemud`
  - `wld_editor_api_agent`
  - `ubermap_agent`

### What `path` is relative to

For grepai search, `path` is interpreted relative to the selected grepai project root, **not** relative to the OpenCode repo root.

This is a common failure mode.

### Correct vs incorrect examples

If you are targeting grepai project `wld_editor_api_agent`:

Correct:

```text
workspace = tymemud
projects = wld_editor_api_agent
path = MM32/src
```

Incorrect:

```text
workspace = tymemud
projects = wld_editor_api_agent
path = _agent_work/wld_editor_api_agent/MM32/src
```

Why incorrect:

- `_agent_work/wld_editor_api_agent/...` is relative to the OpenCode repo root
- grepai already knows the selected project root once `projects = wld_editor_api_agent` is set
- repeating the full repo-root-relative path points grepai at the wrong place

### Mental model

Think of grepai inputs like this:

1. `workspace` chooses the global grepai workspace
2. `projects` / `project` chooses one indexed project inside that workspace
3. `path` narrows inside that chosen grepai project only

If you choose the right grepai project first, `path` should usually become much shorter.

## Practical Scoping Rules

### Prefer root project when

- the question is about shared repo docs/config/scripts
- you want the canonical project root behavior

Example:

```bash
grepai search "builder port authentication flow" --json --compact --workspace tymemud --project tymemud
```

### Prefer `_agent_work` project when

- the question is about a specific worktree’s in-progress code
- the target module is only indexed meaningfully inside that worktree

Example:

```bash
grepai search "room history serialization" --json --compact --workspace tymemud --project wld_editor_api_agent --path MM32/src
```

## When grepai is the right tool

Use grepai for:

- semantic discovery
- unfamiliar code areas
- dependency/caller tracing
- intent-based search questions

Use Grep/Glob instead for:

- exact text matches
- exact filename/path patterns
- small follow-up literal checks

## Result Quality Warnings

Two real behaviors verified in this repo:

1. A grepai command can succeed and still return an empty/near-empty JSON result.
   - Example: `trace callers` on `room_history_new_entry` returned a valid JSON envelope with no callers.
   - Treat this as “no useful trace result found yet”, not necessarily as a syntax failure.

2. grepai may return results from indexed sibling paths you do not actually want.
   - Example: `trace graph status_tx_begin` returned hits from `MM32/src.BROKEN...` as well as active code.
   - Narrow `--project` and inspect paths carefully.

## Fallback Rules

If grepai is unavailable, stale, empty, or clearly weak:

1. say that explicitly
2. narrow scope and retry once if appropriate
3. fall back to `Grep` / `Glob`

## Relationship to Other Docs

- `AGENTS.md` keeps the short mandatory grepai-first bootstrap rule.
- This skill contains the detailed grepai operating guidance.
- Broader non-grepai MCP selection/scoping guidance remains in `docs/agents/mcp-tooling.md`.
