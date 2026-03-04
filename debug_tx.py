#!/usr/bin/env python3
"""Debug transaction command."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")
    await client.connect()

    # Test tx_begin command directly
    print("Testing tx_begin...")
    await client._send("tx_begin ZONES 10")
    response = await client._read_line()
    print(f"Response: {response}")

    # Try alternative formats
    print("\nTrying 'tx_begin 10'...")
    await client._send("tx_begin 10")
    response = await client._read_line()
    print(f"Response: {response}")

    print("\nTrying 'tx_begin ZONE 10'...")
    await client._send("tx_begin ZONE 10")
    response = await client._read_line()
    print(f"Response: {response}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
