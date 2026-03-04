#!/usr/bin/env python3
"""Test tx_begin with zone 0."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")
    await client.connect()

    print("Testing tx_begin with zone 0...")
    await client._send("tx_begin ZONES 0")
    for i in range(5):
        line = await client._read_line()
        print(f"  Line {i}: {repr(line)}")
        if line.startswith("OK") or line.startswith("ERROR"):
            break

    print("\nTesting room_patch in transaction...")
    await client._send("room_patch 0 NAME VGVzdA")  # "Test" in base64
    for i in range(3):
        line = await client._read_line()
        print(f"  Line {i}: {repr(line)}")
        if line:
            break

    print("\nTesting tx_abort...")
    await client._send("tx_abort")
    for i in range(3):
        line = await client._read_line()
        print(f"  Line {i}: {repr(line)}")
        if line:
            break

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
