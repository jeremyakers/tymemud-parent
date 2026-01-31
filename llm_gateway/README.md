# LLM Gateway for TymeMUD

An MCP (Model Context Protocol) service that provides a safe, high-level interface for LLM agents to interact with the TymeMUD BuilderPort protocol.

## Overview

This gateway translates MCP tool calls into raw BuilderPort v1 protocol commands, handling:
- Authentication (HELLO handshake)
- Base64 encoding/decoding
- Transaction management (TX_BEGIN/COMMIT/ABORT)
- Connection lifecycle

## Architecture

```
[OpenCode Agent] <-- MCP (stdio) --> [LLM Gateway] <-- TCP --> [MUD Engine (9697)]
```

## Installation

```bash
cd llm_gateway
pip install -e .
```

Or with uv:
```bash
cd llm_gateway
uv pip install -e .
```

## Usage

### As an MCP Server (for OpenCode)

Add to your OpenCode configuration:

```json
{
  "mcpServers": {
    "tymemud": {
      "command": "python",
      "args": ["-m", "llm_gateway.server"],
      "cwd": "/path/to/tymemud/llm_gateway"
    }
  }
}
```

### Direct Usage (Python)

```python
import asyncio
from llm_gateway import BuilderPortClient

async def main():
    client = BuilderPortClient()
    await client.connect()
    
    # Read a room
    room = await client.get_room(1000)
    print(room)
    
    # List zones
    zones = await client.list_zones()
    print(zones)
    
    # Update a room (within transaction)
    async with client.transaction([10]) as tx:
        await tx.room_patch(1000, name="New Room Name", desc="New description")
    
    await client.disconnect()

asyncio.run(main())
```

## Available Tools

When used as an MCP server, the following tools are available:

- `read_room(vnum)` - Read room data
- `list_zones()` - List all zones
- `update_room(vnum, zone, **fields)` - Update specific room fields
- `create_room(vnum, zone, name, desc, ...)` - Create/replace a room
- `link_rooms(from_vnum, direction, to_vnum, zone, ...)` - Create exits
- `validate_zone(zone)` - Validate zone for errors
- `export_zone(zone)` - Export zone to disk

## Requirements

- Python 3.10+
- MCP library (`pip install mcp`)
- MUD Engine running on localhost:9696 (status port 9697)
- `lib/etc/builderport.token` file with auth token

## Security

- The gateway reads the auth token from `MM32/lib/etc/builderport.token`
- All connections are local (localhost only)
- Transactions ensure atomic updates
- Validation prevents broken world states

## Testing

```bash
# Start the MUD server first
cd ../MM32 && ./start-server.sh 9696

# Run the gateway
cd llm_gateway
python -m llm_gateway.server
```

## Implementation Status

✅ BuilderPort client with full v1 protocol support
✅ MCP server with stdio transport
✅ All design-specified tools implemented
✅ Transaction context management
✅ Base64 encoding/decoding
✅ Error handling with structured responses
