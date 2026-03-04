# Plan: MCP Server Tool Parameter Changes

**Agent:** wld_editor_api_agent
**Date:** 2026-01-31
**Status:** Planned - Awaiting Implementation Authorization

## Problem Statement

The current MCP server implementation has host/port/token configured at startup time via environment variables. This doesn't support multiple agents working against different MUD servers simultaneously within the same OpenCode instance.

## Solution

Move host, port, and token from startup configuration to **required parameters on every tool call**. This allows each agent to specify exactly which server to connect to for each operation.

## Changes Required

### 1. Update MCP Tool Schemas (server.py)

All 7 tools need host, port, and token added as **required** first parameters:

```python
# Example for read_room
inputSchema={
    "type": "object",
    "properties": {
        "host": {
            "type": "string",
            "description": "BuilderPort host address (e.g., 127.0.0.1)"
        },
        "port": {
            "type": "integer",
            "description": "BuilderPort status port (e.g., 9697)"
        },
        "token": {
            "type": "string",
            "description": "Authentication token for BuilderPort"
        },
        "vnum": {
            "type": "integer",
            "description": "Room vnum to read"
        }
    },
    "required": ["host", "port", "token", "vnum"]
}
```

**Tools to update:**
- read_room(host, port, token, vnum)
- list_zones(host, port, token)
- update_room(host, port, zone, vnum, **fields)
- create_room(host, port, zone, vnum, name, desc, ...)
- link_rooms(host, port, zone, from_vnum, direction, to_vnum, ...)
- validate_zone(host, port, zone)
- export_zone(host, port, zone)

### 2. Update Tool Implementations (server.py)

Each tool call handler must:
1. Extract host, port, token from arguments
2. Create a fresh BuilderPortClient with these parameters
3. Connect, execute operation, disconnect
4. **No connection reuse** - each call is independent

Example pattern:
```python
host = arguments["host"]
port = arguments["port"]
token = arguments["token"]

client = BuilderPortClient(host=host, port=port, token=token)
await client.connect()
# ... perform operation ...
await client.disconnect()
```

### 3. Update BuilderPortClient (client.py)

- Remove environment variable fallbacks for host/port
- Keep token loading from file as fallback only if not provided
- Ensure all three parameters are explicit requirements

### 4. Update Wrapper Script (scripts/llm-gateway.sh)

Remove environment variable exports:
```bash
# REMOVE these lines:
# export BUILDERPORT_PORT="${BUILDERPORT_PORT:-9697}"
# export BUILDERPORT_HOST="${BUILDERPORT_HOST:-127.0.0.1}"
```

### 5. Update opencode.json

Remove environment section since host/port/token are now per-call:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "tymemud-builder": {
      "type": "local",
      "command": ["./scripts/llm-gateway.sh"],
      "enabled": true
    }
  }
}
```

## Benefits

1. **Multi-agent support**: Each agent specifies its own server
2. **No accidental connections**: No defaults means no mistakes
3. **Explicit control**: Agent must intentionally choose which server to use
4. **Clean separation**: No global state, each call is self-contained

## Testing

1. Test that tools fail if host/port/token missing
2. Test that two sequential calls can use different servers
3. Test that multiple agents can operate simultaneously against different servers

## Files to Modify

- `llm_gateway/server.py` - Tool schemas and implementations
- `llm_gateway/client.py` - Remove env var fallbacks
- `scripts/llm-gateway.sh` - Remove env exports
- `opencode.json` - Remove environment config

## Migration Notes

This is a breaking change for any existing MCP tool calls. All existing calls must be updated to include host, port, and token parameters.

## Authorization Required

Reply with `ACT` to implement these changes.
