#!/usr/bin/env python3
"""Debug builder port protocol parsing"""

import socket
import time


def debug_command(host, port, command):
    """Send a command and show exactly what's happening"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        # Read banner
        banner = sock.recv(1024)
        print(f"Banner bytes: {banner!r}")

        # Send command with just \n first
        cmd1 = command + "\n"
        print(f"Sending with \\n: {cmd1!r}")
        sock.send(cmd1.encode("utf-8"))
        time.sleep(0.5)

        try:
            resp1 = sock.recv(4096)
            print(f"Response: {resp1!r}")
        except socket.timeout:
            print("Timeout with \\n")

        sock.close()

        # Now try with \r\n
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        banner = sock.recv(1024)

        cmd2 = command + "\r\n"
        print(f"\nSending with \\r\\n: {cmd2!r}")
        sock.send(cmd2.encode("utf-8"))
        time.sleep(0.5)

        try:
            resp2 = sock.recv(4096)
            print(f"Response: {resp2!r}")
        except socket.timeout:
            print("Timeout with \\r\\n")

        sock.close()

    except Exception as e:
        print(f"Error: {e}")


print("Debug: Testing command parsing")
print("=" * 60)
debug_command("127.0.0.1", 9991, "wld_lock c1gtri32 1000 testuser")
