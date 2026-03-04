#!/usr/bin/env python3
"""Debug validate_zone timeout issue."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    print("Connecting...", flush=True)
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")
    await client.connect()
    print("Connected!", flush=True)

    try:
        # Test 1: Simple who command
        print("\n=== Test 1: who command ===", flush=True)
        await client._send("who")
        print("Sent 'who', reading response...", flush=True)
        for i in range(3):
            response = await client._read_line()
            print(f"  Response {i}: {repr(response)}", flush=True)
            if not response:
                break

        # Test 2: tx_begin
        print("\n=== Test 2: tx_begin ZONES 471 ===", flush=True)
        cmd = "tx_begin ZONES 471"
        print(f"Sending: {repr(cmd)}", flush=True)
        await client._send(cmd)
        print(f"Sent {len(cmd)}+2 bytes, reading response...", flush=True)
        for i in range(5):
            response = await client._read_line()
            print(f"  Response {i}: {repr(response)}", flush=True)
            if response.startswith("OK") or response.startswith("ERROR"):
                break
            if not response and i > 0:
                break

    except Exception as e:
        print(f"Error: {e}", flush=True)
        import traceback

        traceback.print_exc()
    finally:
        print("\nDisconnecting...", flush=True)
        await client._send("quit")
        client.writer.close()
        await client.writer.wait_closed()
        print("Disconnected", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
