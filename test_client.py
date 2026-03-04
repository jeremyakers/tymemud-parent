#!/usr/bin/env python3
"""Debug client list_zones."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def test():
    client = BuilderPortClient(host="127.0.0.1", port=9697, token="c1gtri32")

    print("Connecting...")
    await client.connect()
    print("Connected!")

    print("\nSending wld_list ALL...")
    await client._send("wld_list ALL")

    print("Reading response...")
    response = await client._read_line()
    print(f"First response: {repr(response)}")

    if response.startswith("OK"):
        print("Got OK, reading bulk data...")
        lines = await client._read_bulk_response()
        print(f"Got {len(lines)} lines")
        for i, line in enumerate(lines[:5]):
            print(f"  Line {i}: {repr(line[:60])}...")

    await client.disconnect()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(test())
