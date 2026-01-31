#!/usr/bin/env python3
"""Detailed protocol trace."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")


async def trace_protocol():
    print("=" * 70)
    print("PROTOCOL TRACE")
    print("=" * 70)
    print()

    reader, writer = await asyncio.open_connection("127.0.0.1", 9697)
    print("Connected to 127.0.0.1:9697")
    print()

    # Read first line
    print("Reading line 1...")
    line = await asyncio.wait_for(reader.readline(), timeout=5)
    print(f"  Raw bytes: {line!r}")
    print(f"  Decoded: {line.decode().strip()!r}")
    print()

    # Read second line (banner)
    print("Reading line 2...")
    line = await asyncio.wait_for(reader.readline(), timeout=5)
    print(f"  Raw bytes: {line!r}")
    print(f"  Decoded: {line.decode().strip()!r}")
    print()

    # Try to read a third line (should timeout or get empty)
    print("Reading line 3 (should timeout)...")
    try:
        line = await asyncio.wait_for(reader.readline(), timeout=2)
        print(f"  Raw bytes: {line!r}")
        print(f"  Decoded: {line.decode().strip()!r}")
    except asyncio.TimeoutError:
        print("  Timeout - no more data from server (expected)")
    print()

    # Send hello
    token = "c1gtri32"
    cmd = f"hello {token} 1"
    print(f"Sending: {cmd!r}")
    writer.write(f"{cmd}\r\n".encode())
    await writer.drain()
    print("  Sent!")
    print()

    # Read response
    print("Reading hello response...")
    line = await asyncio.wait_for(reader.readline(), timeout=5)
    print(f"  Raw bytes: {line!r}")
    print(f"  Decoded: {line.decode().strip()!r}")
    print()

    # Try wld_list
    print("Sending: wld_list")
    writer.write(b"wld_list\r\n")
    await writer.drain()

    print("Reading wld_list response...")
    for i in range(30):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  Line {i}: {decoded!r}")
            if decoded == "END" or not decoded:
                break
        except asyncio.TimeoutError:
            print("  Timeout")
            break

    writer.close()
    await writer.wait_closed()
    print()
    print("Disconnected")


if __name__ == "__main__":
    asyncio.run(trace_protocol())
