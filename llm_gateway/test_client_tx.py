#!/usr/bin/env python3
"""Trace full transaction flow with actual client."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")
from client import BuilderPortClient


async def trace_client_transaction():
    print("=" * 70)
    print("CLIENT TRANSACTION TRACE")
    print("=" * 70)
    print()

    client = BuilderPortClient()
    print(f"Token: {client.token}")
    print()

    try:
        print("Connecting...")
        await client.connect()
        print("✅ Connected")
        print()

        # Manually trace transaction
        print("Sending: tx_begin ZONES 0")
        await client._send("tx_begin ZONES 0")

        print("Reading response lines:")
        for i in range(5):
            resp = await client._read_line()
            print(f"  [{i}] {resp!r}")
            if not resp:
                continue
            if resp.startswith("OK"):
                print("  -> Transaction started successfully!")
                break
            if resp.startswith("ERROR"):
                code, msg = client._parse_error(resp)
                decoded_msg = client.decode_text(msg)
                print(f"  -> Error {code}: {decoded_msg}")
                break

        await client.disconnect()
        print("\n✅ Disconnected")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(trace_client_transaction())
