# TymeMUD Builder MCP v2 Design Proposal

## Purpose

This document proposes additions to the `tymemud-builder` MCP interface to support high-volume Ubermap auditing and repair workflows safely, without direct `.wld` file edits.

The goals are:

- eliminate syntax-risky world-file editing
- make topology audits first-class API operations
- reduce round-trips for bulk room/link updates
- provide clearer diagnostics when a room is omitted from map outputs

---

## Current Coverage (Already Good)

Existing tools already provide a strong base:

- `read_room`, `update_room`, `create_room`
- `link_rooms`
- `list_zones`, `validate_zone`, `export_zone`
- `list_sectors`, `list_room_flags`, `list_spec_funcs`
- `export_ubermap_svg`

Primary gaps are around **discovery**, **topology diagnostics**, and **transaction/batch ergonomics**.

---

## Recommended Additions

## 1) List Rooms in Zone

### Why

Audits need fast room enumeration by zone with filtering (sector, flags, text queries). Right now, this requires external file parsing.

### Proposed endpoint

- `list_rooms_in_zone`

### Input

- `host`, `port`, `token`
- `zone` (int, required)
- pagination mode:
  - `limit` (default 100)
  - `offset` (default 0)
- optional filters:
  - `sector_in` (list of sector types)
  - `flags_any` (list of flags)
  - `name_contains` (string)
  - `has_exit_to` (vnum)

### Output

- `rooms[]` with minimal summary:
  - `vnum`, `name`, `sector`, `flags`, `width`, `height`, `exit_count`
- `total_count`
- `next_offset` (nullable)

### Notes

- Keep this endpoint lightweight (summary only).
- Use `read_room` for full details on selected VNUMs.

---

## 2) Link Graph Queries (Inbound/Outbound)

### Why

Bidirectionality checks require both outgoing and incoming link visibility. Current APIs make this expensive because callers must brute-force scan.

### Proposed endpoints

- `get_room_links`
- `get_zone_links`

### `get_room_links` input

- `host`, `port`, `token`
- `vnum` (required)

### `get_room_links` output

- `outbound[]`: `{dir, to_vnum, door_flag, key}`
- `inbound[]`: `{from_vnum, dir_from_source, door_flag, key}`

### `get_zone_links` input

- `host`, `port`, `token`
- `zone`
- optional `include_cross_zone` (default true)

### `get_zone_links` output

- normalized edge list for analysis:
  - `{from_vnum, dir, to_vnum, is_cross_zone}`

### Notes

- This directly powers reciprocal-link audits and “who points at this room?” workflows.

---

## 3) Explicit Exit Deletion

### Why

Using sentinel values (for example `to_vnum=-1`) is ambiguous and easy to misuse in automation. An explicit delete is safer.

### Proposed endpoint

- `delete_exit`

### Input

- `host`, `port`, `token`
- `from_vnum`
- `direction`
- required `mode`: `ONEWAY` or `BIDIR`

### Output

- `deleted: true/false`
- if `BIDIR`: reciprocal action status

### Notes

- Return idempotent success if exit is already absent.

---

## 4) Explicit Transaction Lifecycle (Assuming we keep transactions?)

### Why

The docs reference transaction context, but lifecycle endpoints are needed for safe multi-step edits with rollback on failure.

### Proposed endpoints

- `begin_transaction`
- `commit_transaction`
- `rollback_transaction`

### Input/Output

- `begin_transaction` returns `transaction_id`
- mutating endpoints accept optional `transaction_id`
- `commit_transaction` returns mutation summary
- `rollback_transaction` returns reverted operation count

### Notes

- Support server-side lock scoping by zone where possible.
- Timeout stale transactions automatically.

---

## 5) Topology Audit Endpoint

### Why

A single audit endpoint removes custom ad-hoc scripts and ensures consistent diagnostics across agents.

### Proposed endpoint

- `audit_zone_topology`

### Input

