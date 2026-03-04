#!/usr/bin/env python3
"""Test tx_begin with various zone formats."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test_zone(client, zone_str):
    print(f"\nTesting tx_begin ZONES {zone_str}...")
    await client._send(f"tx_begin ZONES {zone_str}")
    for i in range(5):
        line = await client._read_line()
        if line:
            print(f"  Response: {line[:80]}")
            if line.startswith("OK") or line.startswith("ERROR"):
                # Abort if successful
                if line.startswith("OK"):
                    await client._send("tx_abort")
                    await client._read_line()
                return "OK" if line.startswith("OK") else "ERROR"
    return "TIMEOUT"


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")
    await client.connect()

    # Test various zone formats
    tests = [
        "0",
        "1",
        "10",
        "12",
        "0,1",
        "1,2",
        "10,11",
        "12",
    ]

    for zone_str in tests:
        result = await test_zone(client, zone_str)
        print(f"  Result: {result}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
