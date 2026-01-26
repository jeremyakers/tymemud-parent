# MM32 Combat: log findings / stability backlog

This doc captures **recurring combat-related runtime errors** seen while exercising MM32 combat via `mud_client` smoke runs and SIT server boots.

## Sources
- Smoke run logs: `MM32/src/tests/test_logs/combat_smoke_*/mud_client_*.log`
- SIT-managed server logs: `MM32/src/tests/test_logs/server_*.log`
- Smoke-run server logs (new): `MM32/src/tests/test_logs/combat_smoke_*/server.log`

## Combat-runtime issues (recurring)

### 1) `executeNormalDefense` complains `weapons_orientation_ch is NOT SET!!!`
- **Symptom**: Repeated in smoke logs during unarmed fights.
- **Example** (from smoke logs): lines containing
  - `executeNormalDefense' ERROR: weapons_orientation_ch is NOT SET!!!`
- **Code location**: `MM32/src/turn_based_combat.c` in `get_attack_weapon()`:
  - The error is emitted when `attack_weapon` ends up NULL and the function assumes “this should be impossible”.
- **Likely cause**: unarmed attacks (no wielded weapon object) currently flow through weapon-selection logic that expects an equipped object.
- **Impact**: noisy logs and potential downstream undefined behavior (weapon-dependent code paths).
- **Fix direction**: treat “unarmed / no weapon object” as a first-class case (skip weapon selection without raising syserr).

### 2) `random_bodypart` failures / “returned no bodypart”
- **Symptom**: earlier smoke logs showed:
  - `executeNormalHit' DEBUG: random_bodypart returned no bodypart.`
  - `random_bodypart' DEBUG: Couldn't find a bodypart!`
- **Impact**: hits may proceed without a valid bodypart selection, breaking wounds/armor targeting.
- **Fix direction**:
  - Ensure victim bodyparts are always loaded/initialized for PCs and mobs.
  - Ensure forms’ `bodypart_regions` masks are valid for the target.
  - Add a safe fallback (e.g., default to torso/chest) if selection fails.

## Boot-time / data-integrity noise seen during combat testing

### 0) `commands.dat` references undefined command handlers (server won’t have those commands)
- **Symptom** (in smoke-run `server.log`): many lines like:
  - `Bad line #... in command file: <cmd> (./src/bin/tyme3: undefined symbol: do_<something>)`
- **Impact**: missing commands and noisy boot logs; can hide real combat errors during iteration.
- **Fix direction**: reconcile `lib/commands.dat` with the compiled command table (remove/rename commands or restore the missing handlers).
  - For **combat-focused debugging**, this can be treated as **log noise** and filtered while grepping.

### 3) `load_mobprog_lists` / missing mob references
- **Symptom**: lots of SYSERR in SIT logs (not strictly combat, but pollutes logs during combat runs):
  - `SYSERR: db.c:5904 (load_mobprog_lists) No such mob exists: ...`
- **Fix direction**: world data / mobprog list references need reconciliation (or downgrade to non-fatal warning if expected in dev DB/world snapshot).

### 4) `Attempt to assign spec to non-existant mob/obj`
- **Symptom**: repeated SYSERR during boot.
- **Fix direction**: reconcile `spec_assign.c` data vs world index files in this dev snapshot.

## Crash history (ASan)

### 5) ASan crash: `genwld.c:assign_room_locations()` (dynamic-stack-buffer-overflow)
- **Seen in**: `MM32/src/tests/test_logs/server_20251231_110103.log`
- **Root cause**: incorrect sizing/indexing of worldmap array (stack OOB).
- **Status**: previously fixed (server boots past this now).

### 6) ASan crash: `weaves.c:sortSkillNumbers()` (global-buffer-overflow)
- **Seen in**: `MM32/src/tests/test_logs/server_20251231_110208.log`
- **Root cause**: out-of-bounds writes to `skill_num_find`.
- **Status**: fixed (bounds-check + safer loop).

### 7) ASan leak reports during shutdown
- **Seen in**: various `server_*.log` (example: `server_20251231_111126.log`)
- **Status**: informational for now; not a crash, but worth tracking once combat correctness stabilizes.

