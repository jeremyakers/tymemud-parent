#!/usr/bin/env python3
"""Raw socket test."""

import asyncio


async def test():
    reader, writer = await asyncio.open_connection("127.0.0.1", 9697)
    print("Connected!")

    # Drain greeting
    await asyncio.sleep(0.1)
    for _ in range(5):
        try:
            data = await asyncio.wait_for(reader.read(1024), timeout=0.2)
            if data:
                print(f"Greeting: {data!r}")
        except asyncio.TimeoutError:
            break

    # Send HELLO
    writer.write(b"hello c1gtri32 1\r\n")
    await writer.drain()
    print("\nSent HELLO")

    # Read response with raw read
    await asyncio.sleep(0.1)
    data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
    print(f"HELLO response: {data!r}")

    # Send wld_list
    writer.write(b"wld_list ALL\r\n")
    await writer.drain()
    print("\nSent wld_list ALL")

    # Read response
    await asyncio.sleep(0.1)
    data = await asyncio.wait_for(reader.read(4096), timeout=1.0)
    print(f"wld_list response ({len(data)} bytes): {data[:500]!r}")

    writer.write(b"quit\r\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    print("\nDone!")


asyncio.run(test())
