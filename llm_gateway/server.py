"""MCP Server for LLM Gateway - Exposes safe tools for world building."""

import asyncio
import sys
from mcp.server import Server
from mcp.types import TextContent, Tool
from mcp.server.stdio import stdio_server

try:
    from .client import BuilderPortClient, BuilderPortError
except ImportError:
    from client import BuilderPortClient, BuilderPortError


# Create the MCP server
app = Server("tymemud-gateway")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the LLM."""
    return [
        Tool(
            name="read_room",
            description="Read room data from the MUD world database",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "BuilderPort host address (e.g., 127.0.0.1)",
                    },
                    "port": {
                        "type": "integer",
                        "description": "BuilderPort status port (e.g., 9697)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Authentication token for BuilderPort",
                    },
                    "vnum": {
                        "type": "integer",
                        "description": "Virtual room number (vnum) to read",
                    },
                },
                "required": ["host", "port", "token", "vnum"],
            },
        ),
        Tool(
            name="list_zones",
            description="List all available zones in the MUD world",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "BuilderPort host address (e.g., 127.0.0.1)",
                    },
                    "port": {
                        "type": "integer",
                        "description": "BuilderPort status port (e.g., 9697)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Authentication token for BuilderPort",
                    },
                },
                "required": ["host", "port", "token"],
            },
        ),
        Tool(
            name="update_room",
            description="Update specific fields of a room (non-destructive). Requires transaction context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "BuilderPort host address (e.g., 127.0.0.1)",
                    },
                    "port": {
                        "type": "integer",
                        "description": "BuilderPort status port (e.g., 9697)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Authentication token for BuilderPort",
                    },
                    "vnum": {"type": "integer", "description": "Room vnum to update"},
                    "zone": {
                        "type": "integer",
                        "description": "Zone number for transaction context",
                    },
                    "name": {
                        "type": "string",
                        "description": "New room name (optional)",
                    },
                    "desc": {
                        "type": "string",
                        "description": "New room description (optional)",
                    },
                    "sector": {
                        "type": "integer",
                        "description": "Sector type (optional)",
                    },
                    "flags": {
                        "type": "integer",
                        "description": "Room flags (optional)",
                    },
                    "width": {
                        "type": "integer",
                        "description": "Room width (optional)",
                    },
                    "height": {
                        "type": "integer",
                        "description": "Room height (optional)",
                    },
                },
                "required": ["host", "port", "token", "vnum", "zone"],
            },
        ),
        Tool(
            name="create_room",
            description="Create or fully replace a room (destructive). Clears exits and extras. Requires transaction context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "BuilderPort host address (e.g., 127.0.0.1)",
                    },
                    "port": {
                        "type": "integer",
                        "description": "BuilderPort status port (e.g., 9697)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Authentication token for BuilderPort",
                    },
                    "vnum": {"type": "integer", "description": "Room vnum"},
                    "zone": {"type": "integer", "description": "Zone number"},
                    "sector": {
                        "type": "integer",
                        "description": "Sector type",
                        "default": 0,
                    },
                    "width": {
                        "type": "integer",
                        "description": "Room width",
                        "default": 10,
                    },
                    "height": {
                        "type": "integer",
                        "description": "Room height",
                        "default": 10,
                    },
                    "flags": {
                        "type": "integer",
                        "description": "Room flags",
                        "default": 0,
                    },
                    "name": {"type": "string", "description": "Room name"},
                    "desc": {"type": "string", "description": "Room description"},
                },
                "required": ["host", "port", "token", "vnum", "zone", "name", "desc"],
            },
        ),
        Tool(
            name="link_rooms",
            description="Create or update an exit between two rooms. Creates bidirectional link by default. Requires transaction context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "BuilderPort host address (e.g., 127.0.0.1)",
                    },
                    "port": {
                        "type": "integer",
                        "description": "BuilderPort status port (e.g., 9697)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Authentication token for BuilderPort",
                    },
                    "from_vnum": {"type": "integer", "description": "Source room vnum"},
                    "direction": {
                        "type": "integer",
                        "description": "Direction (0-10: N, E, S, W, U, D, NE, NW, SE, SW, etc.)",
                    },
                    "to_vnum": {
                        "type": "integer",
                        "description": "Target room vnum (-1 for no exit)",
                    },
                    "zone": {
                        "type": "integer",
                        "description": "Zone number for transaction context",
                    },
                    "flags": {
                        "type": "integer",
                        "description": "Exit flags (0=open, 1=closed, etc.)",
                        "default": 0,
                    },
                    "key": {
                        "type": "integer",
                        "description": "Key object vnum (-1 for none)",
                        "default": -1,
                    },
                    "desc": {
                        "type": "string",
                        "description": "Exit description",
                        "default": "",
                    },
                    "keywords": {
                        "type": "string",
                        "description": "Exit keywords",
                        "default": "",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Link mode: BIDIR (default) or ONEWAY",
                        "enum": ["BIDIR", "ONEWAY"],
                        "default": "BIDIR",
                    },
                },
                "required": [
                    "host",
                    "port",
                    "token",
                    "from_vnum",
                    "direction",
                    "to_vnum",
                    "zone",
                ],
            },
        ),
        Tool(
            name="validate_zone",
            description="Validate a zone for errors (orphaned rooms, missing links, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "BuilderPort host address (e.g., 127.0.0.1)",
                    },
                    "port": {
                        "type": "integer",
                        "description": "BuilderPort status port (e.g., 9697)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Authentication token for BuilderPort",
                    },
                    "zone": {
                        "type": "integer",
                        "description": "Zone number to validate",
                    },
                },
                "required": ["host", "port", "token", "zone"],
            },
        ),
        Tool(
            name="export_zone",
            description="Export a zone to disk (writes .wld file). Only succeeds if validation passes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "BuilderPort host address (e.g., 127.0.0.1)",
                    },
                    "port": {
                        "type": "integer",
                        "description": "BuilderPort status port (e.g., 9697)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Authentication token for BuilderPort",
                    },
                    "zone": {"type": "integer", "description": "Zone number to export"},
                },
                "required": ["host", "port", "token", "zone"],
            },
        ),
    ]


async def _create_client(arguments: dict) -> BuilderPortClient:
    """Create a fresh BuilderPortClient from tool arguments."""
    host = arguments["host"]
    port = arguments["port"]
    token = arguments["token"]
    return BuilderPortClient(host=host, port=port, token=token)


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from the LLM."""

    try:
        if name == "read_room":
            client = await _create_client(arguments)
            await client.connect()
            try:
                room = await client.get_room(arguments["vnum"])
                if room is None:
                    return [
                        TextContent(
                            type="text", text=f"Room {arguments['vnum']} not found"
                        )
                    ]

                # Format comprehensive room data
                lines = [
                    f"Room {room['vnum']}: {room['name']}",
                    f"Zone: {room['zone']}, Sector: {room['sector']}, Size: {room['width']}x{room['height']}",
                    f"Flags: {room['flags']}",
                    f"Special Function: {room['special_function'] or 'None'}",
                    "",
                    "Description:",
                    room["description"] if room["description"] else "(no description)",
                    "",
                ]

                # Format exits
                if room["exits"]:
                    lines.append("Exits:")
                    for exit in room["exits"]:
                        lines.append(
                            f"  {exit['direction_name']} -> Room {exit['to_vnum']}"
                        )
                        if exit["description"]:
                            lines.append(f"    Desc: {exit['description']}")
                        if exit["keywords"]:
                            lines.append(f"    Keywords: {exit['keywords']}")
                        if exit["key"] != -1:
                            lines.append(f"    Key required: Object {exit['key']}")
                        if exit["flags"] != 0:
                            lines.append(f"    Flags: {exit['flags']}")
                else:
                    lines.append("Exits: None")

                # Format extra descriptions
                if room["extra_descriptions"]:
                    lines.extend(["", "Extra Descriptions:"])
                    for ed in room["extra_descriptions"]:
                        lines.append(f"  Keywords: {ed['keywords']}")
                        lines.append(f"  {ed['description']}")

                return [TextContent(type="text", text="\n".join(lines))]
            finally:
                await client.disconnect()

        elif name == "list_zones":
            client = await _create_client(arguments)
            await client.connect()
            try:
                data = await client.list_zones()

                # Format comprehensive zones data
                lines = []

                # Zones list
                lines.append(f"=== ZONES ({data['count']}) ===")
                for zone in data["zones"]:
                    lines.append(f"  Zone {zone['vnum']}: {zone['name']}")

                # Sector types
                if data["sector_types"]:
                    lines.extend(["", "=== SECTOR TYPES ==="])
                    for sector in data["sector_types"]:
                        lines.append(f"  {sector['id']}: {sector['name']}")

                # Room flags
                if data["room_flags"]:
                    lines.extend(["", "=== ROOM FLAGS ==="])
                    for i, flag in enumerate(data["room_flags"]):
                        lines.append(f"  Bit {i}: {flag}")

                # Special functions
                if data["special_functions"]:
                    lines.extend(["", "=== SPECIAL FUNCTIONS ==="])
                    for func in data["special_functions"]:
                        lines.append(f"  {func}")

                return [TextContent(type="text", text="\n".join(lines))]
            finally:
                await client.disconnect()

        elif name == "update_room":
            client = await _create_client(arguments)
            await client.connect()
            try:
                vnum = arguments["vnum"]
                zone = arguments["zone"]

                # Extract optional fields
                fields = {}
                for key in ["name", "desc", "sector", "flags", "width", "height"]:
                    if key in arguments:
                        fields[key] = arguments[key]

                async with client.transaction([zone]) as tx:
                    await tx.room_patch(vnum, **fields)

                return [
                    TextContent(type="text", text=f"Room {vnum} updated successfully")
                ]
            finally:
                await client.disconnect()

        elif name == "create_room":
            client = await _create_client(arguments)
            await client.connect()
            try:
                vnum = arguments["vnum"]
                zone = arguments["zone"]
                sector = arguments.get("sector", 0)
                width = arguments.get("width", 10)
                height = arguments.get("height", 10)
                flags = arguments.get("flags", 0)
                name = arguments["name"]
                desc = arguments["desc"]

                async with client.transaction([zone]) as tx:
                    await tx.room_full(
                        vnum, zone, sector, width, height, flags, name, desc
                    )

                return [
                    TextContent(type="text", text=f"Room {vnum} created successfully")
                ]
            finally:
                await client.disconnect()

        elif name == "link_rooms":
            client = await _create_client(arguments)
            await client.connect()
            try:
                from_vnum = arguments["from_vnum"]
                direction = arguments["direction"]
                to_vnum = arguments["to_vnum"]
                zone = arguments["zone"]
                flags = arguments.get("flags", 0)
                key = arguments.get("key", -1)
                desc = arguments.get("desc", "")
                keywords = arguments.get("keywords", "")
                mode = arguments.get("mode", "BIDIR")

                async with client.transaction([zone]) as tx:
                    await tx.link_rooms(
                        from_vnum, direction, to_vnum, flags, key, desc, keywords, mode
                    )

                return [
                    TextContent(
                        type="text",
                        text=f"Exit from {from_vnum} to {to_vnum} ({mode}) created",
                    )
                ]
            finally:
                await client.disconnect()

        elif name == "validate_zone":
            client = await _create_client(arguments)
            await client.connect()
            try:
                zone = arguments["zone"]

                async with client.transaction([zone]) as tx:
                    await tx.validate([zone])

                return [TextContent(type="text", text=f"Zone {zone} is valid")]
            finally:
                await client.disconnect()

        elif name == "export_zone":
            client = await _create_client(arguments)
            await client.connect()
            try:
                zone = arguments["zone"]

                async with client.transaction([zone]) as tx:
                    await tx.export([zone])

                return [TextContent(type="text", text=f"Zone {zone} exported to disk")]
            finally:
                await client.disconnect()

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except BuilderPortError as e:
        return [TextContent(type="text", text=f"Error: {e.message} (code {e.code})")]
    except Exception as e:
        import traceback

        return [
            TextContent(
                type="text", text=f"Internal error: {str(e)}\n{traceback.format_exc()}"
            )
        ]


def main():
    """Main entry point - runs the MCP server over stdio."""
    asyncio.run(run_server())


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    main()
