#!/usr/bin/env python3
"""Test fixed client - simple transaction test."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    print("Testing fixed client...", flush=True)
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")
    await client.connect()
    print("Connected!", flush=True)

    try:
        print("\nTest: Transaction with validation", flush=True)
        async with client.transaction([471]) as tx:
            print("Transaction started, validating zone 471...", flush=True)
            await tx.validate([471])
            print("Validation passed!", flush=True)
        print("Transaction committed successfully!", flush=True)

        print("\nTest: Read room 1000", flush=True)
        room = await client.get_room(1000)
        print(f"Room name: {room['name']}")

    except Exception as e:
        print(f"Error: {e}", flush=True)
        import traceback

        traceback.print_exc()
    finally:
        await client.disconnect()
        print("Disconnected", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
