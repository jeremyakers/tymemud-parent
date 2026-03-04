#!/usr/bin/env python3
"""Comprehensive Web Editor Test Suite"""

import socket
import time
import base64


def send_proto(host, port, cmds, label):
    """Send commands to builder port and return responses"""
    print(f"\n{'=' * 60}")
    print(f"TEST: {label}")
    print("=" * 60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        sock.recv(1024)  # banner

        # Authenticate
        sock.send(b"HELLO c1gtri32 1\r\n")
        time.sleep(0.3)
        auth = sock.recv(1024)

        if b"OK" not in auth:
            print("FAIL: Authentication failed")
            return None

        results = []
        for cmd in cmds:
            sock.send(cmd.encode("utf-8"))
            time.sleep(0.3)

            resp = b""
            try:
                chunk = sock.recv(4096)
                resp += chunk
            except socket.timeout:
                pass

            results.append((cmd.strip(), resp))
            print(f"  CMD: {cmd.strip()!r}")
            print(f"  RSP: {resp!r}")

        sock.close()
        return results
    except Exception as e:
        print(f"FAIL: {e}")
        return None


def decode_b64(data):
    """Decode base64 if present"""
    if b" " in data:
        parts = data.split(b" ", 2)
        if len(parts) >= 3:
            try:
                decoded = base64.b64decode(parts[2]).decode("utf-8")
                return f"{parts[0].decode()} {parts[1].decode()} {decoded}"
            except:
                pass
    return data.decode("utf-8", errors="ignore")


def test_1_unlock():
    """Test 1: Ensure room 1000 is unlocked"""
    results = send_proto(
        "127.0.0.1",
        9697,
        ["wld_unlock 1000 testuser\r\n", "quit\r\n"],
        "1. Unlock room 1000",
    )
    if results and b"OK" in results[0][1]:
        return True, "Room 1000 unlocked"
    return False, "Failed to unlock room"


def test_2_lock_update():
    """Test 2: Lock room and verify"""
    results = send_proto(
        "127.0.0.1",
        9697,
        [
            "wld_lock 1000 testuser\r\n",
            "wld_lock_status 1000\r\n",
            "wld_unlock 1000 testuser\r\n",
            "quit\r\n",
        ],
        "2. Lock room, verify status, unlock",
    )
    if not results:
        return False, "No results"

    lock_ok = b"OK" in results[0][1]
    status_locked = b"423" in results[1][1]  # ERROR 423 = locked
    unlock_ok = b"OK" in results[2][1]

    if lock_ok and status_locked and unlock_ok:
        return True, "Lock/verify/unlock cycle works"
    return False, f"Lock:{lock_ok}, Status:{status_locked}, Unlock:{unlock_ok}"


def test_3_lock_conflict():
    """Test 3: OLC lock conflict"""
    results = send_proto(
        "127.0.0.1",
        9697,
        [
            "wld_lock 1000 testuser\r\n",
            "wld_lock 1000 otheruser\r\n",
            "wld_unlock 1000 testuser\r\n",
            "quit\r\n",
        ],
        "3. Lock conflict detection",
    )
    if not results:
        return False, "No results"

    first_lock = b"OK" in results[0][1]
    second_lock_rejected = b"423" in results[1][1]  # Should be rejected
    unlock_ok = b"OK" in results[2][1]

    if first_lock and second_lock_rejected and unlock_ok:
        return True, "Lock conflict detected correctly"
    return (
        False,
        f"First:{first_lock}, Conflict:{second_lock_rejected}, Unlock:{unlock_ok}",
    )


def test_4_basic_room_read():
    """Test 4: Read room data via wld_load"""
    results = send_proto(
        "127.0.0.1",
        9697,
        [
            "wld_load 10\r\n",  # Load zone 10
            "quit\r\n",
        ],
        "4. Load zone 10 (contains room 1000-1099)",
    )
    if results and results[0][1]:
        data = results[0][1].decode("utf-8", errors="ignore")
        if "ZONE" in data and "ROOM" in data:
            return True, f"Zone loaded, data length: {len(data)}"
    return False, "Failed to load zone"


def run_all_tests():
    print("\n" + "=" * 60)
    print("COMPREHENSIVE WEB EDITOR TEST SUITE")
    print("=" * 60)

    tests = [
        ("Test 1: Unlock room 1000", test_1_unlock),
        ("Test 2: Lock/verify/unlock", test_2_lock_update),
        ("Test 3: Lock conflict", test_3_lock_conflict),
        ("Test 4: Zone load", test_4_basic_room_read),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed, msg = test_func()
            results.append((name, passed, msg))
        except Exception as e:
            results.append((name, False, str(e)))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)

    for name, passed, msg in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        print(f"       {msg}")

    print("\n" + "=" * 60)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("=" * 60)

    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
