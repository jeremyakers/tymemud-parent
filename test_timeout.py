#!/usr/bin/env python3
"""Test client directly with asyncio timeout wrapper."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test_with_timeout():
    """Test transaction with global timeout."""
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")

    try:
        # Connect with timeout
        await asyncio.wait_for(client.connect(), timeout=5.0)
        print("✓ Connected", flush=True)

        # Transaction with timeout
        print("Starting transaction...", flush=True)
        print("Calling tx_begin...", flush=True)
        await client._send("tx_begin ZONES 471")
        print("Reading tx_begin response...", flush=True)
        for i in range(10):
            resp = await client._read_line(timeout=2.0)
            print(f"  Response {i}: {repr(resp)}", flush=True)
            if resp.startswith("OK"):
                break
        print("Sending tx_commit...", flush=True)
        await client._send("tx_commit")
        print("Reading tx_commit response...", flush=True)
        for i in range(10):
            resp = await client._read_line(timeout=2.0)
            print(f"  Response {i}: {repr(resp)}", flush=True)
            if resp.startswith("OK"):
                break
        print("✓ Transaction committed", flush=True)

        await client.disconnect()
        print("✓ Success!", flush=True)
        return True

    except asyncio.TimeoutError:
        print("✗ TIMEOUT - operation took too long", flush=True)
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}", flush=True)
        return False


if __name__ == "__main__":
    result = asyncio.run(test_with_timeout())
    sys.exit(0 if result else 1)
