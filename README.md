# A Moment in Tyme (WoT MUD)

## Project Overview

**Name:** A Moment in Tyme  
**Genre:** Wheel of Time (WoT) themed Multi-User Dungeon (MUD)  
**Engine:** Based on MikkiMud / CircleMUD (C-based)  
**Language:** C (GNU11/C11 standard)  
**Database:** MySQL/MariaDB with SQL-based character persistence

---

## Repository Structure

This workspace contains three separate git repositories:

### DO NOT WORK DIRECTLY IN THESE TOP LEVEL FOLDERS

### Git Repository Structure

- **`MM3/src/`** - Local git repository tracking branch `svn/MM_3_Final` (stable/production MUD code)
- **`MM32/src/`** - Local git repository tracking branch `svn/MM_3-2_Start` (development MUD code)
- **`public_html/`** - Local git repository for the website (PHP/Apache assets)

The MUD repositories connect to the same remote: `jeremyakers/tymemud-src.git`  
The website repository connects to: `jeremyakers/tymemud-web.git`

**Important:** All git operations (commit, push, merge) must be run from within the relevant repo directory AFTER YOU COPY TO YOUR OWN WORKTREE:
- `cd MM3/src` for stable MUD branch operations
- `cd MM32/src` for dev MUD branch operations
- `cd public_html` for website operations

---

## Branch-Specific Documentation

**Each branch has its own MANIFESTO.md with branch-specific coding rules and guidelines:**

### For MM3 (Stable Branch) Work:
- **Location:** `MM3/src/MANIFESTO.md`
- **Use when:** Working on bugfixes, hotfixes, or production-critical features
- **Branch:** `svn/MM_3_Final`

### For MM32 (Development Branch) Work:
- **Location:** `MM32/src/MANIFESTO.md`
- **Use when:** Working on new features, major refactoring, or experimental code
- **Branch:** `svn/MM_3-2_Start`

---

## Workflow Rules

**The rule is: Fix in Stable, Merge to Dev.**

1. **Bugfixes and hotfixes** → Implement in YOUR COPY of `MM3/src/` first
2. **New features and refactoring** → Implement in YOUR COPY of `MM32/src/`
3. **Merging:** Use `MM32/src/merge-mm32` script to bring stable fixes from MM3 into MM32
4. **Never merge from MM32 to MM3** - The flow is always MM3 → MM32

### lib workflow (world data repo)

The world data (`lib/`) is a **separate repository** and follows a stricter promotion flow:

1. **All lib changes land in `builder` first**
2. Deploy/test on the **builderport** server
3. After validation, merge **`builder` → `main`**

This is intentional so builders can safely validate world/command table changes before they hit production.

---

## AI Agent Instructions

**When working on code in this project:**

1. **Identify which MikkiMUD version (each has its own branch) you're working on and CREATE YOUR OWN WORKTREE:**
   - MikkiMUD 3.0 (MM3) Files are in `MM3/src/` → Using branch `svn/MM_3_Final` → Use `MM3/src/MANIFESTO.md`
   - MikkiMUD 3.2 (MM32) Files are in `MM32/src/` → Using branch `svn/MM_3-2_Start` → Use `MM32/src/MANIFESTO.md`
   -- Pull these branches into subfolder that you create under _agent_work/<your worktree name>/
   --- See "parallel safety" #6 below for details.

2. **Load the appropriate MANIFESTO.md:**
   - Read the branch-specific MANIFESTO.md before making changes
   - Follow all coding rules and patterns defined in that file

3. **Respect branch boundaries:**
   - Don't mix MM3 and MM32 code patterns
   - Each branch may have different standards and features

4. **Fix the cause; don’t work around it (avoid masking bugs):**
   - Prefer **ordering/state fixes** that ensure required data is set before it’s used (e.g., set `attack_weapon` when a form is chosen, not later).
   - Avoid “fallbacks” that **change output to look valid** while hiding incorrect engine state (e.g., printing some other weapon/bodypart instead of surfacing the bad state).
   - It is OK to use **data-coverage fallbacks** (e.g., default prose if a DB text slot is missing). That masks missing content, not an engine bug.

5. **When referencing files/paths in agent messages (clickable links in Cursor):**
   - Always use paths **relative to the project root** (this repo root folder), not relative to a sub-repo like `MM32/src/`.
     - Good: `_agent_work/channeling_agent/MM32/src/docs/release/mm32-3.2-tuning-report.md`
     - Bad (ambiguous when multiple agent worktrees exist): `MM32/src/docs/release/mm32-3.2-tuning-report.md`
   - Wrap paths in **inline code** (backticks): `` `relative/path/from/repo/root` ``
   - **Do not** use Markdown link syntax (`[text](path)`) for local files; plain inline paths are what Cursor auto-links reliably.

6. **Parallel-safe workflow (worktrees, ports, PRs):**
   - Follow `docs/agents/parallel-safety.md` (**mandatory**) for:
     - how to create your own `_agent_work/<agent_name>/MM3/{src,lib}` and `_agent_work/<agent_name>/MM32/{src,lib}` worktrees
     - how to pick/register ports (`tmp/agent_ports.tsv`) and stop only your own server PIDs
     - PR-only submission rules (no direct pushes to `svn/MM_3_Final` / `svn/MM_3-2_Start`)
     - PR hygiene: **never** push new commits expecting to “update” a merged/closed PR (open a new PR instead)

---

## Additional Resources

- **Rules System:** See `RULES_INDEX.md` for AI agent rule discovery
- **Agent Protocol:** See `AGENTS.md` for MODE/ACT workflow and rule loading
- **Parallel-safety / worktrees / ports:** See `docs/agents/parallel-safety.md`
- **Design Notes (combat/channeling):** See `Combat_Channeling_Design_Notes/`
- **Design Notes (building/ubermap):** See `Building_Design_Notes/` and `docs/ubermap/`
- **Project docs:** See `docs/`
- **MM3.2 release docs (examples):**
  - `MM32/src/docs/release/mm32-3.2-tuning-report.md`
  - `MM32/src/docs/release/mm32-3.2-tuning-recommendations.md`

---

## Quick Reference

| Branch | Folder | Git Repo | MANIFESTO | Purpose |
|--------|--------|----------|-----------|---------|
| Stable | `MM3/` | `MM3/src/` | `MM3/src/MANIFESTO.md` | Production, bugfixes |
| Dev | `MM32/` | `MM32/src/` | `MM32/src/MANIFESTO.md` | New features, refactoring |
| Web | `public_html/` | `public_html/` | N/A | Website (PHP/Apache) |

