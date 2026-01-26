# Database Context (Combat/Channeling)

## Quick Start
- **Primary goal (MM32 combat)**: Use DB-backed `class_bodyparts` + `form_base` + existing object value fields to finish combat without schema rewrites.
- **How to re-query**: Use `MM32/lib/mysql-interface.conf` and a `--defaults-extra-file` temp cnf (avoid passwords in CLI history).

## Connection
- **Config file**: `MM32/lib/mysql-interface.conf` (5 lines: host/user/pass/db/port)
- Do **not** paste credentials into logs/commands; prefer a temp cnf file.

## Core Tables (confirmed present in DB)

### Combat bodyparts
- **`class_bodyparts`** (source of truth for bodypart definitions)
  - Loaded by: `MM32/src/bodyparts.c:sql_load_bodyparts()`
  - Columns (high-signal):
    - **Identity**: `id` (PK), `name` (UNIQUE)
    - **Topology**: `babove`, `bbelow`, `bright`, `bleft`, `bfront`, `bbehind`, `inside`
    - **Targeting weights**: `region`, `body_percent`, `x/y/z`
    - **Wounds tuning**: `bloodloss_*`, `injury_*`, broken/severed messages + timers
  - **Current DB findings (2025-12-31)**:
    - **Count**: 78 parts (after migration)
    - **Critical parts present**: `throat`, `heart`, `skull`
      - `heart` is inside `chest`
      - `skull` is inside `head`
    - **Region IDs in use**: 1..6 (head, arms, torso, legs, feet, hands)
    - **Adjacency integrity**: no missing foreign references in adjacency columns
    - **Body percent sum**: 97.83 (not 100; likely “incomplete but usable”)
    - **Eq-slot**: populated via migration so armor coverage can work
    - **Multipliers/messages**: many rows currently default to 1/0 with empty messages (needs tuning)
- **Migration (re-apply safe)**:
  - `MM32/src/sql_migrations/2025-12-31_combat_bodyparts_eqslot_skull.sql`
    - Populates `class_bodyparts.eq_slot`
    - Inserts `skull` (idempotent; requires `head` to exist)
- **`pfiles_bodyparts` / `pfiles_bodydamages`**
  - Used for per-player bodypart HP and stored wound/affliction state.

### Combat forms
- **`form_base`** (base form definitions; includes `damage_type`, `endurance_cost`, `attack_direction`, `bodypart_regions`)
- **`form_*_text`**: `form_initial_text`, `form_unblocked_text`, `form_defend_text`, `form_critfail_text`
- **`form_mods`**: form modifiers array population (includes readiness slots)
- **`form_spec_procs` / `form_spec_conds`**: form special procedure hooks
- **`combat_forms` / `pfiles_forms` / `newbie_forms`**: learned/enabled forms state

### Objects / armor values
- **`pfiles_objects`** (saved objects include `value1..value14`)
- **Per-damage-type armor absorbance exists in item values** (no schema change needed):
  - `ITEM_ARMOR` uses **`value7/value8/value9`** as absorbance vs **pierce/slash/crush** (0-100), per `MM32/src/oedit.c`
  - MM32 combat should apply typed absorbance with a **90% soft cap** (design doc)

## How to re-run the key audits (safe pattern)
1. Create temp cnf:
   - `mktemp` → chmod 600 → write `[client] host/user/password/port/database`
2. Schema:
   - `mysql --defaults-extra-file="$TMP" -e "DESCRIBE class_bodyparts"`
   - `mysql --defaults-extra-file="$TMP" -e "DESCRIBE form_base"`
3. Critical part lookup:
   - `SELECT id,name,region,body_percent,inside FROM class_bodyparts WHERE LOWER(name) REGEXP 'skull|heart|throat|neck|head'`
4. Adjacency sanity:
   - LEFT JOIN each adjacency column to ensure referenced IDs exist

## Nostalgia source pointers (MM2)
- Old MM2 forms live in `MiT_MM2_Code/src/lib/misc/formdata` (binary) and contain classic form names as embedded strings.
- Old MM2 weaves live in `MiT_MM2_Code/src/weaves.c` (string tables + engine).

