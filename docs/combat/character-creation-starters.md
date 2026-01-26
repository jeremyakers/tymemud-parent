# MM32 Character Creation Starters (Forms + Equipment)

This is a durable guide for maintaining what new characters start with:

- **Starter combat forms** (from `newbie_forms`)
- **Starter equipment** (from `eq_set_groups` / `eq_set_objs`)

The goal is simple: if a player chooses a weapon specialization, they should
start with **both**:

- usable forms for that weapon family, and
- a matching weapon in their starter equipment set

## Where the behavior lives (code)

New player creation is implemented in `MM32/src/pcreate.c`.

Key fields used during creation:

- **Weapon specialization**: `desc->edit_mode`
  - This value is used as `newbie_forms.weapon_type`.
- **Equipment set**: `desc->mailtype`
  - This value is used as `eq_set_groups.id` / `eq_set_objs.id`.

## Starter forms: `newbie_forms`

When a new character finishes creation, the code loads forms via:

- `SELECT form_id, learned FROM newbie_forms WHERE weapon_type = <edit_mode>`

Migration files that define weapon-family starter kits:

- `MM32/src/sql_migrations/2026-01-01_newbie_forms_mm2_starter_kits.sql`
- `MM32/src/sql_migrations/2026-01-02_newbie_forms_more_weapon_kits.sql`

If a new weapon family feels “unplayable”, the first question is:

- does that `weapon_type` have at least **2 attacks + 2 defenses + 1 tempo**
  form in `newbie_forms`?

## Starter equipment: `eq_set_groups` + `eq_set_objs`

At the end of creation, the code equips a newbie by loading vnums via:

- `SELECT vnum FROM eq_set_objs WHERE id = <mailtype> AND gender = <SEX_*>`

Tables:

- `eq_set_groups(id, gender, name)` — lists available starter sets in creation
- `eq_set_objs(id, gender, vnum)` — the object prototypes to give/equip

### Weapon-matching starter equipment sets

We add weapon-matching starter sets by copying the baseline set (id=1) and then
adding a weapon vnum.

Migration:

- `MM32/src/sql_migrations/2026-01-02_eq_set_weapon_specialization_starters.sql`

Starter set IDs provided by that migration:

- **8005**: Starter Staff
- **8006**: Starter Dagger
- **8008**: Starter Axe
- **8017**: Starter Mace

Weapon vnums used (stable indexed prototypes in `MM32/lib/world/obj/37.obj`):

- **3747**: walking staff (WEAPON_STAFF=5)
- **3713**: dagger (WEAPON_DAGGER=6)
- **3786**: wood axe (WEAPON_AXE=8)
- **3725**: large wooden club (WEAPON_MACE=17)

## Choosing vnums safely (content rules)

Use a weapon that is:

- present in the local content repo (`MM32/lib/world/obj/*.obj`)
- `ITEM_WEAPON` type
- has `value[10]` set to the correct `WEAPON_*` constant

If you need to find candidates, you can:

- search `MM32/lib/world/obj/` for the item name (or vnum)
- prefer low-risk, generic items (training/practice weapons, simple weapons)

## Applying changes (developer workflow)

1. Apply SQL migrations to the dev DB (idempotent).
2. Smoke test:
   - `cd MM32/src/tests && ./combat_smoke.sh`
3. If adding a new starter weapon family, add a smoke scenario that:
   - equips a matching weapon vnum
   - sets at least one appropriate form
   - executes the matching command (`slash`/`thrust`/`unarmed`)
   - asserts a strong log signal (equip text or form text)

## Common failure modes

### Newbie knows forms but can’t use them

Symptoms:

- `No appropriate forms found: No valid forms found for class ...`

Likely causes:

- starter equipment does not include a matching weapon for the specialization
- the weapon’s `value[10]` is wrong (mis-typed weapon family)
- form weapon masks are too restrictive for the weapon family

### Newbie has weapon but gets weapon-required runtime errors

Likely cause:

- a form was misconfigured in `form_base` (weapon requirements/orientation).
  Fix with an idempotent SQL migration rather than suppressing errors.
