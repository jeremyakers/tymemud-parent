#!/usr/bin/env python3
"""Test with HELLO authentication"""

import socket
import time


def test_with_auth(host, port, label, *commands):
    print(f"\n=== {label} ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        banner = sock.recv(1024)

        # First send HELLO to authenticate
        sock.send(b"HELLO c1gtri32 1\r\n")
        time.sleep(0.3)
        hello_resp = sock.recv(1024)
        print(f"HELLO response: {hello_resp!r}")

        if b"OK" not in hello_resp:
            print("Authentication failed!")
            sock.close()
            return None

        # Now send the actual commands
        for cmd in commands:
            sock.send(cmd.encode("utf-8"))
            print(f"Sent: {cmd!r}")

        time.sleep(0.5)

        responses = []
        try:
            while True:
                resp = sock.recv(4096)
                if not resp:
                    break
                responses.append(resp)
        except socket.timeout:
            pass

        sock.close()

        full_resp = b"".join(responses)
        print(f"Response: {full_resp!r}")
        return full_resp
    except Exception as e:
        print(f"Error: {e}")
        return None


print("Testing with HELLO authentication on port 9697")
print("=" * 60)

# Test wld_lock_status
test_with_auth(
    "127.0.0.1",
    9697,
    "wld_lock_status 1000",
    "wld_lock_status c1gtri32 1000\r\n",
    "quit\r\n",
)

# Test wld_unlock
test_with_auth(
    "127.0.0.1",
    9697,
    "wld_unlock 1000",
    "wld_unlock c1gtri32 1000 testuser\r\n",
    "quit\r\n",
)

# Test wld_lock
test_with_auth(
    "127.0.0.1",
    9697,
    "wld_lock 1000",
    "wld_lock c1gtri32 1000 testuser\r\n",
    "quit\r\n",
)

# Test lock status again to verify
test_with_auth(
    "127.0.0.1",
    9697,
    "wld_lock_status 1000 (after lock)",
    "wld_lock_status c1gtri32 1000\r\n",
    "quit\r\n",
)
