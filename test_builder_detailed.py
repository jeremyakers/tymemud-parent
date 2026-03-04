#!/usr/bin/env python3
"""Test builder port protocol commands with detailed debugging"""

import socket
import sys
import time


def send_command(host, port, command, wait_for_response=True):
    """Send a command to the status port and return the response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        # Read initial banner
        banner = sock.recv(1024).decode("utf-8", errors="ignore")
        print(f"Connected. Banner received: {repr(banner)}")

        # Send command with CRLF
        full_cmd = command + "\r\n"
        sock.send(full_cmd.encode("utf-8"))
        print(f"Sent command: {repr(command)}")

        if wait_for_response:
            # Give server time to process
            time.sleep(1)

            # Read response
            try:
                response = sock.recv(4096).decode("utf-8", errors="ignore")
                print(f"Response received: {repr(response)}")
                return response
            except socket.timeout:
                print("Timeout waiting for response")
                return None

        sock.close()
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def run_tests():
    print("Builder Port Protocol Tests - Detailed")
    print("=" * 60)

    # Test 0: Basic who command
    print("\n=== Test 0: Basic 'who' command ===")
    response = send_command("127.0.0.1", 9991, "who")
    if response:
        print(f"PASS: who command works")
    else:
        print(f"FAIL: who command no response")

    # Test 1: Help command
    print("\n=== Test 1: 'help' command ===")
    response = send_command("127.0.0.1", 9991, "help")
    if response:
        print(f"PASS: help command works")
    else:
        print(f"FAIL: help command no response")

    # Test 2: Unlock room 1000
    print("\n=== Test 2: wld_unlock c1gtri32 1000 testuser ===")
    response = send_command("127.0.0.1", 9991, "wld_unlock c1gtri32 1000 testuser")
    if response and "OK" in response:
        print(f"PASS: Room 1000 unlocked successfully")
    elif response and "LOCKED" in response:
        print(f"INFO: Room 1000 is locked by someone else")
    elif response and "ERROR" in response:
        print(f"FAIL: Error response: {response}")
    else:
        print(f"FAIL: No response or unexpected response: {response}")

    # Test 3: Lock room 1000
    print("\n=== Test 3: wld_lock c1gtri32 1000 testuser ===")
    response = send_command("127.0.0.1", 9991, "wld_lock c1gtri32 1000 testuser")
    if response and "OK" in response:
        print(f"PASS: Room 1000 locked successfully")
    elif response and "LOCKED" in response:
        print(f"INFO: Room 1000 is already locked")
    else:
        print(f"FAIL: No response or unexpected: {response}")

    # Test 4: Check lock status
    print("\n=== Test 4: wld_lock_status c1gtri32 1000 ===")
    response = send_command("127.0.0.1", 9991, "wld_lock_status c1gtri32 1000")
    if response:
        print(f"PASS: Lock status: {response.strip()}")
    else:
        print(f"FAIL: No lock status response")

    # Test 5: Try to lock with different user (should fail)
    print("\n=== Test 5: wld_lock c1gtri32 1000 otheruser (should be LOCKED) ===")
    response = send_command("127.0.0.1", 9991, "wld_lock c1gtri32 1000 otheruser")
    if response and "LOCKED" in response:
        print(f"PASS: Lock conflict detected correctly")
    else:
        print(f"FAIL: Expected LOCKED response, got: {response}")

    # Test 6: Unlock room 1000
    print("\n=== Test 6: wld_unlock c1gtri32 1000 testuser ===")
    response = send_command("127.0.0.1", 9991, "wld_unlock c1gtri32 1000 testuser")
    if response and "OK" in response:
        print(f"PASS: Room 1000 unlocked successfully")
    else:
        print(f"FAIL: No response or unexpected: {response}")

    # Test 7: Verify it's free
    print("\n=== Test 7: wld_lock_status c1gtri32 1000 (should be FREE) ===")
    response = send_command("127.0.0.1", 9991, "wld_lock_status c1gtri32 1000")
    if response and "FREE" in response:
        print(f"PASS: Room is now FREE")
    else:
        print(f"FAIL: Expected FREE, got: {response}")


if __name__ == "__main__":
    run_tests()
