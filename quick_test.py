#!/usr/bin/env python3
"""Quick test of validate_zone via JSON-RPC."""

import subprocess
import json
import sys
import time


def send_msg(proc, msg):
    """Send JSON-RPC message."""
    data = json.dumps(msg)
    print(f"\n>>> {data[:200]}...")
    proc.stdin.write(data + "\n")
    proc.stdin.flush()


def read_msg(proc, timeout=10):
    """Read JSON-RPC response."""
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if line:
            print(f"<<< {line[:200]}...")
            return json.loads(line)
        time.sleep(0.1)
    print("<<< TIMEOUT")
    return None


# Start MCP server
proc = subprocess.Popen(
    [sys.executable, "run_mcp_test.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd="/home/jeremy/tymemud",
)

try:
    # Initialize
    print("=" * 60)
    print("Initializing...")
    print("=" * 60)
    send_msg(
        proc,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        },
    )
    read_msg(proc)

    # Test validate_zone
    print("\n" + "=" * 60)
    print("Testing validate_zone...")
    print("=" * 60)
    send_msg(
        proc,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "validate_zone",
                "arguments": {
                    "host": "127.0.0.1",
                    "port": 9697,
                    "token": "c1gtri32",
                    "zone": 471,
                },
            },
        },
    )
    response = read_msg(proc, timeout=30)

    if response:
        print(f"\nResult: {response.get('result', 'N/A')}")
    else:
        print("\nNo response (timeout)")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except:
        proc.kill()
