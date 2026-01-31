#!/usr/bin/env python3
"""Test with actual BuilderPortClient."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")
from client import BuilderPortClient


async def test_real_client():
    client = BuilderPortClient()

    print("Connecting with real BuilderPortClient...")
    await client.connect()
    print(f"Connected! Authed: {client.authed}")
    print()

    print("Calling list_zones...")
    zones = await client.list_zones()
    print(f"Got {len(zones)} zones")
    print()

    print("Trying transaction...")
    try:
        async with client.transaction([0]) as tx:
            print(f"Transaction active: {tx.active}")
    except Exception as e:
        print(f"Transaction error: {e}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_real_client())
