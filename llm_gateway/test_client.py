#!/usr/bin/env python3
"""Quick test script for LLM Gateway client."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test_client():
    print("🧪 Testing LLM Gateway Client...")
    print()

    client = BuilderPortClient()

    try:
        # Test 1: Connection and HELLO handshake
        print("Test 1: Connecting and authenticating...")
        await client.connect()
        print("✅ Connected and authenticated successfully!")
        print()

        # Test 2: List zones
        print("Test 2: Listing zones...")
        zones = await client.list_zones()
        print(f"✅ Found {len(zones)} zones")
        if zones:
            print(f"   First zone: {zones[0]}")
        print()

        # Test 3: Read a room
        print("Test 3: Reading room 1000...")
        room = await client.get_room(1000)
        print(f"✅ Room data: {room}")
        print()

        # Test 4: Transaction context
        print("Test 4: Testing transaction context...")
        async with client.transaction([10]) as tx:
            print("   Transaction started")
            # Just verify the transaction context works
            print("   Transaction active, would commit on exit...")
        print("✅ Transaction committed successfully!")
        print()

        print("🎉 All client tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await client.disconnect()
        print("\n🔌 Disconnected from BuilderPort")

    return 0


if __name__ == "__main__":
    exit(asyncio.run(test_client()))
