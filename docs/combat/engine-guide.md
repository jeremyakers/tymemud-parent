# MM32 Turn-Based Combat Engine Guide (Coders)

This is a durable guide to the MM32 turn-based combat engine:
**where state lives**, **what functions do**, and **how to debug/test changes**
safely.

## Where the combat engine lives

- **Core turn-based engine**: `MM32/src/turn_based_combat.c`
- **Form skill and form command list**: `MM32/src/act.offensive.c`
- **Forms DB + OLC plumbing**: `MM32/src/forms.c`, `MM32/src/forms.h`
- **Bodyparts system**: `MM32/src/bodyparts.c`, `MM32/src/bodyparts.h`
- **Damage pipeline (authoritative armor absorbance)**: `MM32/src/fight.c`

## High-level call flow (manual commands)

Most player combat commands are `do_combat` with a different subcmd:

1. `do_combat(ch, argument, cmd, subcmd)` parses:
   - target (victim)
   - optional aim token (region/bodypart)
   - pass/defense/attack routing
2. `get_appropriate_form()` selects a usable form for the command class
   (slash/thrust/unarmed/etc.)
3. `setupBattle()` allocates and initializes `turn_combat_data` if this is a new
   fight
4. `turnAttack(ch, vict, form, feint, aimed_part)` sets up the attacker’s move
5. When the defender responds (or autocombat resolves it), the engine runs:
   - `executeNormalHit()` (attack resolution path)
   - `executeNormalDefense()` (attack vs defense / counterattack resolution path)

## Targeting UX (region vs. bodypart)

### Parsing rules (in `do_combat`)

For non-specific commands, the parser supports:

- `<command> <target> <aim>`
- `<command> <aim> <target>`

The aim token is resolved **after** a form is selected, via
`combat_pick_targetpart()` (which delegates to bodypart helpers).

### Resolution rules

- If `aim_token` resolves to a valid bodypart, the engine passes it down to
  `turnAttack()` and the hit logic uses that bodypart instead of
  `random_bodypart()`.
- If it cannot be resolved, the command fails cleanly (no attack is executed).

## Readiness and Predictability

These mechanics were added to support the “B: longer, tactical fights” preference.

### State storage

State is stored on `struct char_data` (see `MM32/src/structs.h`):

- `combat_readiness` (int): 0..100, baseline 50
- `combat_predict_last_key` (unsigned long): hash of last used command class
  (case-insensitive djb2 of `form_data->class_name`)
- `combat_predict_streak` (int): repeat streak counter

### When state resets

- On new battle creation: `setupBattle()` sets readiness to 50 and
  predictability to neutral.
- On combat end: `stopFighting()` returns those fields to neutral values.

### When state updates

Current update points are:

- `doPass()` increases readiness (bigger bump for “true pass”)
- `executeNormalDefense()` updates:
  - attacker readiness down (attack costs tempo)
  - defender readiness up/down depending on whether they were hit
  - predictability streaks based on repeating the same command class
  - player-facing warning for predictability when streak is high enough

### How state affects resolution (effective form skill)

`get_mod_form_skill()` in `MM32/src/act.offensive.c` computes:

`effective_skill = base_form_skill * injury_mod * endurance_mod * blood_mod *`
`readiness_mod * predictability_mod`

Where:

- `readiness_mod = 1.0 + (readiness - 50)/500.0` (≈ ±10% range)
- `predictability_mod = 1.0 - 0.05*min(streak, 6)` (caps at 30% penalty)

Important behavior detail:

- Predictability is keyed by `form_data->class_name`, not by form ID, so
  variants within a class still count as repeating the same command type.

## Bruises: aggregation + readiness impact (anti-spam)

Historically, bruise afflictions printed a “bleeds from bruises …” line for
**every damage entry** on a bodypart, **every round**, which produced a lot of
duplicate-looking output and overstated actual blood loss.

Current behavior:

- Bruises are treated as **pain/impairment**, primarily reducing
  `ch->combat_readiness`.
- Bruise “hurt” processing is **aggregated per body region per update** using
  `struct bruise_hurt_agg` (declared in `MM32/src/afflictions.h`).
- `updateAfflictions()` in `MM32/src/turn_based_combat.c` creates an instance of
  the aggregator, passes it as the `args` pointer to `BP_HURT`, and applies a
  single readiness update per region (with debug-only per-region output under
  `combat debug`).

## Runtime-error philosophy

Combat runtime errors should be **logged**, not suppressed. The codebase uses:

- `syserr()` for critical/invalid state reporting
- guardrails to avoid crashing the server (bail out instead of abort)

Examples of “invalid state” cases that are logged:

- weapon-typed damage attempted with no weapon
- missing bodypart target (`NULL part`)
- missing form pointers

## Debugging knobs

### combat debug flag

There is a player preference flag used for combat debug logging:

- `PRF2_COMBATDEBUG` (see `MM32/src/structs.h`)
- toggled via `combat debug` command (MM32-only)

### Practical debug workflow

1. Run a smoke test (fast):
   - `cd MM32/src/tests && ./combat_smoke.sh`
2. Run SIT tests (slower, more comprehensive):
   - `cd MM32/src/tests && python3 -u test_comprehensive_sit.py --test targeting`
     `--timeout 300`
   - `cd MM32/src/tests && python3 -u test_comprehensive_sit.py --test predictability`
     `--timeout 300`
3. Review logs:
   - smoke logs: `MM32/src/tests/test_logs/combat_smoke_*/`
   - SIT logs: `MM32/src/tests/test_logs/test_run_*.log`

## Known sharp edges (current)

- `get_mod_form_skill()` debug output is **imm-only** and gated behind
  `combat debug` (`PRF2_COMBATDEBUG`). Do not reintroduce room-wide spam
  (`send_to_room`) in any skill hot path.
- The SIT runner uses an in-game `shutdown`, which may trigger a reboot message
  instead of cleanly terminating the OS process. The harness now **terminates the
  server process it started** if needed, so reruns don't collide.

## New character starters (weapon choice, forms, equipment)

Character creation has **two independent starter selections**:

- **Weapon specialization** (what combat command families you start with)
  - Stored in `desc->edit_mode`
  - Used by `MM32/src/pcreate.c` to load forms from:
    - `newbie_forms(weapon_type, form_id, learned)`
  - `weapon_type` uses `WEAPON_*` constants from `MM32/src/structs.h`.
  - `weapon_types[]` is indexed such that **index == `WEAPON_*`** (see
    `MM32/src/fight.c`), which is why `edit_mode` works as the DB key.

- **Starter equipment set** (what physical items you start with)
  - Stored in `desc->mailtype` (historical reuse)
  - Used by `MM32/src/pcreate.c` to load items from:
    - `eq_set_groups(id, gender, name)`
    - `eq_set_objs(id, gender, vnum)`

These are intentionally separate: you can pick a weapon specialization and
still choose a different “outfit” set.

### Maintaining starter sets

For the current development environment we provide weapon-matching starter
equipment sets via SQL migration:

- `MM32/src/sql_migrations/2026-01-02_eq_set_weapon_specialization_starters.sql`

See `docs/combat/character-creation-starters.md` for the full maintenance
workflow and vnum selection guidance.
