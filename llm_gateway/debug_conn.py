#!/usr/bin/env python3
"""Debug the connection to see what's happening."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")


async def debug_connection():
    print("🔍 Debugging connection to BuilderPort...")
    print()

    reader, writer = await asyncio.open_connection("127.0.0.1", 9697)
    print("✅ Connected to 127.0.0.1:9697")

    # Read all lines until we get something non-empty
    print("\n📨 Reading initial lines...")
    for i in range(5):
        line = await reader.readline()
        print(f"  Line {i}: {repr(line)}")
        if line == b"":
            break

    # Send HELLO
    token = "c1gtri32"
    cmd = f"hello {token} 1\r\n"
    print(f"\n📤 Sending: {repr(cmd)}")
    writer.write(cmd.encode())
    await writer.drain()

    # Read response lines
    print("\n📨 Reading response lines...")
    for i in range(5):
        line = await reader.readline()
        print(f"  Line {i}: {repr(line)}")
        if line == b"":
            break

    # Send quit
    print("\n📤 Sending quit...")
    writer.write(b"quit\r\n")
    await writer.drain()

    writer.close()
    await writer.wait_closed()
    print("\n✅ Connection closed")


if __name__ == "__main__":
    asyncio.run(debug_connection())
