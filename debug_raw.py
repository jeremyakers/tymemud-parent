#!/usr/bin/env python3
"""Debug trace client communication."""

import asyncio
import sys


async def test():
    reader, writer = await asyncio.open_connection("127.0.0.1", 9697)
    print("Connected!", flush=True)

    # Wait for greeting
    await asyncio.sleep(0.1)

    # Send HELLO
    writer.write(b"hello c1gtri32 1\r\n")
    await writer.drain()
    print("Sent HELLO", flush=True)

    # Read responses
    print("\nReading HELLO response...", flush=True)
    for i in range(5):
        line = await asyncio.wait_for(reader.readline(), timeout=1.0)
        line_str = line.decode().strip()
        print(f"  Line {i}: {repr(line_str)}", flush=True)
        if line_str.startswith("OK"):
            break

    # Send wld_list ALL
    writer.write(b"wld_list ALL\r\n")
    await writer.drain()
    print("\nSent wld_list ALL", flush=True)

    # Read response
    print("\nReading wld_list response...", flush=True)
    line = await asyncio.wait_for(reader.readline(), timeout=2.0)
    line_str = line.decode().strip()
    print(f"  First line: {repr(line_str)}", flush=True)

    if line_str.startswith("OK"):
        print("  Got OK, reading bulk...", flush=True)
        count = 0
        for i in range(200):
            try:
                line = await asyncio.wait_for(reader.readline(), timeout=0.5)
                line_str = line.decode().strip()
                if line_str == "END":
                    print(f"  Got END after {count} DATA lines", flush=True)
                    break
                if line_str.startswith("DATA ZONE"):
                    count += 1
                    if count <= 3:
                        print(f"  DATA ZONE: {line_str[:60]}...", flush=True)
            except asyncio.TimeoutError:
                print(f"  Timeout after {count} lines", flush=True)
                break

    # Send quit
    writer.write(b"quit\r\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    print("\nDone!", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
