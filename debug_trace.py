#!/usr/bin/env python3
"""Debug trace of transaction flow."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")
from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")

    print("=== Step 1: Connect ===", flush=True)
    await client.connect()
    print("Connected (authed)", flush=True)

    print("\n=== Step 2: Send tx_begin ===", flush=True)
    await client._send("tx_begin ZONES 471")
    print("Sent tx_begin ZONES 471", flush=True)

    print("\n=== Step 3: Read tx_begin response ===", flush=True)
    for i in range(10):
        line = await client._read_line()
        print(f"  Line {i}: {repr(line)}", flush=True)
        if line.startswith("OK") or line.startswith("ERROR"):
            print(f"  -> Got result: {line}", flush=True)
            break

    print("\n=== Step 4: Send validate ===", flush=True)
    await client._send("validate ZONES 471")
    print("Sent validate ZONES 471", flush=True)

    print("\n=== Step 5: Read validate response ===", flush=True)
    for i in range(10):
        line = await client._read_line()
        print(f"  Line {i}: {repr(line)}", flush=True)
        if line.startswith("OK") or line.startswith("ERROR"):
            print(f"  -> Got result: {line}", flush=True)
            break
        if not line:
            print("  -> Empty line, continuing...", flush=True)

    print("\n=== Step 6: Send quit and cleanup ===", flush=True)
    await client._send("quit")
    print("Sent quit, reading any remaining responses...", flush=True)
    for i in range(5):
        try:
            line = await asyncio.wait_for(client._read_line(), timeout=0.5)
            print(f"  Quit response {i}: {repr(line)}", flush=True)
        except asyncio.TimeoutError:
            print(f"  Timeout reading quit response {i}", flush=True)
            break
    client.writer.close()
    await client.writer.wait_closed()
    print("Done!", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
