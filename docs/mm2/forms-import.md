# MM2 → MM32 Forms Import (Nostalgia Port)

## Goal
Preserve the **MM2 combat “feel”** by importing MM2 form names + notes into MM32’s DB-backed forms system, without reintroducing the MM2 combat engine.

## Source of Truth (MM2)
- **Binary form database**: `MiT_MM2_Code/src/lib/misc/formdata`
- **Reference loader/parser**: `MiT_MM2_Code/src/fight_forms.c`
  - `boot_forms()` reads the file header
  - `read_form()` reads each record (fixed struct + variable-length strings + arrays)

## MM32 Import Pipeline

### 1) Deterministic extraction
Tool:
- `MM32/src/tools/mm2_formdata_extract.py`

Outputs:
- `docs/mm2/mm2_forms_dump.csv` (122 forms; stable order)
- `MM32/src/sql_migrations/2026-01-01_mm2_forms_import.sql` (idempotent)
- `MM32/src/sql_migrations/2026-01-01_mm2_forms_deduplicate.sql` (cleanup: remove name collisions)

### 2) Import policy
- **Import ALL MM2 forms**.
- **Mark obvious dev/joke forms as EXOTIC** so they are not auto-set:
  - `Newbie hits the fan`
  - `Going to the shop`

### 3) Initial MM2 → MM32 mapping (best-effort)
MM2 types → MM32 `form_type`:
- **OFF** → `attack` (2)
- **DEF** → `block` (1) (stored as `class_name='parry'`)
- **CNT** → `flourish` (3)
- **DOD** → `dodge` (0)

Weapon legality:
- Derived from MM2 `kind` where possible; otherwise permissive fallback during the initial import.

Combat text:
- **MM2 does not store a full “message matrix” per form in `formdata`.**
  - The on-disk record contains **name**, **comment**, and numeric effectiveness/prereq data (see `read_form()` in `MiT_MM2_Code/src/fight_forms.c`).
  - In MM2, much of the “feel” comes from **runtime templates** that combine the chosen form names plus the shared intensity ladder (`dam_strings[]`).
- In MM32 we *must* persist per-slot text in DB tables, so we generate/bake:
  - baseline `form_initial_text` that includes the **form name** (nostalgia payload)
  - MM2 `comment` preserved as an imm-visible entry in `form_critfail_text` (provenance note)
  - plus backfilled text for all other required slots to avoid empty placeholders being treated as intentional.

## IDs / Provenance
- Imported MM2 forms are assigned IDs starting at **6000**, sequential by extraction order.
- MM2’s `form_data.id` (from the binary) is stored in `form_base.id_secondary` for traceability.

## Quality fixes (MM32)
- We apply an idempotent grammar fix migration for known 2nd-person template issues:
  - `MM32/src/sql_migrations/2026-01-04_form_initial_text_grammar_fix.sql`
  - Example fixed pattern: `"You form <X> and slashes/lunges/strikes at $N."` → `"You form <X> and slash/lunge/strike at $N."`

## Next steps
1. Curate/upgrade the best known MM2 WoT forms to richer MM32 text (unblocked/defend/critfail).
2. Add missing WoT forms not present in MM2.
3. Build starter kits for players + archetype kits for NPCs using the expanded library.

