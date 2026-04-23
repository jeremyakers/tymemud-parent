# A Moment in Tyme (WoT MUD)

## Project Overview

**Name:** A Moment in Tyme  
**Genre:** Wheel of Time (WoT) themed Multi-User Dungeon (MUD)  
**Engine:** Based on MikkiMud / CircleMUD (C-based)  
**Language:** C (GNU11/C11 standard)  
**Database:** MySQL/MariaDB with SQL-based character persistence

---

## Repository Structure

~/tymemud is a meta repo! There are multiple repos! Make sure you're looking in the right folder.
Each workspace contains three to four (3-4) separate git repositories:

### DO NOT WORK OUTSIDE YOUR OWN WORKTREES
### DO NOT EDIT FILES UNDER _human_work - YOU MAY USE THIS AS THE BASIS FOR CREATING YOUR OWN WORKTREE

### Git Repository Structure

- **`_agent_work/<your_worktree>/MM3/src/`** - Local git repository tracking branch `svn/MM_3_Final` (stable/production MUD code)
- **`_agent_work/<your_worktree_parent>/MM32/src/`** - Local git repository tracking branch `svn/MM_3-2_Start` (development MUD code)
- **`_agent_work/<your_worktree_parent>/public_html/`** - Local git repository for the website (PHP/Apache assets)

The MUD source (src) repositories connect to the same remote: `jeremyakers/tymemud-src.git`  
The website (public_html) repository connects to: `jeremyakers/tymemud-web.git`

**Important:** All git operations (commit, push, merge) must be run from within the relevant repo directory AFTER YOU COPY TO YOUR OWN WORKTREE:
- `cd MM3/src` for stable MUD branch operations
- `cd MM32/src` for dev MUD branch operations
- `cd public_html` for website operations

**Important** Depending on what you're working on: Create your own sub-branch within MM3/src, MM32/src, MM32/lib, and/or public_html
- Then create pull requests as needed to pull those branches into MM3 or MM32, builderport or public_html as required.
---

## Branch-Specific Documentation

**Each branch has its own MANIFESTO.md with branch-specific coding rules and guidelines:**

### For MM3 (Stable Branch) Work:
- **Location:** `MM3/src/MANIFESTO.md`
- **Use when:** Working on bugfixes, hotfixes, or production-critical features
- **Branch:** `svn/MM_3_Final`
- **Process** Create your own sub-branch for every feature/bugfix. Then submit PR to merge into svn/MM_3_Final

### For MM32 (Development Branch) Work:
- **Location:** `MM32/src/MANIFESTO.md`
- **Use when:** Working on new features, major refactoring, or experimental code
- **Branch:** `svn/MM_3-2_Start`

---

## Workflow Rules

**The rule is: Fix in Stable, Merge to Dev.**

1. **Bugfixes and hotfixes** → Implement in YOUR COPY and YOUR BRANCH of `MM3/src/` first
2. **New features and refactoring** → Implement in YOUR COPY and YOUR BRANCH of `MM32/src/`
3. **Merging:** Use `MM32/src/merge-mm32` script to bring stable fixes from MM3 into MM32
4. **Never merge from MM32 to MM3** - The flow is always MM3 → MM32

### lib workflow (world data repo)

The world data (`lib/`) is a **separate repository** (Which must also be copied to your worktree) and follows a stricter promotion flow:

1. **All lib changes land in `builder` first**
2. Deploy/test on the **builderport** server
3. After validation, merge **`builder` → `main`**

This is intentional so builders can safely validate world/command table changes before they hit production.

---

## AI Agent Instructions

**When working on code in this project:**

1. **Choose the correct repo/worktree first:**
   - MikkiMUD 3.0 (MM3) work belongs in `MM3/src/` on branch `svn/MM_3_Final`
   - MikkiMUD 3.2 (MM32) work belongs in `MM32/src/` on branch `svn/MM_3-2_Start`
   - Create and use your own isolated worktree under `_agent_work/<agent_name>/...`

2. **Load the correct branch-specific manifesto:**
   - `MM3/src/MANIFESTO.md` for MM3 work
   - `MM32/src/MANIFESTO.md` for MM32 work

3. **Use the canonical agent docs instead of relying on duplicate summaries here:**
   - Bootstrap / response protocol: `AGENTS.md`
   - Parallel-safe workflow: `docs/agents/parallel-safety.md`
   - Detailed grepai guidance: project skill `grepai-usage`
   - MCP/tooling guidance: `docs/agents/mcp-tooling.md`

4. **Respect branch and repo boundaries:**
   - Do not mix MM3 and MM32 code patterns
   - Use paths relative to the project root when referencing local files in agent messages

---

## Additional Resources

- **Rules System:** See `RULES_INDEX.md` for AI agent rule discovery
- **Agent Protocol:** See `AGENTS.md` for MODE/ACT workflow and rule loading
- **Parallel-safety / worktrees / ports:** See `docs/agents/parallel-safety.md` (ALWAYS REQUIRED)
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
