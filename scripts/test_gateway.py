#!/usr/bin/env python3
"""Quick test to verify the gateway can start and connect to BuilderPort."""

import asyncio
import sys
import os

# Add parent dir to path so we can import llm_gateway
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_gateway.client import BuilderPortClient


async def test():
    print("Testing BuilderPort connection...")
    client = BuilderPortClient()
    try:
        await client.connect()
        print("✅ Connected to BuilderPort successfully!")

        zones = await client.list_zones()
        print(f"✅ List zones: Found {zones.get('count', 0)} zones")

        room = await client.get_room(1000)
        print(f"✅ Get room 1000: {room.get('name', 'N/A') if room else 'Not found'}")

        await client.disconnect()
        print("✅ Disconnected cleanly")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(test()))
