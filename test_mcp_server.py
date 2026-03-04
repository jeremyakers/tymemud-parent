#!/usr/bin/env python3
"""Test script for MCP server - sends JSON-RPC messages via stdio."""

import subprocess
import json
import sys


def send_message(proc, message):
    """Send a JSON-RPC message to the server."""
    msg_str = json.dumps(message)
    print(f"\n>>> SENDING:\n{msg_str}")
    proc.stdin.write(msg_str + "\n")
    proc.stdin.flush()


def read_response(proc, timeout=5):
    """Read a response from the server."""
    try:
        line = proc.stdout.readline()
        if line:
            print(f"<<< RECEIVED:\n{line.strip()}")
            return json.loads(line)
        return None
    except Exception as e:
        print(f"Error reading response: {e}")
        return None


def main():
    # Start the MCP server
    print("=" * 60)
    print("Starting MCP server test...")
    print("=" * 60)

    proc = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/home/jeremy/tymemud/llm_gateway",
    )

    try:
        # Test 1: Initialize
        print("\n" + "=" * 60)
        print("TEST 1: Initialize")
        print("=" * 60)
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        }
        send_message(proc, init_msg)
        response = read_response(proc)

        # Test 2: List tools
        print("\n" + "=" * 60)
        print("TEST 2: List tools")
        print("=" * 60)
        list_msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        send_message(proc, list_msg)
        response = read_response(proc)

        # Test 3: Call list_zones WITHOUT required params
        print("\n" + "=" * 60)
        print("TEST 3: Call list_zones WITHOUT required params (should fail)")
        print("=" * 60)
        call_msg_no_params = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "list_zones", "arguments": {}},
        }
        send_message(proc, call_msg_no_params)
        response = read_response(proc)

        # Test 4: Call list_zones WITH required params
        print("\n" + "=" * 60)
        print("TEST 4: Call list_zones WITH required params (should work)")
        print("=" * 60)
        call_msg_with_params = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "list_zones",
                "arguments": {"host": "127.0.0.1", "port": 9697, "token": "c1gtri32"},
            },
        }
        send_message(proc, call_msg_with_params)
        response = read_response(proc)

        # Give it a bit more time for the response
        import time

        time.sleep(2)

        # Read any remaining stderr
        print("\n" + "=" * 60)
        print("STDERR OUTPUT:")
        print("=" * 60)
        proc.stderr.close()

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()

    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
