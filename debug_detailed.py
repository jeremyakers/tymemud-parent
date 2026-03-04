#!/usr/bin/env python3
"""Debug list_zones parsing with detailed output."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")

    await client.connect()
    print("Connected!", flush=True)

    print("\nSending: wld_list ALL", flush=True)
    await client._send("wld_list ALL")

    print("Reading response...", flush=True)
    response = await client._read_line()
    print(f"Got response: {repr(response)}", flush=True)

    if response.startswith("OK"):
        print("Response is OK, reading bulk...", flush=True)
        lines = await client._read_bulk_response()
        print(f"Got {len(lines)} lines:", flush=True)
        for i, line in enumerate(lines[:10]):
            print(f"  Line {i}: {repr(line[:80])}...", flush=True)
    else:
        print(f"ERROR: {response}", flush=True)

    await client.disconnect()
    print("\nDone!", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
