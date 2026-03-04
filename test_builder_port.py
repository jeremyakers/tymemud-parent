#!/usr/bin/env python3
"""Test builder port protocol commands"""

import socket
import sys


def send_command(host, port, command, wait_for_response=True):
    """Send a command to the status port and return the response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        # Read initial banner
        banner = sock.recv(1024).decode("utf-8", errors="ignore")
        print(f"Banner: {banner.strip()}")

        # Send command with CRLF
        full_cmd = command + "\r\n"
        sock.send(full_cmd.encode("utf-8"))
        print(f"Sent: {command}")

        if wait_for_response:
            # Give server time to process
            import time

            time.sleep(0.5)

            # Read response
            response = sock.recv(4096).decode("utf-8", errors="ignore")
            print(f"Response: {response.strip()}")
            return response

        sock.close()
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_unlock_room():
    print("\n=== Test 1: Unlock room 1000 ===")
    response = send_command("127.0.0.1", 9991, "wld_unlock c1gtri32 1000 testuser")
    return "OK" in response if response else False


def test_lock_room():
    print("\n=== Test 2a: Lock room 1000 ===")
    response = send_command("127.0.0.1", 9991, "wld_lock c1gtri32 1000 testuser")
    return "OK" in response if response else False


def test_lock_status():
    print("\n=== Test 2b: Check lock status ===")
    response = send_command("127.0.0.1", 9991, "wld_lock_status c1gtri32 1000")
    print(f"Lock status response: {response}")
    return True


if __name__ == "__main__":
    print("Builder Port Protocol Tests")
    print("=" * 50)

    test_unlock_room()
    test_lock_room()
    test_lock_status()
