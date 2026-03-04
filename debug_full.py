#!/usr/bin/env python3
"""Debug full line length for room 1204."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697)
    await client.connect()

    await client._send("wld_load 12")
    await client._read_line()

    lines = await client._read_bulk_response()

    for line in lines:
        if line.startswith("DATA ROOM 1204"):
            print(f"Full line length: {len(line)}")
            print(f"Line: {line}")
            parts = line.split(maxsplit=9)
            print(f"\nSplit into {len(parts)} parts with maxsplit=9")
            for i, p in enumerate(parts):
                print(f"  [{i}]: len={len(p)} {p[:80]}{'...' if len(p) > 80 else ''}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
