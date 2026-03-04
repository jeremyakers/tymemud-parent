#!/usr/bin/env python3
"""Debug raw protocol data for room 1204."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697)
    await client.connect()

    # Get raw protocol lines for zone 12
    await client._send("wld_load 12")
    response = await client._read_line()
    print(f"Response: {response}")

    lines = await client._read_bulk_response()

    for line in lines:
        if "1204" in line:
            print(f"Line: {line[:200]}")
            if line.startswith("DATA ROOM "):
                parts = line.split()
                print(f"  Parts count: {len(parts)}")
                for i, p in enumerate(parts[:10]):
                    print(f"  [{i}]: {p[:50] if len(p) > 50 else p}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
