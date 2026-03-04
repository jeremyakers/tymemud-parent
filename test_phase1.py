#!/usr/bin/env python3
"""Test Phase 1 - Single zone transaction fix."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")
    await client.connect()

    print("Test 1: Single zone transaction (471)")
    try:
        async with client.transaction([471]) as tx:
            print("  ✓ Transaction started successfully")
        print("  ✓ Transaction committed successfully")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\nTest 2: Multiple zones transaction (471,472)")
    try:
        async with client.transaction([471, 472]) as tx:
            print("  ✓ Transaction started successfully")
        print("  ✓ Transaction committed successfully")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\nTest 3: Zone 10 (should work now)")
    try:
        async with client.transaction([10]) as tx:
            print("  ✓ Transaction started successfully")
        print("  ✓ Transaction committed successfully")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test())
