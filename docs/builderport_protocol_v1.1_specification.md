# BuilderPort Protocol v1.1 Specification

## Overview

The BuilderPort Protocol provides programmatic access to the MUD world's room and zone data through a TCP status port. It enables external tools (web editors, MCP servers, etc.) to read and modify the game world in real-time.

**Protocol Version:** 1.1  
**Transport:** TCP (plain text with base64 encoding for binary data)  
**Default Port:** Game port + 1 (e.g., 9696 → 9697)  
**Authentication:** Token-based, auto-generated on server boot

---

## Connection & Authentication

### Initial Handshake

All sessions must begin with a HELLO command:

```
Client: hello <token> <protocol_version>
Server: OK <protocol_version>
```

**Example:**
```
hello AbC123XyZ789 1
OK 1
```

### Token Management

- Tokens are auto-generated on each server boot
- 32-character alphanumeric string (mixed case)
- Written to `lib/etc/builderport.token`
- External tools should read token from this file
- Token changes on every server restart for security

**Token File Location:**
```
../lib/etc/builderport.token
```

---

## Response Format

### Success Responses

All successful commands return `OK` followed by optional data:

```
OK
OK <additional_data>
```

### Error Responses

Errors use HTTP-style status codes with base64-encoded messages:

```
ERROR <code> <base64_message>
```