- `host`, `port`, `token`
- `zone`
- optional checks toggle (all default true):
  - `check_duplicate_dir_targets`
  - `check_missing_reciprocals`
  - `check_invalid_destinations`
  - `check_cardinal_doorflags_for_overland`
  - `check_cross_zone_link_consistency`

### Output

- categorized findings:
  - `errors[]`
  - `warnings[]`
  - `info[]`
- each finding:
  - `code`, `severity`, `vnum`, optional `direction`, optional `related_vnum`, `message`

### Suggested finding codes

- `DUPLICATE_DIR_TARGET`
- `MISSING_RECIPROCAL`
- `INVALID_DESTINATION`
- `CARDINAL_EXIT_LOCKED`
- `CROSS_ZONE_ONEWAY`

---

## 6) Room Inclusion Diagnostics ("Why is room missing?")

### Why

During Ubermap SVG generation, users often ask why a room is excluded or annotated unexpectedly. A structured diagnostic endpoint is easier to consume than parsing logs.

### Proposed endpoint

- `diagnose_room_map_inclusion`

### Input

- `host`, `port`, `token`
- `vnum`
- optional map context:
  - `base_zone_start`, `base_zone_end`
  - `pluslinked` (bool)

### Output

- `included: true/false`
- `classification` (for example: `in_scope`, `linked_oos`, `excluded`)
- `reasons[]` machine-readable codes + human text
- `supporting_facts`:
  - sector, exits summary, reachability summary, any violated constraints


---

## 7) Batch Mutations

### Why

Large repair sets require many API calls. Batch endpoints reduce latency and make failures easier to manage in one transaction.

### Proposed endpoints

- `update_rooms_batch`
- `link_rooms_batch`

### Input

- `host`, `port`, `token`
- `transaction_id` (recommended)
- `operations[]` (same schema as single-room/link operations)

### Output

- `results[]` per operation:
  - `index`, `success`, `error_code`, `error_message`
- aggregate summary counts

### Notes

- Prefer partial-results reporting over all-or-nothing, with transaction rollback handled by caller policy.

---

## 8) Direction Name Support

### Why

Human-authored repair plans are usually directional names, not integers. This reduces mistakes.

### Proposal

- Accept `direction` as either int or enum string (`north`, `east`, `south`, `west`, etc.)
- Always return both:
  - `direction_code` (int)
  - `direction_name` (string)

---

## 9) Return Data Directly Instead of File Export (for Artifacts)

### Why

For agent workflows, data APIs are generally better than writing files and reading them back.

### Recommendation

Instead of an `export_ubermap_all_artifacts` file-oriented endpoint, prefer:

- `get_ubermap_coords`
- `get_ubermap_components`
- `get_ubermap_mismatches`
- `get_ubermap_outofscope_edges`

All should support pagination and optional filters by zone/vnum.

### Keep existing file export

- Keep `export_ubermap_svg` for human review artifacts.
- For machine use, expose structured data directly via MCP.

---

## Priority Order for Implementation

## P0 (highest value)

1. `list_rooms_in_zone`
2. `get_room_links` + `get_zone_links`
3. `delete_exit`
4. transaction lifecycle endpoints
5. `audit_zone_topology`

## P1

6. `diagnose_room_map_inclusion`
7. batch mutation endpoints
8. direction name support

## P2

9. structured ubermap data endpoints (coords/components/mismatches)

---

## Compatibility and Safety Notes

- Keep existing endpoints stable; add new endpoints non-breaking.
- Add a `dry_run` option on all mutating calls (or at least batch calls).
- Include optional `actor` and `reason` metadata for audit trails.
- Return deterministic error codes for automation (`INVALID_VNUM`, `ZONE_LOCKED`, etc.).

---

## Example Minimal v2 Milestone

If scope must stay tight, a strong first milestone is:

- `list_rooms_in_zone`
- `get_room_links`
- `delete_exit`
- `begin/commit/rollback_transaction`
- `audit_zone_topology`

This set alone would cover most overland audit and repair operations safely.
