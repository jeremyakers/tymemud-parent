#!/usr/bin/env python3
"""Test against existing 9696 server"""

import socket
import time


def test_command(host, port, commands, label):
    print(f"\n=== {label} ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        banner = sock.recv(1024)
        print(f"Connected")

        for cmd in commands:
            sock.send(cmd.encode("utf-8"))

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


print("Testing against existing 9696 server")
print("=" * 60)

# Test who
test_command("127.0.0.1", 9697, ["who\r\n", "quit\r\n"], "who command")

# Test wld_lock_status
test_command(
    "127.0.0.1",
    9697,
    ["wld_lock_status c1gtri32 1000\r\n", "quit\r\n"],
    "wld_lock_status",
)

# Test wld_unlock
test_command(
    "127.0.0.1",
    9697,
    ["wld_unlock c1gtri32 1000 testuser\r\n", "quit\r\n"],
    "wld_unlock",
)

# Test wld_lock
test_command(
    "127.0.0.1", 9697, ["wld_lock c1gtri32 1000 testuser\r\n", "quit\r\n"], "wld_lock"
)