**Common Error Codes:**
- `400` - Bad Request (missing/invalid parameters)
- `401` - Unauthorized (invalid token)
- `404` - Not Found (room/zone doesn't exist)
- `409` - Conflict (transaction error, room locked)
- `422` - Unprocessable Entity (validation failed)
- `423` - Locked (room is locked by another user)
- `500` - Internal Server Error

**Error Message Decoding:**
```bash
echo "VW5hdXRob3JpemVk" | base64 -d
# Output: Unauthorized
```

---

## Metadata Commands

### List Sectors

Returns all available sector types for room classification.

**Command:**
```
list_sectors
```

**Response:**
```
OK
DATA SECTOR <index> <name_b64>
...
END
```

**Example:**
```
list_sectors
OK
DATA SECTOR 0 SW5zaWRl
DATA SECTOR 1 Q2l0eQAA
...
END
```

**Standard Sectors (0-11):**
- 0: Inside
- 1: City
- 2: Field
- 3: Forest
- 4: Hills
- 5: Mountains
- 6: Water (Swim)
- 7: Water (No Swim)
- 8: Underwater
- 9: In Flight
- 10: Dirt road
- 11: Main road

### List Room Flags

Returns all available room flags.

**Command:**
```
list_room_flags
```

**Response:**
```
OK
DATA ROOMFLAG <bit_position> <name_b64>
...
END
```

**Common Flags:**
- DARK, INDOORS, PEACEFUL, SOUNDPROOF
- TRACK, MAGIC, TUNNEL, PRIVATE
- GODROOM, HOUSE, CRASH, ATRIUM
- OLC, NOGATE, RAIDED, TELEPORTER
- SHIP, PLANK, DECK, HELL
- DOMAIR, DOMEFIRE, LOCKER, RECALL

### List Special Functions

Returns all available special function assignments.

**Command:**
```
list_spec_funcs
```

**Response:**
```
OK
DATA SPECFUNC <name_b64>
...
END
```

---

## Zone Commands

### List Zones

Returns a list of all zones with pagination support.

**Command:**
```
wld_list ALL
wld_list RANGE <start_zone> <end_zone>
wld_list OFFSET <limit> <offset>
```

**Response:**
```
OK
DATA ZONE <vnum> <name_b64>
...
END
```

**Examples:**
```
wld_list RANGE 0 10
OK
DATA ZONE 0 YCZJYDdtbW0g
DATA ZONE 1 YDJJbW1vcnRhbA--
...
END
```

### Load Zone Data

Returns all rooms in specified zone(s) with complete data.

**Command:**
```
wld_load <zone_vnum> [<zone_vnum> ...]
wld_load ALL
```

**Response:**
```
OK
DATA ROOM <vnum> <zone_vnum> <sector> <sector_name_b64> <width> <height> <flags> <flags_names_b64> <name_b64> <desc_b64>
DATA EXIT <room_vnum> <dir> <to_vnum> <flags> <key> <desc_b64> <keyword_b64>
DATA EXTRADESC <room_vnum> <keyword_b64> <desc_b64>
DATA SPECFUNC <room_vnum> <func_name>
...
END
```

**Room Data Fields (10 fields):**
1. Room VNUM (numeric)
2. Zone VNUM (numeric)
3. Sector type (numeric index)
4. Sector name (base64) - human-readable sector type
5. Width (numeric)
6. Height (numeric)
7. Room flags (bitmask)
8. Flags names (base64) - comma-separated flag names
9. Room name (base64)
10. Room description (base64)

**Exit Data Fields (7 fields):**
1. Source room VNUM
2. Direction (0-9: N, E, S, W, U, D, NE, NW, SE, SW)
3. Target room VNUM (-1 for no exit)
4. Exit flags (0=open, 1=closed, etc.)
5. Key object VNUM (-1 for none)
6. Exit description (base64)
7. Exit keywords (base64)

### Validate Zones

Checks zones for errors (orphaned rooms, missing links, etc.).

**Command:**
```
validate ZONES <zone_vnum> [<zone_vnum> ...]
```

**Success Response:**
```
OK
```

**Error Response:**
```
ERROR 422 <validation_errors_b64>
```

### Export Zones

Exports zones to disk (writes .wld files).

**Command:**
```
export ZONES <zone_vnum> [<zone_vnum> ...]
```

**Response:**
```
OK
```

---

## Room Commands

### Create/Replace Room (Full)

Creates a new room or completely replaces an existing one.

**Command:**
```
room_full <vnum> <zone> <sector> <width> <height> <flags> <name_b64> <desc_b64>
```

**Parameters:**
- `vnum` - Room virtual number
- `zone` - Zone VNUM this room belongs to
- `sector` - Sector type (0-11)
- `width` - Room width (typically 8-10)
- `height` - Room height (typically 8-10)
- `flags` - Room flags bitmask
- `name_b64` - Room name (base64 encoded)
- `desc_b64` - Room description (base64 encoded)

**Example:**
```
room_full 9999 12 3 10 10 0 VGVzdFJvb20- RGVzY3JpcHRpb24-
OK
```

**Note:** This command clears all exits and extra descriptions on existing rooms.

### Patch Room (Partial Update)

Updates specific fields of an existing room without affecting others.

**Command:**
```
room_patch <vnum> [<field> <value>]...
```

**Fields:**
- `NAME <b64>` - Room name
- `DESC <b64>` - Room description
- `SECTOR <n>` - Sector type (numeric)
- `FLAGS <n>` - Room flags (bitmask)
- `WIDTH <n>` - Room width
- `HEIGHT <n>` - Room height
- `SPECFUNC <name>` - Special function name
- `EXTRADESC <keyword_b64> <desc_b64>` - Add extra description

**Examples:**
```
# Update name and description
room_patch 1200 NAME VXBkYXRlZFJvb20- DESC VXBkYXRlZERlc2M-
OK

# Change sector to Forest (3)
room_patch 1200 SECTOR 3
OK

# Add extra description
room_patch 1200 EXTRADESC c2lnbg-- c2lnbiB0ZXh0IGhlcmU-
OK
```

### Create Exit (Link Rooms)

Creates an exit from one room to another.

**Command:**
```
link <from_vnum> <dir> <to_vnum> <flags> <key> <desc_b64> <keyword_b64> [<mode>]
```

**Parameters:**
- `from_vnum` - Source room
- `dir` - Direction (0-9)
- `to_vnum` - Target room (-1 for no exit)
- `flags` - Exit flags (0=open)
- `key` - Key object VNUM (-1 for none)
- `desc_b64` - Exit description (base64)
- `keyword_b64` - Exit keywords (base64)
- `mode` - `BIDIR` (default) or `ONEWAY`

**Direction Values:**
- 0: North
- 1: East
- 2: South
- 3: West
- 4: Up
- 5: Down
- 6: Northeast
- 7: Northwest
- 8: Southeast
- 9: Southwest

**Example:**
```
# Create bidirectional exit from 1200 east to 1201
link 1200 1 1201 0 -1 dGVzdA-- dG9vci1lYXN0 BIDIR
OK
```

### Remove Exit

Removes an exit from a room.

**Command:**
```
unlink <room_vnum> <dir> [<mode>]
```

**Example:**
```
unlink 1200 1 BIDIR
OK
```

---

## Room Locking

Room locking prevents concurrent edits by multiple builders.

### Lock Room

**Command:**
```
wld_lock <vnum> <builder_name>
```

**Success:**
```
OK
```

**Error (already locked):**
```
ERROR 423 <current_holder_b64>
```

### Unlock Room

**Command:**
```
wld_unlock <vnum> <builder_name>
```

### Check Lock Status

**Command:**
```
wld_lock_status <vnum>
```

**Response (locked):**
```
ERROR 423 <holder_b64>
```

**Response (unlocked):**
```
OK
```

---

## Map Commands

### Export Ubermap

Generates an SVG map of overland zones.

**Command:**
```
export_ubermap [<filepath>]
```

**Response:**
```
OK <filepath>
```

**Examples:**
```
# Use default path
export_ubermap
OK tmp/ubermap_468_640_pluslinked_z0.svg

# Custom path
export_ubermap /var/www/maps/world.svg
OK /var/www/maps/world.svg
```

---

## Base64 Encoding

All text fields use URL-safe base64 encoding (RFC 4648).

**Encoding:**
```python
import base64

# Encode
data = "Room Name"
encoded = base64.b64encode(data.encode()).decode()
# Result: "Um9vbSBOYW1l"

# URL-safe variant (no padding)
url_safe = base64.urlsafe_b64encode(data.encode()).decode().rstrip('=')
# Result: "Um9vbSBOYW1l"
```

**Decoding:**
```python
# Decode
decoded = base64.b64decode(encoded).decode()
```

**Special Values:**
- `-` (dash) represents NULL/empty
- Must decode to UTF-8 text

---

## Protocol Flow Examples

### Complete Room Edit Workflow

```
# 1. Authenticate
hello ABC123xyz 1
OK 1

# 2. Lock room for editing
wld_lock 1200 builder1
OK

# 3. Load current room data
wld_load 12
OK
DATA ROOM 1200 12 0 SW5zaWRl 8 8 0 - Um9vbTEyMDA- VGVzdHJvb20-
...
END

# 4. Update room
room_patch 1200 NAME VXBkYXRlZFJvb20-
OK

# 5. Add exit
link 1200 1 1201 0 -1 dG9vci0- ZG9vci1lYXN0 BIDIR
OK

# 6. Add extra description
room_patch 1200 EXTRADESC c2lnbg-- c2lnbiBkZXNj-
OK

# 7. Validate zone
validate ZONES 12
OK

# 8. Export zone
export ZONES 12
OK

# 9. Unlock room
wld_unlock 1200 builder1
OK

# 10. Disconnect
quit
```

### Quick Room Creation

```
hello ABC123xyz 1
OK 1

# Create new room
room_full 9999 12 3 10 10 0 VGVzdFJvb20- RGVzY3JpcHRpb24tZXN0-
OK

# Link to existing room
link 9999 0 3001 0 -1 LS1kdW1teS0- LS1kdW1teS0- BIDIR
OK

quit
```

---

## Error Handling Best Practices

1. **Always check for ERROR responses**
2. **Decode base64 error messages** for user display
3. **Handle 423 (Locked)** by showing who holds the lock
4. **Retry on 401** after re-reading token file
5. **Validate before export** to catch errors early

---

## Security Considerations

1. **Token Rotation** - Tokens change on every server restart
2. **No Persistent Sessions** - Must re-authenticate after disconnect
3. **Room Locking** - Prevents concurrent modification conflicts
4. **In-Memory Only** - Changes persist only until server restart unless exported
5. **Zone Validation** - Prevents creating invalid world states

---

## Version History

- **v1.0** - Initial implementation with transaction-based workflow
- **v1.1** - Standalone commands, auto-generated tokens, enhanced room data format

---

## Implementation Notes

### Server-Side Implementation

Located in: `_agent_work/wld_editor_api_agent/MM32/src/statusport.c`

Key functions:
- `load_status_token()` - Token generation on boot
- `status_hello()` - Authentication handler
- `status_room_full()` / `status_room_patch()` - Room mutators
- `status_link()` / `status_unlink()` - Exit management
- `status_wld_load()` - Room data retrieval
- `status_room_lock()` / `status_room_unlock()` - Locking

### Client Libraries

- **MCP Server**: `llm_gateway/server.py` - OpenAI MCP protocol wrapper
- **PHP API**: `public_html/wld_editor_api.php` - Web editor backend

---

## Support

For issues or questions:
- Check server logs: `server_9696.log`
- Verify token file: `lib/etc/builderport.token`
- Test connectivity: `echo -e "who\nquit" | nc 127.0.0.1 9697`
