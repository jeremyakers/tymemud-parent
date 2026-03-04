#!/usr/bin/env python3
"""Show raw room data responses."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient
import json


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")
    await client.connect()

    # Test room 1000
    print("=== Room 1000 Raw Data ===")
    room = await client.get_room(1000)
    if room:
        print(json.dumps(room, indent=2))
    else:
        print("ERROR: Room not found")

    # Test room 1204
    print("\n=== Room 1204 Raw Data ===")
    room = await client.get_room(1204)
    if room:
        print(json.dumps(room, indent=2, default=str))
    else:
        print("ERROR: Room not found")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
