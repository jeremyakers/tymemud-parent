#!/usr/bin/env python3
"""Debug client connection step by step."""

import asyncio


async def test():
    print("Opening connection...", flush=True)
    reader, writer = await asyncio.open_connection("127.0.0.1", 9697)
    print("Connected!", flush=True)

    # Wait for greeting
    print("\nDraining greeting...", flush=True)
    await asyncio.sleep(0.1)
    for i in range(10):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=0.1)
            line_str = line.decode().strip()
            print(f"  Drained: {repr(line_str)}", flush=True)
            if not line:
                break
        except asyncio.TimeoutError:
            print("  Timeout (no more greeting)", flush=True)
            break

    # Send HELLO
    print("\nSending HELLO...", flush=True)
    writer.write(b"hello c1gtri32 1\r\n")
    await writer.drain()
    print("Sent, waiting for response...", flush=True)

    # Read response
    line = await asyncio.wait_for(reader.readline(), timeout=2.0)
    line_str = line.decode().strip()
    print(f"Got response: {repr(line_str)}", flush=True)

    if line_str.startswith("OK"):
        print("Authentication successful!", flush=True)

        # Try wld_list
        print("\nSending wld_list ALL...", flush=True)
        writer.write(b"wld_list ALL\r\n")
        await writer.drain()

        # Read OK
        line = await asyncio.wait_for(reader.readline(), timeout=2.0)
        line_str = line.decode().strip()
        print(f"wld_list response: {repr(line_str)}", flush=True)

        if line_str.startswith("OK"):
            print("Reading zones...", flush=True)
            count = 0
            for i in range(200):
                try:
                    line = await asyncio.wait_for(reader.readline(), timeout=0.5)
                    line_str = line.decode().strip()
                    if line_str == "END":
                        print(f"Got END after {count} zones", flush=True)
                        break
                    if line_str.startswith("DATA ZONE"):
                        count += 1
                        if count <= 5:
                            print(f"  Zone {count}: {line_str[:60]}...", flush=True)
                except asyncio.TimeoutError:
                    print(f"Timeout after {count} zones", flush=True)
                    break
    else:
        print(f"Authentication failed: {line_str}", flush=True)

    # Send quit
    writer.write(b"quit\r\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    print("\nDone!", flush=True)


if __name__ == "__main__":
    asyncio.run(test())
