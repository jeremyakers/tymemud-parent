#!/usr/bin/env python3
"""Trace transaction with wld_list first."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")
from client import BuilderPortClient


async def trace_with_wldlist():
    client = BuilderPortClient()

    print("Connecting...")
    await client.connect()
    print("✅ Connected\n")

    print("Calling list_zones()...")
    zones = await client.list_zones()
    print(f"✅ Got {len(zones)} zones\n")

    print("Starting transaction for zone 0...")
    try:
        async with client.transaction([0]) as tx:
            print("✅ Transaction started!")
            print(f"Transaction zones: {tx.zones}")
            print(f"Transaction active: {tx.active}")
    except Exception as e:
        print(f"❌ Transaction failed: {e}")
        import traceback

        traceback.print_exc()

    await client.disconnect()
    print("\n✅ Disconnected")


if __name__ == "__main__":
    asyncio.run(trace_with_wldlist())
