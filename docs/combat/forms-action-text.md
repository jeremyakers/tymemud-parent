# Combat form action text (MM32)

## Goals
- Ensure combat always has action text coverage.
- Keep the best “nostalgia payload” from MM2: **the form names themselves**.
- Avoid clobbering curated prose: migrations should be **idempotent** and only fill/upgrade where safe.

## Current policy (as of 2026-01-07)
- **DB stores curated prose** (unique, lore-faithful), not “generic templates”.
- **Code keeps fallbacks** for safety, but the long-term goal is: **no fallback usage for non-exotic forms**.
- **Scope for full curation**: all **non-exotic** forms (`(form_base.flags & FORM_EXOTIC)==0`).

## How MM32 stores form text
MM32 persists form action text in DB tables and loads them at boot/reload into in-memory matrices:

- `form_initial_text(form, act_num, aggressiveness, text)`
- `form_critfail_text(form, act_num, fail_num, text)`
- `form_unblocked_text(form, act_num, followthru, text)` (attack forms only)
- `form_defend_text(form, act_num, complete, followthru, text)` (defense forms only)

At runtime, combat prints these via `bpact()`:
- `print_form_initial()` / `print_form_hit()` / `print_form_partial_defend()` in `MM32/src/act.offensive.c`

## Form type semantics (engine invariant)
Per `docs/combat/engine-guide.md`:
- `0`: dodge (defense)
- `1`: block/parry (defense)
- `2`: attack / counterattack (damage-dealing)
- `3`: flourish / tempo (non-damaging)
- `4`: recovery (non-damaging)

**Only**:
- `form_type == 2` uses `form_unblocked_text`
- `form_type < 2` uses `form_defend_text`

## Current migrations
- **Cleanup**: remove generated/generic templates so code-level fallback is used
  - `MM32/src/sql_migrations/2026-01-05_form_text_remove_generated_templates.sql`
  - `MM32/src/sql_migrations/2026-01-05_form_text_remove_generated_templates_v3_defend_unblocked.sql`
  - `MM32/src/sql_migrations/2026-01-06_form_text_remove_generated_templates_v4_unblocked.sql`
  - `MM32/src/sql_migrations/2026-01-06_form_text_remove_generated_templates_v5_critfail.sql`
- **Curated pack (newbie kits)**: unique descriptive prose for starter forms
  - `MM32/src/sql_migrations/2026-01-05_form_text_newbie_kits_unique_v1.sql`
- **Curated pack (defend/unblocked v1)**: high-visibility per-form overrides (UPSERT, update-only-if-empty)
  - `MM32/src/sql_migrations/2026-01-05_form_text_curated_defend_v1.sql`
  - `MM32/src/sql_migrations/2026-01-06_form_text_curated_defend_v2.sql`
  - `MM32/src/sql_migrations/2026-01-05_form_text_curated_unblocked_v1.sql`
  - `MM32/src/sql_migrations/2026-01-06_form_text_curated_unblocked_v2.sql`
- **Curated pack (critfail v3)**: unique per-form critical failure prose (UPSERT, update-only-if-empty)
  - `MM32/src/sql_migrations/2026-01-06_form_text_curated_critfail_v3.sql`
- **Audit (read-only)**: report missing/blank slots per form
  - `MM32/src/sql_migrations/2026-01-04_form_text_audit_missing_slots.sql`

These are applied by the smoke harness:
- `MM32/src/tests/combat_smoke.sh` → `ensure_smoke_migrations()`

## Prose rules (enforceable)

### POV and token usage
- **act_num meanings**:
  - `0`: to_room (others see)
  - `1`: to_char (actor sees) → must read naturally as “you”
  - `2`: to_vict (victim sees)
- **Required**: always use `$n`/`$N`/`$s`/`$m`/`$e` (etc.) and avoid hardcoding names.
- **Required**: use `$g/$h/$G/$H` for third-person verb suffixes when the same verb must read correctly for both observer/victim lines.
  - `$g` → `s` (3rd person) / `` (1st/2nd)
  - `$h` → `es` (3rd person) / `` (1st/2nd)

### “High prose” tone constraints
- **Keep the form name prominent**: the reader should always notice the named form being executed.
- **No bland placeholders**: avoid lines that read like mechanical templates (“slips through cleanly”, “crashes through”, “turns aside the blow”) unless they are uniquely elaborated per form.
- **Combat clarity beats poetry**: prose may be flavorful, but must still communicate what happened (attack/defense/critfail, and relative intensity via followthru/aggressiveness).
- **No anachronisms**: avoid modern slang/idioms; keep Wheel-of-Time-ish voice.

### Slot semantics reminders
- `form_initial_text`: telegraph intent + stance/tempo; aggressiveness should change tone.
- `form_unblocked_text`: describe the strike landing; followthru should change intensity.
- `form_defend_text`: describe partial vs complete defense; followthru should change decisiveness.
- `form_critfail_text`: describe a believable failure for the weapon family (unarmed should never “drop your weapon”).

## Safe editing rules
- Prefer **adding new migrations** over editing old ones when changing already-applied text.
- If updating existing rows, restrict updates to:
  - rows that are empty, or
  - rows that match the known generated template patterns (LIKE/REPLACE), so we do not overwrite curated prose.
- Prefer `$n/$N/$f` + `$g/$h/$G/$H` over hardcoded "You ..." variants when writing reusable prose.

## Open work (planned)
- Continue iterating `form_critfail_text` and `form_unblocked_text` for richer WoT tone (keeping pattern-matched safety).
- Use the audit SQL to spot any remaining blank slots after adding new forms or importing additional sets.

