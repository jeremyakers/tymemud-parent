# MM2 Nostalgia Assets (for reuse in MM32)

## Goals
- Preserve “classic” MM2 feel by reusing **form names/text** and **weave naming/content** where feasible.
- Do this as **data import/mapping**, not by reintroducing the old combat engine.

## What we have (confirmed)
### Forms
- **Binary data file**: `MiT_MM2_Code/src/lib/misc/formdata`
  - Contains embedded strings for many iconic form names (e.g., “Hummingbird Kisses the Honeyrose”, “Boar Rushes Down the Mountain”).
  - The on-disk format is parseable (see MM2 `fight_forms.c:read_form()`).
- **Extracted artifacts**
  - `docs/mm2/mm2_forms_strings.txt`: strings-first list (115 unique candidates)
  - `docs/mm2/mm2_forms_dump.csv`: parsed dump of **all 122** forms (type/time/attack/defense/kind/name/comment/prereqs)

### Weaves
- **Source**: `MiT_MM2_Code/src/weaves.c` + `MiT_MM2_Code/src/weaves.h`
  - Contains spell/skill/talent numbering + the `spells[]` string table and the engine code.

## Proposed reuse strategy (low-risk)
- **Forms**
  - Import iconic names into MM32 `form_base.name` (keeping MM32’s weapon/stance/damage_type model).
  - Recreate (or port) MM2 “flavor text” into MM32 `form_*_text` tables (initial/unblocked/defend/critfail) where it fits.
  - Keep a mapping layer so we can trace provenance: `mm2_source_name → mm32_form_id`.
- **Implementation doc**: `docs/mm2/forms-import.md`
- **Weaves**
  - Reuse **weave/spell names** as player-facing aliases where possible, without changing MM32’s mechanics until combat is stable.

## Next extraction steps (when we implement)
- Parse `MiT_MM2_Code/src/weaves.c` to extract:
  - `spells[]` names
  - per-spell metadata if present in `weave_info[]` initialization
- Decide whether to port any of MM2’s “weave UX” (targeting verbs, messages) separately from mechanics.

