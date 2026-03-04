#!/usr/bin/env python3
"""Test with correct command format (no token in command)"""

import socket
import time


def send_cmds(host, port, label, *cmds):
    print(f"\n=== {label} ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        sock.recv(1024)  # banner

        # Authenticate
        sock.send(b"HELLO c1gtri32 1\r\n")
        time.sleep(0.3)
        auth = sock.recv(1024)
        print(f"Auth: {auth!r}")

        if b"OK" not in auth:
            print("Auth failed!")
            return None

        # Send commands (no token needed!)
        for cmd in cmds:
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
        full = b"".join(responses)
        print(f"Response: {full!r}")
        return full
    except Exception as e:
        print(f"Error: {e}")
        return None


print("Testing with correct format (no token in wld_* commands)")
print("=" * 60)

# Unlock first to ensure clean state
send_cmds(
    "127.0.0.1", 9697, "1. Unlock room 1000", "wld_unlock 1000 testuser\r\n", "quit\r\n"
)

# Check status (should be FREE)
send_cmds(
    "127.0.0.1",
    9697,
    "2. Check status (should be FREE)",
    "wld_lock_status 1000\r\n",
    "quit\r\n",
)

# Lock room
send_cmds(
    "127.0.0.1", 9697, "3. Lock room 1000", "wld_lock 1000 testuser\r\n", "quit\r\n"
)

# Check status (should show testuser)
send_cmds(
    "127.0.0.1",
    9697,
    "4. Check status (should show LOCKED testuser)",
    "wld_lock_status 1000\r\n",
    "quit\r\n",
)

# Try to lock with different user (should fail)
send_cmds(
    "127.0.0.1",
    9697,
    "5. Try lock with otheruser (should fail)",
    "wld_lock 1000 otheruser\r\n",
    "quit\r\n",
)

# Unlock
send_cmds(
    "127.0.0.1", 9697, "6. Unlock room 1000", "wld_unlock 1000 testuser\r\n", "quit\r\n"
)

# Final status (should be FREE)
send_cmds(
    "127.0.0.1",
    9697,
    "7. Final status (should be FREE)",
    "wld_lock_status 1000\r\n",
    "quit\r\n",
)
