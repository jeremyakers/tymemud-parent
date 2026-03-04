#!/usr/bin/env python3
"""Debug list_zones parsing."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    print("Creating client...", flush=True)
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")

    print("Connecting...", flush=True)
    await client.connect()
    print("Connected!", flush=True)

    print("\nTesting list_zones(mode='all')...", flush=True)
    result = await client.list_zones(mode="all")
    print(f"Result: {result}", flush=True)

    print("\nTesting list_sectors()...", flush=True)
    sectors = await client.list_sectors()
    print(f"Sectors count: {len(sectors)}", flush=True)
    if sectors:
        print(f"First sector: {sectors[0]}", flush=True)

    print("\nTesting list_room_flags()...", flush=True)
    flags = await client.list_room_flags()
    print(f"Flags count: {len(flags)}", flush=True)
    if flags:
        print(f"First flag: {flags[0]}", flush=True)

    await client.disconnect()
    print("\nDone!", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
