# MM32 Combat Forms Audit (Playability / Weapon Coverage)

This is a **snapshot** intended to answer:

- If a player specializes in a weapon, do they have a complete, fun, tactical
  kit?

## Key findings (current DB state)

- **Form commands (classes) currently supported** (from `MM32/src/act.offensive.c:class_list`):
  - `slash`, `thrust`, `parry`, `dodge`, `unarmed`, `flourish`
  - There is **no explicit `crush` command**; blunt weapons may need to be
    represented via existing classes (likely `unarmed`), or we add a new class
    (design decision).

## Starter kit coverage (`newbie_forms`)

`newbie_forms` is now weapon-specific (kit contents vary by `weapon_type`).

See:

- `MM32/src/sql_migrations/2026-01-01_newbie_forms_mm2_starter_kits.sql`
- `MM32/src/sql_migrations/2026-01-02_generic_forms_expand_weapon_masks.sql`
- `MM32/src/sql_migrations/2026-01-02_newbie_forms_more_weapon_kits.sql`

## NPC playability

- Mob form loading is already supported via `parse_mob_forms()` from mob prototypes.
- Example fix applied: `MM32/lib/world/mob/0.mob` bandit vnum `#2` now has
  `Forms: 90 89` (Ram + Withdraw), which prevents “mob knows no defense forms”
  and makes PvE actually interactive.

## Next content work (to make it “B: tactical + longer fights”)

- Define baseline kits **per weapon type** (at minimum: one attack + one
  defense + one recovery/tempo tool where applicable).
- Ensure common NPCs have at least 1 attack + 1 defense form appropriate to
  their equipment (or unarmed kit).

## Starter kit coverage (newbie_forms)

- Starter kits exist for:
  - Sword (`WEAPON_SWORD=1`)
  - Spear (`WEAPON_SPEAR=4`)
  - Unarmed (`WEAPON_UNARMED=19`)
- Extended starter kits (MM2-nostalgia baseline) now also exist for:
  - Staff (`WEAPON_STAFF=5`)
  - Dagger (`WEAPON_DAGGER=6`)
  - Axe (`WEAPON_AXE=8`)
  - Flail (`WEAPON_FLAIL=11`)
  - Polearm (`WEAPON_POLEARM=12`)
  - Mace (`WEAPON_MACE=17`)

See:

- `MM32/src/sql_migrations/2026-01-01_newbie_forms_mm2_starter_kits.sql`
- `MM32/src/sql_migrations/2026-01-02_generic_forms_expand_weapon_masks.sql`
- `MM32/src/sql_migrations/2026-01-02_newbie_forms_more_weapon_kits.sql`

## Starter equipment sets (eq_set_*)

New characters receive equipment based on the selected **equipment set** in
creation (`pcreate` stores it in `desc->mailtype`).

To ensure weapon-specialized newbies can actually use their starter forms, we
also provide weapon-matching starter equipment sets (baseline gear + a matching
weapon):

- `MM32/src/sql_migrations/2026-01-02_eq_set_weapon_specialization_starters.sql`

See `docs/combat/character-creation-starters.md` for the workflow and vnums.
