#!/usr/bin/env python3
"""Test all 7 MCP tools."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient

HOST = "127.0.0.1"
PORT = 9697
TOKEN = "c1gtri32"


async def test_all_tools():
    client = BuilderPortClient(host=HOST, port=PORT, token=TOKEN)
    await client.connect()

    print("=" * 60)
    print("1. Testing read_room (Room 1000)")
    room = await client.get_room(1000)
    if room:
        print(f"  ✓ Name: {room['name']}")
        print(f"  ✓ Desc length: {len(room['description'])}")
        print(f"  ✓ Exits: {len(room['exits'])}")
    else:
        print("  ✗ FAILED")

    print("\n2. Testing list_zones")
    zones = await client.list_zones()
    print(f"  ✓ Found {zones['count']} zones")
    print(f"  ✓ Sectors: {len(zones['sector_types'])}")

    print("\n3. Testing update_room (non-destructive patch)")
    try:
        async with client.transaction([10]) as tx:
            # Just update the name slightly
            await tx.room_patch(1000, name="Beginning Room Test")
            await tx.room_patch(1000, name="Beginning Room")  # Restore
        print("  ✓ Room patch successful")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\n4. Testing create_room (destructive full replace)")
    try:
        async with client.transaction([99]) as tx:
            await tx.room_full(
                9900,
                99,
                sector=0,
                width=10,
                height=10,
                flags=0,
                name="Test Room 9900",
                desc="This is a test room for the MCP gateway.\r\n",
            )
        print("  ✓ Room create successful")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\n5. Testing link_rooms")
    try:
        async with client.transaction([99]) as tx:
            await tx.link_rooms(9900, 0, -1, mode="ONEWAY")  # North exit to nowhere
        print("  ✓ Link rooms successful")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\n6. Testing validate_zone")
    try:
        async with client.transaction([10]) as tx:
            await tx.validate([10])
        print("  ✓ Zone 10 validation passed")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\n7. Testing export_zone")
    try:
        async with client.transaction([10]) as tx:
            await tx.validate([10])
            await tx.export([10])
        print("  ✓ Zone 10 export successful")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\n" + "=" * 60)
    print("All tests completed!")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_all_tools())
