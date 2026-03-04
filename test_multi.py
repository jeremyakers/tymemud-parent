#!/usr/bin/env python3
"""Test sending command followed by quit like PHP does"""

import socket
import time


def test_multi_command(host, port, commands):
    """Send multiple commands like PHP does"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        # Read banner
        banner = sock.recv(1024)
        print(f"Connected. Banner: {banner!r}")

        # Send all commands
        for cmd in commands:
            sock.send(cmd.encode("utf-8"))
            print(f"Sent: {cmd!r}")

        time.sleep(1)

        # Read all responses
        responses = []
        try:
            while True:
                resp = sock.recv(4096)
                if not resp:
                    break
                responses.append(resp)
                print(f"Response chunk: {resp!r}")
        except socket.timeout:
            print("Timeout (expected)")

        sock.close()
        return b"".join(responses)
    except Exception as e:
        print(f"Error: {e}")
        return None


print("Testing multi-command like PHP")
print("=" * 60)

# Test 1: Single command with quit
print("\n--- Test 1: wld_lock with quit ---")
test_multi_command(
    "127.0.0.1", 9991, ["wld_lock c1gtri32 1000 testuser\r\n", "quit\r\n"]
)

# Test 2: Check status, then quit
print("\n--- Test 2: wld_lock_status with quit ---")
test_multi_command("127.0.0.1", 9991, ["wld_lock_status c1gtri32 1000\r\n", "quit\r\n"])

# Test 3: who then quit (should work)
print("\n--- Test 3: who with quit (should work) ---")
test_multi_command("127.0.0.1", 9991, ["who\r\n", "quit\r\n"])
