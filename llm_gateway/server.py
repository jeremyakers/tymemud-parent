"""MCP Server for LLM Gateway - Exposes safe tools for world building."""

import asyncio
import sys
from typing import AsyncIterator
from contextlib import asynccontextmanager
from mcp.server import Server
from mcp.types import TextContent, Tool
from mcp.server.stdio import stdio_server

try:
    from .client import BuilderPortClient, BuilderPortError
except ImportError:
    from client import BuilderPortClient, BuilderPortError


class GatewayContext:
    """Context for the MCP server containing the BuilderPort client."""

    def __init__(self):
        self.client: BuilderPortClient = BuilderPortClient()
        self._connected = False

    async def ensure_connected(self):
        """Connect if not already connected."""
        if not self._connected:
            await self.client.connect()
            self._connected = True

    async def disconnect(self):
        """Disconnect client."""
        if self._connected:
            await self.client.disconnect()
            self._connected = False


@asynccontextmanager
async def app_lifespan(server: Server) -> AsyncIterator[GatewayContext]:
    """Manage application lifecycle."""
    context = GatewayContext()
    try:
        yield context
    finally:
        await context.disconnect()


# Create the MCP server
app = Server("tymemud-gateway", lifespan=app_lifespan)


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
                    "vnum": {
                        "type": "integer",
                        "description": "Virtual room number (vnum) to read",
                    }
                },
                "required": ["vnum"],
            },
        ),
        Tool(
            name="list_zones",
            description="List all available zones in the MUD world",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="update_room",
            description="Update specific fields of a room (non-destructive). Requires transaction context.",
            inputSchema={
                "type": "object",
                "properties": {
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
                "required": ["vnum", "zone"],
            },
        ),
        Tool(
            name="create_room",
            description="Create or fully replace a room (destructive). Clears exits and extras. Requires transaction context.",
            inputSchema={
                "type": "object",
                "properties": {
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
                "required": ["vnum", "zone", "name", "desc"],
            },
        ),
        Tool(
            name="link_rooms",
            description="Create or update an exit between two rooms. Creates bidirectional link by default. Requires transaction context.",
            inputSchema={
                "type": "object",
                "properties": {
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
                "required": ["from_vnum", "direction", "to_vnum", "zone"],
            },
        ),
        Tool(
            name="validate_zone",
            description="Validate a zone for errors (orphaned rooms, missing links, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone": {
                        "type": "integer",
                        "description": "Zone number to validate",
                    }
                },
                "required": ["zone"],
            },
        ),
        Tool(
            name="export_zone",
            description="Export a zone to disk (writes .wld file). Only succeeds if validation passes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone": {"type": "integer", "description": "Zone number to export"}
                },
                "required": ["zone"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from the LLM."""
    ctx = app.request_context.lifespan_context

    try:
        if name == "read_room":
            await ctx.ensure_connected()
            room = await ctx.client.get_room(arguments["vnum"])
            return [TextContent(type="text", text=str(room))]

        elif name == "list_zones":
            await ctx.ensure_connected()
            zones = await ctx.client.list_zones()
            return [TextContent(type="text", text=str(zones))]

        elif name == "update_room":
            await ctx.ensure_connected()
            vnum = arguments["vnum"]
            zone = arguments["zone"]

            # Extract optional fields
            fields = {}
            for key in ["name", "desc", "sector", "flags", "width", "height"]:
                if key in arguments:
                    fields[key] = arguments[key]

            async with ctx.client.transaction([zone]) as tx:
                await tx.room_patch(vnum, **fields)

            return [TextContent(type="text", text=f"Room {vnum} updated successfully")]

        elif name == "create_room":
            await ctx.ensure_connected()
            vnum = arguments["vnum"]
            zone = arguments["zone"]
            sector = arguments.get("sector", 0)
            width = arguments.get("width", 10)
            height = arguments.get("height", 10)
            flags = arguments.get("flags", 0)
            name = arguments["name"]
            desc = arguments["desc"]

            async with ctx.client.transaction([zone]) as tx:
                await tx.room_full(vnum, zone, sector, width, height, flags, name, desc)

            return [TextContent(type="text", text=f"Room {vnum} created successfully")]

        elif name == "link_rooms":
            await ctx.ensure_connected()
            from_vnum = arguments["from_vnum"]
            direction = arguments["direction"]
            to_vnum = arguments["to_vnum"]
            zone = arguments["zone"]
            flags = arguments.get("flags", 0)
            key = arguments.get("key", -1)
            desc = arguments.get("desc", "")
            keywords = arguments.get("keywords", "")
            mode = arguments.get("mode", "BIDIR")

            async with ctx.client.transaction([zone]) as tx:
                await tx.link_rooms(
                    from_vnum, direction, to_vnum, flags, key, desc, keywords, mode
                )

            return [
                TextContent(
                    type="text",
                    text=f"Exit from {from_vnum} to {to_vnum} ({mode}) created",
                )
            ]

        elif name == "validate_zone":
            await ctx.ensure_connected()
            zone = arguments["zone"]

            async with ctx.client.transaction([zone]) as tx:
                await tx.validate([zone])

            return [TextContent(type="text", text=f"Zone {zone} is valid")]

        elif name == "export_zone":
            await ctx.ensure_connected()
            zone = arguments["zone"]

            async with ctx.client.transaction([zone]) as tx:
                await tx.export([zone])

            return [TextContent(type="text", text=f"Zone {zone} exported to disk")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except BuilderPortError as e:
        return [TextContent(type="text", text=f"Error: {e.message} (code {e.code})")]
    except Exception as e:
        return [TextContent(type="text", text=f"Internal error: {str(e)}")]


def main():
    """Main entry point - runs the MCP server over stdio."""
    asyncio.run(run_server())


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    main()
