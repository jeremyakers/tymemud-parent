#!/usr/bin/env python3
"""Test validate_zone via standalone MCP server process."""

import subprocess
import json
import sys
import time
import threading


def send_msg(proc, msg):
    """Send JSON-RPC message."""
    data = json.dumps(msg)
    proc.stdin.write(data + "\n")
    proc.stdin.flush()
    print(f">>> {data[:150]}...")


def read_msg(proc, timeout=30):
    """Read JSON-RPC response."""
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if line:
            print(f"<<< {line[:150]}...")
            return json.loads(line)
        time.sleep(0.1)
    print("<<< TIMEOUT")
    return None


# Start MCP server
print("=" * 60)
print("Starting standalone MCP server...")
print("=" * 60)

proc = subprocess.Popen(
    [sys.executable, "-m", "llm_gateway.server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd="/home/jeremy/tymemud",
)


def log_stderr():
    """Log stderr in background."""
    for line in proc.stderr:
        print(f"[STDERR] {line.rstrip()}")


# Start stderr logging thread
stderr_thread = threading.Thread(target=log_stderr, daemon=True)
stderr_thread.start()

try:
    # Initialize
    print("\n" + "=" * 60)
    print("TEST 1: Initialize")
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
    response = read_msg(proc)

    if not response or "error" in response:
        print("Initialization failed!")
        sys.exit(1)

    # Test validate_zone
    print("\n" + "=" * 60)
    print("TEST 2: validate_zone")
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

    print("Waiting for response (up to 30 seconds)...")
    response = read_msg(proc, timeout=30)

    if response:
        if "error" in response:
            print(f"\n✗ ERROR: {response['error']}")
        else:
            print(f"\n✓ SUCCESS: {response.get('result', 'N/A')}")
    else:
        print("\n✗ TIMEOUT - No response received")

finally:
    print("\n" + "=" * 60)
    print("Cleaning up...")
    print("=" * 60)
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except:
        proc.kill()

print("\nTest complete!")
