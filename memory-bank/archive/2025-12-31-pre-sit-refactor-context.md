# Snapshot: 2025-12-31 (memory-bank content prior to SIT refactor updates)

This file preserves a snapshot of the memory-bank content as it existed before the
SIT framework refactor + documentation refresh on 2025-12-31.

This content is **not deprecated**; it was simply the state of the memory bank at
the time. The SQL `pfiles_main` + `port` pattern remains a critical invariant.

## Previous `activeContext.md` (as found)
- Objective: Maintain project context and document critical SQL bug fix pattern for pfiles_main operations
- Date: 2025-01-29
- Key finding: pfiles_main composite key includes `port`
- Claimed fix: `MM3/src/interpreter.c:1691` (commit references present in old memory bank)

## Previous `systemPatterns.md` (as found)
- SQL pattern for pfiles_main: always include `port` in WHERE clause for single-row ops
- Git workflow notes (MM3 stable → MM32 dev)

## Previous `progress.md` (as found)
- Dated 2025-01-29; tracked a pfiles_main SQL DELETE bugfix and merges

