# Active Context

## Quick Start (Lines 1-30)

**Current Objective:** Port **MM2 combat forms** (names + metadata + nostalgia
text) into **MM32** as DB-backed forms, then curate/expand with missing WoT
forms and build starter kits / NPC kits on top.

**Next 3 Steps:**

1. Write durable docs for player-facing combat usage + coder-facing combat
   engine navigation.
2. Continue form curation (fill gaps / add missing WoT forms only as needed for
   kits).
3. (Later) Migrate the polished player docs into in-game helpfiles.

**Active Blockers:** None

**Validation Signal:** MM2 forms import is reproducible (script + migration),
forms are usable in smoke tests, and memory-bank stays within size budgets.

**Cross-project note (Ubermap work):** Ubermap MVP world work is happening in the
`MM32/lib` repo and should be done from the isolated worktree:
`/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib` (branch
`agent/ubermap-lib`). Recent PRs:
- `https://github.com/jeremyakers/tymemud-lib/pull/1` (MVP boot blockers + seams)
- `https://github.com/jeremyakers/tymemud-lib/pull/4` (placeholder cleanup in 537/611/670 + seam repairs)

**Cross-project note (Ubermap work — Tar Valon diagonal rotation):**
Tar Valon (city zones `90–98`) has been rotated **45° clockwise** for the overland
“north-star strict” alignment against `Building_Design_Notes/tar-valon-final.svg`.
Current work is being staged in:
`/home/jeremy/cursor/tymemud/_agent_work/tv_diagonal_hole_agent/MM32/lib`

Key invariants:
- Overland “holes” are explicit `!unused` disconnected vnums (reserved for inserts).
- “Ethereal” towns (Darein/Jualdhe/Luagde/Daghain/Osenrein) are *walkable* overland
  placeholder rooms; used overland vnums stay in-grid.

## Current Session

This file is treated as **project-level active context** shared across agents
(not per-agent session notes).

**Cross-project note (Web world editor):** Engine-backed web editor API work is
in `_agent_work/wld_editor_api_agent/` using builderport `9696` (status `9697`).

**Key Invariants / Non-Negotiables:**

- `pfiles_main` single-row SQL operations must include `port` in WHERE clause
  (see `memory-bank/systemPatterns.md`).
- MM3 is stable; MM32 is dev; fixes flow **MM3 → MM32**
  (see `MM3/src/MANIFESTO.md` and `memory-bank/systemPatterns.md`).
- SIT harness/runner/suite layering is designed to minimize merge conflicts
  (see `memory-bank/systemPatterns.md`).
- When refactoring output formatting (e.g., adding `%.100s` truncation)
  **format specifier count must match varargs count** to avoid UB with
  `send_to_charf()`/`vsnprintf`.

## Combat/Channeling reboot thread (2025-12-31 → ongoing)

- **Combat target**: Finish MM32 combat system first (channeling depends on
  combat timing + wounds).
- **MM2 nostalgia input**:
  - Forms binary: `MiT_MM2_Code/src/lib/misc/formdata` (parseable via MM2
    `fight_forms.c`)
  - Extracted dump: `docs/mm2/mm2_forms_dump.csv`
  - Import tooling: `MM32/src/tools/mm2_formdata_extract.py` + generated
    migration `MM32/src/sql_migrations/2026-01-01_mm2_forms_import.sql`
- **Reference doc**: `docs/mm2/nostalgia.md`
- **Player guide (durable docs)**: `docs/combat/player-combat-guide.md`
- **Coder guide (durable docs)**: `docs/combat/engine-guide.md`

**2025-12-31 Additions (ASan / stack-smash work):**
- ASan enabled in Makefiles to catch stack/buffer overflows; note ASan implies
  `-O1`.
- MM32 merge from MM3 involved non-trivial conflict resolution; ensure post-merge
  build + warnings check.
- Wizard command output regression fixes landed in `MM32/src/act.wizard.c`
  (`do_show` / `do_set`) to restore header ordering/visibility.
- Found format-string/varargs mismatch in
  `MM32/src/oedit.c:oedit_disp_extradesc_menu` after `%s%.100s%s` refactor:
  missing `nrm` arguments for the trailing `%s` reset-color specifiers (the “add
  `nrm`” fix was later reverted in working tree; mismatch remains until
  re-applied).

**2025-12-31 Additions (Combat system completion - MM32):**
- Objective: finish MM32 combat system (then channeling) based on
  `Combat_Channeling_Design_Notes/`.
- Decision: reuse existing MM32 `turn_based_combat.c` + `forms.c` +
  `bodyparts.c` implementation; keep current single HP pool for now (TODO later:
  split Health vs Blood pools).
- DB audit (tyme DB): `class_bodyparts` has 77 parts including `throat` +
  `heart` (heart is inside `chest`), but no explicit `skull` row; `eq_slot`
  currently 0 for all bodyparts (armor coverage incomplete).
- Armor data: OLC supports per-type absorbance for `ITEM_ARMOR` via object values
  `value7/value8/value9` (pierce/slash/crush); combat code needs to consume
  these.

## Last Session Summary

See `memory-bank/progress.md` for recent accomplishments (including SIT
refactor commits and dates).
