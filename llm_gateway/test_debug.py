#!/usr/bin/env python3
"""Debug version of test script."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")
from client import BuilderPortClient


async def test_with_debug():
    print("=" * 70)
    print("TYMEMUD LLM GATEWAY - DEBUG TEST")
    print("=" * 70)
    print()

    client = BuilderPortClient()
    print(f"Token loaded: {client.token}")
    print(f"Host: {client.host}, Port: {client.port}")
    print()

    print("Attempting connection...")
    try:
        # Manually do what connect() does but with debug
        import asyncio

        client.reader, client.writer = await asyncio.wait_for(
            asyncio.open_connection(client.host, client.port), timeout=5
        )
        print("TCP connection established")

        # Read greeting
        print("Reading greeting...")
        greeting = await asyncio.wait_for(client._read_line(), timeout=5)
        print(f"First line: {repr(greeting)}")

        # Skip banner lines
        count = 0
        while (
            greeting == ""
            or "MikkiMUD" in greeting
            or "status port" in greeting.lower()
        ):
            greeting = await asyncio.wait_for(client._read_line(), timeout=5)
            print(f"Banner line {count}: {repr(greeting)}")
            count += 1
            if count > 10:
                print("Too many banner lines, breaking")
                break

        print(f"Final greeting before HELLO: {repr(greeting)}")

        # Send HELLO
        print(f"Sending: hello {client.token} 1")
        await client._send(f"hello {client.token} 1")

        # Read response
        print("Reading HELLO response...")
        response = await asyncio.wait_for(client._read_line(), timeout=5)
        print(f"HELLO response: {repr(response)}")

        if response.startswith("OK"):
            print("Authentication successful!")
            client.authed = True
        else:
            print(f"Authentication failed: {response}")
            return

        # Now test list_zones
        print("\nTesting list_zones...")
        await client._send("wld_list")
        response = await asyncio.wait_for(client._read_line(), timeout=5)
        print(f"wld_list response: {repr(response)}")

        if response.startswith("OK"):
            lines = []
            while True:
                line = await asyncio.wait_for(client._read_line(), timeout=5)
                print(f"Zone line: {repr(line)}")
                if line == "END" or not line:
                    break
                lines.append(line)
            print(f"Total zones received: {len(lines)}")

        await client.disconnect()
        print("\nDisconnected successfully")

    except asyncio.TimeoutError:
        print("TIMEOUT: Operation took too long")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_debug())
