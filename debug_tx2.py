#!/usr/bin/env python3
"""Debug tx_begin with proper response handling."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")
    await client.connect()

    print("Test 1: tx_begin ZONES 10")
    await client._send("tx_begin ZONES 10")
    # Read multiple lines to get the actual response
    for i in range(5):
        line = await client._read_line()
        print(f"  Line {i}: {repr(line)}")
        if line.startswith("OK") or line.startswith("ERROR"):
            break

    print("\nTest 2: Checking if already in transaction")
    await client._send("tx_commit")
    for i in range(5):
        line = await client._read_line()
        print(f"  Line {i}: {repr(line)}")
        if line:
            break

    print("\nTest 3: tx_begin ZONES 10 again")
    await client._send("tx_begin ZONES 10")
    for i in range(5):
        line = await client._read_line()
        print(f"  Line {i}: {repr(line)}")
        if line.startswith("OK") or line.startswith("ERROR"):
            break

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
