# Technical Context

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | C (GNU11/C11) |
| Compiler | GCC |
| Database | MySQL/MariaDB |
| Engine Base | MikkiMud / CircleMUD |

## Essential Commands

### Git Operations
```bash
# MM3 (stable) operations
cd MM3/src
git commit -m "fix(scope): description"
git push origin svn/MM_3_Final

# MM32 (dev) operations  
cd MM32/src
git merge origin/svn/MM_3_Final
git push origin svn/MM_3-2_Start
```

### SIT (Python) - recommended usage
```bash
# MM3
cd MM3/src/tests
python3 test_comprehensive_sit.py
python3 test_comprehensive_sit.py --test comm_c_buffer_safety

# MM32
cd MM32/src/tests
python3 test_comprehensive_sit.py
python3 test_comprehensive_sit.py --test mm32_format_truncation_refactor

# Recommended for long-running telnet SIT runs (force unbuffered output + higher overall timeout)
python3 -u test_comprehensive_sit.py --test mm32_format_truncation_refactor --timeout 900
```

## Manual-first smoke testing (MM32 combat)
- **Primary entrypoint**: `MM32/src/tests/combat_smoke.sh`
- **Underlying tools**: `MM32/src/tests/mud_client.py` + `MM32/src/tests/mud_client_helper.sh`
- **Pattern**:
  - Use **`testimp`** for imm/admin setup only (`transfer`, `purge`, `load mob`, `setform`, `advance`).
  - Use dedicated mortal **combat smoke chars** (`combatA`, `combatB`) for actual combat commands.
- **Important prompt behavior**:
  - The game frequently pauses output with **“Hit the ENTER key to continue...”** / **“*** PRESS RETURN”** prompts; send an **empty line** to advance.
  - Character creation uses the `pcreate` flow; use **`done`** at the creation prompt to finish quickly.
- **Log artifacts**: copied into `MM32/src/tests/test_logs/combat_smoke_YYYYMMDD_HHMMSS/`
- **Key smoke signals**:
  - `Calling damage_line_bodyparts` (damage pipeline ran)
  - `bleeds` (wound/affliction output)
- **Doc**: `docs/testing/mm32-combat-smoke-testing.md`

## MM2 nostalgia: forms import tooling (MM32)
- **Extractor**: `MM32/src/tools/mm2_formdata_extract.py`
- **Source**: `MiT_MM2_Code/src/lib/misc/formdata` (parsed using MM2 `fight_forms.c` layout)
- **Outputs**:
  - `docs/mm2/mm2_forms_dump.csv`
  - `MM32/src/sql_migrations/2026-01-01_mm2_forms_import.sql`
  - `MM32/src/sql_migrations/2026-01-01_mm2_forms_deduplicate.sql`

### Build System
- Makefile in `src/` directory
- Build: `make` or `make default`
- Tests: `make test`
- Clean: `make clean`

## Debugging: AddressSanitizer (ASan) (2025-12-31)
**Decision:** Keep ASan enabled until the stack-smash crash is found.

**Build flags (C):**
- CFLAGS: `-g -O1 -fsanitize=address -fno-omit-frame-pointer`
- Link: `-fsanitize=address`

**Gotcha:** Enabling `-O1` (often required/used with ASan) can surface `-Wformat-truncation` warnings that do not appear under `-O0`.

## SIT Architecture (to avoid merge conflicts)
- Shared plumbing (should be identical in MM3/MM32):
  - `tests/mud_sit_harness.py`
  - `tests/mud_sit_runner.py`
  - `tests/sit_suite_base.py` (MM3-owned base suite)
- MM32-only:
  - `MM32/src/tests/sit_suite_mm32.py` (overrides/extensions)

## SIT Suite Rules (stable IDs + overrides)
- Base suite is a mapping keyed by stable IDs (snake_case).
- MM32 overrides by reusing the same key and replacing the `TestSpec`.
- MM32-only tests use `mm32_` prefix IDs.

## Database Patterns
- Use `sqlQuery()` for SQL operations
- Always include `port` column in pfiles_main WHERE clauses
- Check for NULL results before accessing

## Key Files
- `interpreter.c` - Command parsing and execution
- `sqlcharsave.c` - Database character persistence
- `structs.h` - Core data structures
- `MANIFESTO.md` - Branch-specific coding rules
