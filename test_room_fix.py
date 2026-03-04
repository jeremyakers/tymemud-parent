#!/usr/bin/env python3
"""Quick test to verify room parsing fix."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697)
    await client.connect()

    # Test room 1000
    print("=== Room 1000 ===")
    room = await client.get_room(1000)
    if room:
        print(f"Name: {repr(room['name'])}")
        print(f"Desc: {repr(room['description'])}")
        print(f"OK: name='{room['name']}', desc length={len(room['description'])}")
    else:
        print("ERROR: Room not found")

    # Test room 1204
    print("\n=== Room 1204 ===")
    room = await client.get_room(1204)
    if room:
        print(f"Name: {repr(room['name'])}")
        print(
            f"Desc: {repr(room['description'][:100])}..."
            if room["description"]
            else "Desc: None"
        )
        print(
            f"OK: name='{room['name']}', desc length={len(room['description']) if room['description'] else 0}"
        )
    else:
        print("ERROR: Room not found")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
