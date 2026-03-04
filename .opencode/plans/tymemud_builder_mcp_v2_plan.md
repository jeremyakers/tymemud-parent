# TymeMUD Builder MCP v2 Implementation Plan

## Context

This plan refines the v2 design proposal in `Building_Design_Notes/tymemud_builder_mcp_v2_design.md` with the following product decisions:

- Keep existing v1 endpoints stable and non-breaking.
- Do not introduce explicit transaction lifecycle endpoints.
- Use room locking + deterministic preflight validation for safety.
- For batch operations, use continue-on-error execution after preflight passes.
- Abort before any mutation if preflight reports errors.

## Finalized v2 Behavior Rules

1. All mutating batch endpoints must run a full preflight phase first.
2. If preflight has any errors, no mutations are attempted.
3. If preflight passes, execute operations with per-operation results.
4. Default execution policy is continue-on-error (`stop_on_error=false`).
5. Warnings do not block execution; errors do.
6. Support `dry_run=true` to run preflight only and return a simulated execution summary.
7. Include `actor` and `reason` metadata on mutating batch endpoints for auditability.

## Scope for v2 Milestone

### P0 (Implement First)

1. `list_rooms_in_zone`
2. `get_room_links`
3. `get_zone_links`
4. `delete_exit` (wrapper over existing `unlink` behavior)
5. `audit_zone_topology`
6. Direction name support (`north`, `east`, etc. in addition to int direction)
7. Stateless batch endpoints with mandatory preflight:
   - `update_rooms_batch`
   - `link_rooms_batch`

### Deferred (Later)

- `diagnose_room_map_inclusion`
- structured ubermap data APIs (`get_ubermap_coords`, components, mismatches, out-of-scope edges)

## API Contract Additions

## Shared Mutating Request Fields

- `actor` (string, required for batch)
- `reason` (string, required for batch)
- `dry_run` (bool, default `false`)
- `stop_on_error` (bool, default `false`)

## Shared Mutating Response Fields

- `preflight`:
  - `ok` (bool)
  - `errors[]`
  - `warnings[]`
- `execution` (present only when preflight ok and not dry-run):
  - `attempted`
  - `succeeded`
  - `failed`
  - `results[]`

## Per-Operation Result Shape

- `index` (int)
- `op_type` (string)
- `success` (bool)
- `error_code` (nullable string)
- `error_message` (nullable string)
- `details` (object)

## Deterministic Error Code Set (Initial)

- `INVALID_VNUM`
- `ROOM_NOT_FOUND`
- `ZONE_NOT_FOUND`
- `INVALID_DIRECTION`
- `INVALID_SECTOR`
- `INVALID_FLAG`
- `INVALID_DIMENSION`
- `INVALID_LINK_TARGET`
- `ROOM_LOCKED`
- `AUTH_FAILED`
- `ENGINE_ERROR`
- `TIMEOUT`

## Endpoint Notes

### `delete_exit`

- Implement as explicit wrapper over existing `unlink` behavior.
- Inputs: `from_vnum`, `direction`, `mode` (`ONEWAY` or `BIDIR`).
- Return idempotent success if exit is already absent.
- Document this as the preferred explicit deletion path (instead of sentinel patterns).

### Direction Support

- Accept `direction` as either int or case-insensitive enum string.
- Always return both:
  - `direction_code`
  - `direction_name`

## Implementation Strategy

## Phase 1: MCP Layer (No Engine Protocol Changes)

Deliver most P0 features by composing existing protocol commands:

- source room/zone snapshots from `wld_load` and `wld_dump` parsing already in gateway client.
- derive inbound links by indexing outbound edges in memory.
- implement preflight validators in MCP server before issuing mutation commands.
- normalize all errors to deterministic error codes.

Target files:

- `MM32/src/llm_gateway/server.py`
- `MM32/src/llm_gateway/client.py`
- `MM32/src/llm_gateway/README.md`

## Phase 2: Optional Engine Enhancements

Only if scale/performance requires:

- add native statusport commands for room/link summaries and topology audits.
- keep MCP contract unchanged and switch backend implementation to native fast paths.

Potential file:

- `MM32/src/statusport.c`

## Validation Plan

## Unit / Contract Validation (Gateway)

- direction parser and normalization tests
- preflight validator tests (error vs warning behavior)
- deterministic error mapping tests
- batch execution policy tests (`stop_on_error` true/false)

## Integration Validation (Live BuilderPort)

- list/filter pagination behavior for `list_rooms_in_zone`
- inbound/outbound correctness for `get_room_links`
- zone edge completeness for `get_zone_links`
- `delete_exit` idempotency and BIDIR behavior
- preflight abort behavior (zero mutations on errors)
- continue-on-error result accounting correctness

## Non-Regression Checks

- existing v1 MCP tools still operate unchanged
- lock contention behavior remains intact
- no crash/hang on invalid inputs

## Rollout Plan

1. Implement Phase 1 endpoints behind additive MCP tools.
2. Update docs with clear migration guidance and examples.
3. Ship as non-breaking v2 additions while retaining v1 tools.
4. Collect usage/performance signals before considering Phase 2 engine commands.

## Open Questions (Resolved for Current Plan)

- Transactions: not included in v2.
- Preflight warnings: non-blocking.
- Preflight errors: blocking (abort all mutations before execution).
- Batch policy after preflight: continue-on-error by default.

## Acceptance Criteria for Milestone Completion

1. All P0 endpoints implemented and documented.
2. Batch preflight blocks execution on any error.
3. Batch execution returns deterministic per-op results.
4. Direction name + code support is consistent across inputs/outputs.
5. Existing v1 functionality remains stable and backward-compatible.
