#!/usr/bin/env python3
"""Trace if wld_list affects tx_begin."""

import asyncio


async def test_sequence():
    reader, writer = await asyncio.open_connection("127.0.0.1", 9697)

    # Skip greeting
    await reader.readline()
    await reader.readline()

    # Send hello
    writer.write(b"hello c1gtri32 1\r\n")
    await writer.drain()

    for i in range(3):
        resp = await asyncio.wait_for(reader.readline(), timeout=2)
        decoded = resp.decode().strip()
        if decoded.startswith("OK"):
            print(f"Hello response: {decoded!r}")
            break

    # Try tx_begin immediately
    print("\n1. tx_begin ZONES 0 (immediately after hello):")
    writer.write(b"tx_begin ZONES 0\r\n")
    await writer.drain()

    for i in range(3):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"   [{i}] {decoded!r}")
        except asyncio.TimeoutError:
            print(f"   [{i}] Timeout")
            break

    # Send tx_commit/abort
    writer.write(b"tx_abort\r\n")
    await writer.drain()
    await asyncio.wait_for(reader.readline(), timeout=2)

    # Now do wld_list
    print("\n2. wld_list:")
    writer.write(b"wld_list\r\n")
    await writer.drain()

    zones = []
    for i in range(150):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            if decoded.startswith("DATA ZONE"):
                parts = decoded.split()
                if len(parts) >= 3:
                    zones.append(int(parts[2]))
            if not decoded:
                break
        except asyncio.TimeoutError:
            break

    print(f"   Got {len(zones)} zones")

    # Now try tx_begin again
    print("\n3. tx_begin ZONES 0 (after wld_list):")
    writer.write(b"tx_begin ZONES 0\r\n")
    await writer.drain()

    for i in range(3):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"   [{i}] {decoded!r}")
        except asyncio.TimeoutError:
            print(f"   [{i}] Timeout")
            break

    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(test_sequence())
