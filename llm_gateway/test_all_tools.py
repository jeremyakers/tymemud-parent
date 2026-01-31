#!/usr/bin/env python3
"""Comprehensive test showing exact outputs from each MCP tool."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test_all_tools():
    print("=" * 70)
    print("TYMEMUD LLM GATEWAY - TOOL OUTPUT EXAMPLES")
    print("=" * 70)
    print()

    client = BuilderPortClient()
    await client.connect()

    # Tool 1: list_zones
    print("🔧 TOOL: list_zones()")
    print("-" * 70)
    zones = await client.list_zones()
    print(f"Return type: {type(zones)}")
    print(f"Number of zones: {len(zones)}")
    print(f"\nFirst 3 zones:")
    for i, zone in enumerate(zones[:3]):
        print(f"  [{i}] {zone}")
    print(f"\nZone data structure:")
    if zones:
        print(f"  Keys: {list(zones[0].keys())}")
        print(f"  Example: {zones[0]}")
    print()

    # Tool 2: read_room
    print("🔧 TOOL: get_room(1000)")
    print("-" * 70)
    room = await client.get_room(1000)
    print(f"Return type: {type(room)}")
    print(f"Room data: {room}")
    print()

    # Tool 3: read_room (non-existent)
    print("🔧 TOOL: get_room(999999) - Non-existent room")
    print("-" * 70)
    room = await client.get_room(999999)
    print(f"Return type: {type(room)}")
    print(f"Room data: {room}")
    print()

    # Tool 4: Transaction with room_patch
    print("🔧 TOOL: Transaction with room_patch")
    print("-" * 70)
    print("Creating transaction for zones [0]...")
    async with client.transaction([0]) as tx:
        print("  Transaction active")
        print("  Calling tx.room_patch(0, name='Test Room')...")
        await tx.room_patch(0, name="Test Room Name")
        print("  Room patched successfully")
        print("  Transaction will auto-commit on exit...")
    print("✅ Transaction committed")
    print()

    # Verify the update
    print("🔧 VERIFY: Reading room 0 after update")
    print("-" * 70)
    room = await client.get_room(0)
    print(f"Updated room: {room}")
    print()

    # Tool 5: Transaction with room_full
    print("🔧 TOOL: Transaction with room_full (destructive)")
    print("-" * 70)
    async with client.transaction([0]) as tx:
        print("  Creating new room 99 with room_full...")
        await tx.room_full(
            vnum=99,
            zone=0,
            sector=2,  # Field
            width=10,
            height=10,
            flags=0,
            name="A New Test Room",
            desc="This is a test room created by the LLM Gateway.",
        )
        print("  Room created successfully")
    print("✅ Room creation committed")
    print()

    # Tool 6: Transaction with link_rooms
    print("🔧 TOOL: Transaction with link_rooms (BIDIR)")
    print("-" * 70)
    async with client.transaction([0]) as tx:
        print("  Creating bidirectional exit from 0 to 1 (East)...")
        await tx.link_rooms(
            from_vnum=0,
            direction=1,  # East
            to_vnum=1,
            flags=0,
            key=-1,
            desc="A wide corridor.",
            keywords="east corridor",
            mode="BIDIR",
        )
        print("  Exit created successfully")
    print("✅ Exit creation committed")
    print()

    # Tool 7: Transaction with validate
    print("🔧 TOOL: Transaction with validate")
    print("-" * 70)
    async with client.transaction([0]) as tx:
        print("  Validating zone 0...")
        try:
            await tx.validate([0])
            print("  ✅ Zone 10 is valid")
        except Exception as e:
            print(f"  ❌ Validation error: {e}")
    print()

    # Tool 8: Transaction with export
    print("🔧 TOOL: Transaction with export")
    print("-" * 70)
    async with client.transaction([0]) as tx:
        print("  Exporting zone 0 to disk...")
        try:
            await tx.export([0])
            print("  ✅ Zone 10 exported successfully")
        except Exception as e:
            print(f"  ❌ Export error: {e}")
    print()

    # Tool 9: Error handling example
    print("🔧 TOOL: Error handling (unauthorized access)")
    print("-" * 70)
    new_client = BuilderPortClient(token="invalid_token")
    try:
        await new_client.connect()
    except Exception as e:
        print(f"Expected error: {type(e).__name__}")
        print(f"Error message: {e}")
    print()

    await client.disconnect()

    print("=" * 70)
    print("ALL TOOL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all_tools())
