#!/usr/bin/env python3
"""Test with different line endings"""

import socket
import time


def test_with_lineending(host, port, command, lineending):
    """Send a command with specific line ending"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        # Read banner
        banner = sock.recv(1024)

        # Send command
        cmd = command + lineending
        sock.send(cmd.encode("utf-8"))
        print(f"Sent: {command!r} with {lineending!r}")

        time.sleep(0.5)

        try:
            resp = sock.recv(4096)
            print(f"Response: {resp!r}")
            return resp
        except socket.timeout:
            print("Timeout")
            return None

        sock.close()
    except Exception as e:
        print(f"Error: {e}")
        return None


print("Testing different line endings")
print("=" * 60)

# Test 1: \r\n (CRLF)
print("\n--- Test with \\r\\n ---")
test_with_lineending("127.0.0.1", 9991, "wld_lock c1gtri32 1000 testuser", "\r\n")

# Test 2: \n\r (LFCR) - what PHP uses
print("\n--- Test with \\n\\r ---")
test_with_lineending("127.0.0.1", 9991, "wld_lock c1gtri32 1000 testuser", "\n\r")

# Test 3: \n only
print("\n--- Test with \\n ---")
test_with_lineending("127.0.0.1", 9991, "wld_lock c1gtri32 1000 testuser", "\n")

# Test 4: \r only
print("\n--- Test with \\r ---")
test_with_lineending("127.0.0.1", 9991, "wld_lock c1gtri32 1000 testuser", "\r")
