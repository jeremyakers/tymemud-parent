#!/usr/bin/env python3
"""Simple test using the fixed client."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")
from client import BuilderPortClient


async def simple_test():
    print("=" * 70)
    print("TYMEMUD LLM GATEWAY - SIMPLE TEST")
    print("=" * 70)
    print()

    client = BuilderPortClient()
    print(f"Token: {client.token}")
    print()

    try:
        print("Connecting...")
        await asyncio.wait_for(client.connect(), timeout=10)
        print("✅ Connected successfully!")
        print()

        print("Testing list_zones...")
        zones = await asyncio.wait_for(client.list_zones(), timeout=10)
        print(f"✅ Found {len(zones)} zones")
        print()
        print("First 5 zones:")
        for zone in zones[:5]:
            print(f"  - Zone {zone['vnum']}: {zone['name']}")
        print()

        print("Testing get_room(1000)...")
        room = await asyncio.wait_for(client.get_room(1000), timeout=10)
        print(f"✅ Room data: {room}")
        print()

        print("Disconnecting...")
        await client.disconnect()
        print("✅ Disconnected successfully!")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_test())
