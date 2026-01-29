# System Patterns

## SQL Database Patterns

### pfiles_main Table Operations (CRITICAL)

**Table Schema:**
- Unique key: Composite of `(name, port)` OR `(idnum, port)`
- Port column is REQUIRED for all single-row operations

**Pattern Rule:**
ALL SQL queries against `pfiles_main` that are supposed to affect a single row MUST include the `port` column in the WHERE clause.

**Required Patterns:**
1. **DELETE operations:** `DELETE FROM pfiles_main WHERE name = '%s' AND port = %d`
2. **UPDATE operations:** `UPDATE pfiles_main SET ... WHERE idnum = %ld AND port = %d`
3. **SELECT single row:** `SELECT ... FROM pfiles_main WHERE name = '%s' AND port = %d`

**Anti-Pattern (CRITICAL BUG):**
```c
// WRONG - Deletes ALL rows with matching name across all ports
sqlQuery("DELETE FROM pfiles_main WHERE name = '%s'", name);
```

**Correct Pattern:**
```c
// CORRECT - Only affects current port
sqlQuery("DELETE FROM pfiles_main WHERE name = '%s' AND port = %d", name, port_number);
```

**Location of Fix:**
- `MM3/src/interpreter.c:1691` - Fixed DELETE query in character creation
- All other queries in codebase verified to include port column

**Reference:** Commit `08c0c28` in svn/MM_3_Final, merged to svn/MM_3-2_Start

## Git Workflow Patterns

### Branch Strategy
- **MM3/src/** tracks `svn/MM_3_Final` (stable/production)
- **MM32/src/** tracks `svn/MM_3-2_Start` (development)
- **Workflow:** Fix in Stable, Merge to Dev (MM3 → MM32)

### Merge Conflict Resolution
When merging MM3 → MM32:
- Keep MM32 dev branch enhancements (more detailed documentation)
- Apply MM3 stable fixes to MM32 code structure
- Preserve MM32-specific features that don't conflict with fixes

## Ubermap patterns (MM32 lib/world data)

- **Physical scope policy (source of truth)**: `docs/ubermap/physical_scope_policy.md`
- **Macro grid alignment**: keep overland macro tiles at the standard width/height; abnormal footprints can cause the Ubermap coordinate solver to “shear” a whole column/row (visible as misaligned tiles and direction-mismatch edges).

## Buffer Safety / Stack-Smash Hardening (2025-12-31)

### ASan workflow (MM3 → MM32)
- Enable ASan in the Makefiles to catch overflows early; fix in **MM3 first**, then merge to MM32.
- Use `MM32/src/merge-mm32` (wrapper around git operations) for the merge and expect conflicts in shared docs/tests.

### Character output formatting rule
- When addressing buffer overflow / truncation issues for output that is ultimately sent to a player, **rewrite to `send_to_charf()` instead of `snprintf` into an intermediate `buf` + `send_to_char`**.
- Source of truth: `MM32/src/MANIFESTO.md` Buffer Safety rules (contains the MUST-rule).

## SIT Automation Patterns (Python, Telnet)

### Layering: harness vs runner vs suites (reduce MM3→MM32 merge conflicts)

**Goal:** Keep shared SIT plumbing identical across MM3/MM32 while allowing branch-specific tests.

**Files (MM3 and MM32):**
- `tests/mud_sit_harness.py`: shared telnet/prompt/login/pager + send/verify helpers.
- `tests/mud_sit_runner.py`: shared CLI + orchestration + status JSON + completion markers.
- `tests/sit_suite_base.py`: MM3-owned base suite keyed by **stable test IDs**.

**MM32-only:**
- `MM32/src/tests/sit_suite_mm32.py`: extends and overrides the base suite.

**Override rule:**
- Override a base test by reusing the same stable ID key and replacing the `TestSpec`.
- Add MM32-only tests using `mm32_` prefix IDs.

### Status markers (for CI/agents)

SIT runs should always emit:
- `=== TEST SUITE COMPLETE: SUCCESS|PARTIAL|FAILED ===`
- `test_run_*.status.json` alongside the log file

### Command naming rule: use player command names from commands.dat

Do not assume internal helper names. Example:
- `affected` is the player command (`commands.dat`), not `affects`/`affect`.

## printf/varargs Safety During Format-Truncation Refactors (2025-12-31)

### Pattern: never change format specifiers without matching varargs
- `send_to_charf()` wraps `vsnprintf()`: **format specifier count must match the number/types of arguments**.
- Common refactor shape: adding truncation + explicit reset-color suffix:
  - From: `%s%s` (color + value)
  - To: `%s%.100s%s` (color + truncated value + reset color)
- If you add the trailing `%s`, you must also add the missing trailing argument (typically `nrm`) at the call site.

### Concrete example (MM32)
- `MM32/src/oedit.c:oedit_disp_extradesc_menu`:
  - Format expects a trailing reset-color `%s` for both keyword and description lines.
  - Call site must include `..., keyword_value, nrm, ... description_value, nrm, ...` or output is undefined behavior (stack read past provided args).

## BuilderPort Protocol v1 (World Building)

The engine's status port (BuilderPort) is the canonical authority for world data and `.wld` generation.

**Key Decisions:**
- **Handshake:** `HELLO <token> <proto_version>` is required before any world-mutating commands.
- **Authentication:** Token loaded from `lib/etc/builderport.token`; never hardcoded in source.
- **Transactions:** Mutating operations must occur within `TX_BEGIN` ... `TX_COMMIT` / `TX_ABORT` blocks.
- **Standardized Responses:**
  - `OK` or `OK <data>`
  - `ERROR <code> <msg_b64>`
  - Bulk data: `OK` -> `DATA <type> ...` -> `END`
- **Mutators:**
  - `room_full`: Destructive replace of core fields (clears exits/extras).
  - `room_patch`: Field-level updates (`NAME`, `DESC`, `SECTOR`, `FLAGS`, `WIDTH`, `HEIGHT`, `SPECFUNC`, `EXTRADESC`).
  - `link` / `unlink`: Support `BIDIR` (default) and `ONEWAY` modes.
- **Validation:** `validate` checks for non-existent targets and accidental one-way links.
- **Export:** `export` performs authoritative serialization to disk only after validation.
