# BuilderPort Protocol v1.1 Implementation Plan

## Overview
Enhance the BuilderPort protocol to return human-readable text values alongside numeric values, and restructure list_zones to support pagination.

## Phase 1: Fix Server-Side Zone Parsing
**Status:** Not Started
**Priority:** Critical - blocks all transaction operations

### Issue
Transaction commands fail with "invalid zone list" for single zones

### Root Cause
The `parse_zone_list()` function in `statusport.c` may not handle single zones correctly

### Implementation
1. Debug `parse_zone_list()` function behavior with single vs multiple zones
2. Identify why single zone "471" fails but "471,472" works
3. Fix the parsing logic

### Test Criteria
- `tx_begin ZONES 471` → OK
- `tx_begin ZONES 471,472` → OK
- `tx_begin ZONES 10` → OK (zone 10 exists)

## Phase 2: Update read_room Protocol Response
**Status:** Not Started
**Dependencies:** Phase 1

### Changes to DATA ROOM Format
**Current:**
```
DATA ROOM <vnum> <zone> <sector> <width> <height> <flags> <name_b64> <desc_b64>
```

**New:**
```
DATA ROOM <vnum> <zone> <sector> <sector_name_b64> <width> <height> <flags> <flags_names_b64> <name_b64> <desc_b64>
```

### New Fields
- `sector_name_b64` - base64 encoded sector type name (e.g., "Inside", "City")
- `flags_names_b64` - base64 encoded comma-separated flag names (e.g., "GODROOM,OLC,PRIVATE")

### Affected Code
- `statusport.c` - update room data output format
- `llm_gateway/client.py` - update `get_room()` parsing
- `llm_gateway/server.py` - update `read_room` tool output

### Test Criteria
- Read room 1000: sector=0, sector_name="Inside", flags=0, flags_names=""
- Read room 1204: sector=0, sector_name="Inside", flags=1032, flags_names includes "GODROOM" and "OLC"

## Phase 3: Restructure list_zones Protocol Response
**Status:** Not Started
**Dependencies:** Phase 2

### Changes
**Remove from response:**
- SECTOR data lines
- ROOMFLAGS line
- SPECFUNCS line

**Add required pagination:**
New command format: `wld_list <mode> [params]`

**Modes (mutually exclusive):**
1. `RANGE <start_zone> <end_zone>` - Return zones in numeric range
2. `OFFSET <limit> <offset>` - Return paginated results
3. `ALL` - Return all zones (explicit opt-in required)

**Error if no mode specified:**
`ERROR 400 bW9kZSByZXF1aXJlZA==` ("mode required")

### Response Format
```
OK
DATA ZONE <vnum> <name_b64>
...
END
```

### Affected Code
- `statusport.c` - rewrite `status_wld_list()` function
- `llm_gateway/client.py` - update `list_zones()` method
- `llm_gateway/server.py` - update `list_zones` tool schema

### Test Criteria
- `wld_list` (no args) → ERROR 400
- `wld_list RANGE 470 480` → zones 470-480
- `wld_list OFFSET 20 0` → first 20 zones
- `wld_list OFFSET 20 20` → zones 21-40
- `wld_list ALL` → all 132 zones

## Phase 4: Add New Protocol Commands
**Status:** Not Started
**Dependencies:** Phase 3

### list_sectors Command
**Format:** `list_sectors`

**Response:**
```
OK
DATA SECTOR <id> <name_b64>
...
END
```

**Example:**
```
DATA SECTOR 0 SW5zaWRl
DATA SECTOR 1 Q2l0eQ==
...
```

### list_room_flags Command
**Format:** `list_room_flags`

**Response:**
```
OK
DATA ROOMFLAG <bit> <name>
...
END
```

**Example:**
```
DATA ROOMFLAG 0 DARK
DATA ROOMFLAG 2 !MOB
...
```

### Affected Code
- `statusport.c` - add `status_list_sectors()` and `status_list_room_flags()`
- `llm_gateway/client.py` - add `list_sectors()` and `list_room_flags()` methods
- `llm_gateway/server.py` - add new MCP tools

### Test Criteria
- `list_sectors` returns 12 sector types
- `list_room_flags` returns 27 room flags

## Phase 5: Update MCP Server Tools
**Status:** Not Started
**Dependencies:** Phases 2-4

### Changes

#### read_room Tool
- Parse new DATA ROOM format (10 fields instead of 8)
- Include sector_name in response
- Include flags_names array in response

#### list_zones Tool
- Add mode parameter (required enum: "range", "offset", "all")
- Add range_start/range_end parameters (for mode="range")
- Add limit/offset parameters (for mode="offset")
- Update response to only include zones

#### New Tools
- `list_sectors` - list all sector types
- `list_room_flags` - list all room flags

### Affected Code
- `llm_gateway/client.py` - update all protocol parsing
- `llm_gateway/server.py` - update tool schemas and handlers

### Test Criteria
- All 7 tools work correctly
- read_room returns both numeric and text values
- list_zones enforces required mode parameter
- list_sectors returns sector mappings
- list_room_flags returns flag mappings

## Phase 6: Update PHP API
**Status:** Not Started
**Dependencies:** Phase 5

### Changes to `wld_editor_api.php`

#### List Action
**Current:** Calls `wld_list` and parses sectors/room_flags/spec_funcs
**New:** 
- Call `wld_list ALL` to get all zones
- Call `list_sectors` separately if needed
- Call `list_room_flags` separately if needed

#### Load Action
**Current:** Parses DATA ROOM with 8 fields
**New:** Parse DATA ROOM with 10 fields, extract sector_name and flags_names

#### Save Action
**Current:** Uses numeric sector and flags values
**New:** No change needed - still sends numeric values

### Affected Code
- `public_html/wld_editor_api.php` - update all protocol interactions

### Test Criteria
- Zone list displays correctly
- Room data loads with sector names
- Room saves work correctly

## Phase 7: Integration Testing
**Status:** Not Started
**Dependencies:** Phase 6

### Full Workflow Tests
1. **Browse zones:** list_zones → display to user
2. **Load room:** read_room → display room data
3. **Edit room:** update fields
4. **Save room:** create_room/update_room → validate_zone → export_zone

### Pagination Tests
- Browse first 20 zones
- Navigate to next 20 zones
- Jump to specific zone range

### Edge Cases
- Empty zone list
- Non-existent zone
- Invalid room vnum
- Network errors

## Implementation Notes

### Breaking Changes
This is a breaking protocol change. All clients must be updated:
- MCP server (llm_gateway)
- Web editor (wld_editor_api.php)
- Any other status port clients

### No Backwards Compatibility
Since this is an internal tool, we will not maintain backwards compatibility. All affected code must be updated and tested.

### File Locations
- MUD engine: `_agent_work/wld_editor_api_agent/MM32/src/statusport.c`
- MCP server: `llm_gateway/client.py`, `llm_gateway/server.py`
- Web API: `_agent_work/wld_editor_api_agent/public_html/wld_editor_api.php`

## Success Criteria
- [ ] All transaction commands work (Phase 1)
- [ ] Room data includes text values (Phase 2)
- [ ] Zone list supports pagination (Phase 3)
- [ ] New list commands work (Phase 4)
- [ ] MCP tools updated and functional (Phase 5)
- [ ] PHP API updated and functional (Phase 6)
- [ ] Full end-to-end workflow tested (Phase 7)

## Authorization
Status: PLAN mode - awaiting ACT authorization
Last Updated: 2026-01-31
