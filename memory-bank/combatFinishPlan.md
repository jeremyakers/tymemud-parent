# MM32 Combat: Finish Plan (grounded in current code + DB)

## Status
- **Status:** Completed (turn-based combat loop is playable; smoke + SIT guardrails green)
- **Last validated:** 2026-01-05

## Current reality (what exists already)
- **Turn-based combat engine**: `MM32/src/turn_based_combat.c` / `.h`
- **Forms are DB-backed**: `form_base`, `form_mods`, `form_*_text`, `form_spec_*` (loaded in `MM32/src/forms.c`)
- **Bodyparts are DB-backed**: `class_bodyparts` → per-player state in `pfiles_bodyparts` / `pfiles_bodydamages` (loaded in `MM32/src/bodyparts.c`)
- **Wounds/bleed exist**: `MM32/src/afflictions.c` (`cut()`, `bruise()`) currently model bloodloss by reducing `GET_HIT` (keep for now).
- **Armor absorbance exists**: `ITEM_ARMOR` uses `value7/value8/value9` for pierce/slash/crush absorbance (OLC already supports it).

## Just-validated DB prerequisites (done)
- **Migration applied in dev DB**: `MM32/src/sql_migrations/2025-12-31_combat_bodyparts_eqslot_skull.sql`
  - Populates `class_bodyparts.eq_slot` (was all 0)
  - Adds missing critical part: `skull` (inside `head`)

## Implementation roadmap (completed)
### Phase 0: Combat stability + log-signal cleanup (completed)
- Fix recurring combat runtime errors observed during smoke runs (see `docs/testing/mm32-combat-log-findings.md`):
  - `executeNormalDefense` / `get_attack_weapon()` emitting `weapons_orientation_ch is NOT SET!!!` during unarmed attacks
  - `random_bodypart` failures (“returned no bodypart” / “Couldn't find a bodypart!”)
- Track and reduce boot-time SYSERR noise that confuses combat debugging (mobprog/spec assigns missing IDs).
- **Deferred (follow-up): creation reconnect correctness**
  - If the server/client session is interrupted during `ED_PCREATE`, a character can reconnect in `CON_PLAYING` with a stale `GET_PROMPT()` (e.g., the temporary “Hit the ENTER key to continue...” creation prompt) and without being routed back into pcreate.
  - For now, **workaround** is to delete/recreate test characters (CombatA/CombatB) cleanly; later fix should resume pcreate or normalize prompt on reconnect.

### Phase 1: Make damage + armor correct (completed)
- Update `MM32/src/fight.c:damage()` / `damage_bodypart()` path to:
  - Determine **damage type** (slash/pierce/crush/unarmed) consistently
  - Apply **typed DR** using armor absorbance per damage type (from worn items covering the struck bodypart)
  - Enforce the design’s **soft cap** (90% reduction max)
- Add debug logging toggles (imm-only) for: raw damage → DR → final damage → wound flags.

### Phase 2: Wound severity + instant-death triggers (completed)
- Ensure bodypart HP + `BODYPART_*` flags map to design severities:
  - Minor / Substantial / Gashed / Severed / Broken
- Add the “critical parts” rules:
  - `skull`, `heart`, `throat` reaching the configured severity thresholds → death checks.
- Keep **single HP pool** for now (per user decision); add TODO for later split:
  - **TODO**: separate Health vs Blood pools.

### Phase 3: Targeting UX (region vs specific) (completed)
- Extend targeting selection so players can choose:
  - **region targeting** (head/arms/torso/legs/feet/hands) or
  - **specific part targeting** (e.g., throat)
- Resolve region → part via weighted roll using `class_bodyparts.body_percent` within that region.

### Phase 4: Readiness + predictability penalty (completed)
- Implement attacker “recent forms” tracking and apply the hit-chance penalty/bonus rules.
- Implement readiness/reaction modifiers (likely via existing `form_mods` readiness slots + per-combatant state in `turn_combat_data`).

### Phase 5: Nostalgia import (MM2 assets) (completed)
- Import iconic MM2 form names/text as data:
  - Reference artifacts: `memory-bank/mm2_forms_dump.csv`, `memory-bank/mm2_forms_strings.txt`
- Import MM2 spell/weave naming as aliases:
  - Reference artifact: `memory-bank/mm2_spell_names.txt`

