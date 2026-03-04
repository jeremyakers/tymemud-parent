#!/usr/bin/env python3
"""Debug connection and transaction flow."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    print("Creating client...", flush=True)
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")

    print("Opening connection...", flush=True)
    client.reader, client.writer = await asyncio.open_connection(
        client.host, client.port
    )
    print("Connected!", flush=True)

    # Read ALL greeting lines
    print("\nReading greeting lines...", flush=True)
    for i in range(10):
        line = await client._read_line()
        print(f"  Greeting {i}: {repr(line)}", flush=True)
        if not line:
            break

    # Send HELLO
    print("\nSending HELLO...", flush=True)
    await client._send(f"hello {client.token} 1")

    # Read ALL HELLO response lines
    print("Reading HELLO response...", flush=True)
    for i in range(5):
        line = await client._read_line()
        print(f"  HELLO response {i}: {repr(line)}", flush=True)
        if line.startswith("OK"):
            break

    # Send tx_begin
    print("\nSending tx_begin ZONES 471...", flush=True)
    await client._send("tx_begin ZONES 471")

    # Read response
    print("Reading tx_begin response...", flush=True)
    for i in range(5):
        line = await client._read_line()
        print(f"  tx_begin response {i}: {repr(line)}", flush=True)
        if line.startswith("OK") or line.startswith("ERROR"):
            break

    print("\nDisconnecting...", flush=True)
    await client._send("quit")
    client.writer.close()
    await client.writer.wait_closed()
    print("Done!", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
