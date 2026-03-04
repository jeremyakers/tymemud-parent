#!/usr/bin/env python3
"""Debug room parsing to find the issue."""

import base64
import sys

sys.path.insert(0, "/home/jeremy/tymemud")

# Raw data from protocol
room_1000_name_b64 = "QmVnaW5uaW5nIFJvb20A"
room_1000_desc_b64 = "VGhpcyBpcyBhbiBlbXB0eSB6b25lLg0K"

room_1204_name_b64 = "VGhlIGAhR29kc2AyIEJvYXJkIFJvb21gNwAA"
room_1204_desc_b64 = "ICBgMk9uZSBvZiB0aGUgYnVzaWVzdCBwbGFjZXMgaW4gdGhlIG11ZCwgYXQgbGVhc3QgZm9yIGFuIGFjdGl2ZSBgIUdvZGAsDQppcyBvbmUgb2YgZXh0cmVtZSBpbXBvcnRhbmNlLqAgVGhlIGRhcmsgY2hlcnJ5IGFjY2VudHMsIGFsb25nIHdpdGgNCmAjZ29sZGAgMiB0cmltIGJhY2sgdXAgeW91ciBub3Rpb24gdGhhdCBvbmx5IHJlYWxseSByZWFsbHkgaW1wb3J0YW50DQptZXNzYWdlcyBzaG91bGQgYmUgcG9zdGVkIGhlcmUuICBUbyB0aGUgYDhucnRoaCBgMiBsaWVzIHRoZSBgMUdvZHNgMg0KSW5uLiAgVG8gdGhlIGBhc291dGhgMiBpcyB0aGUgYCFHb2RzYDIgbWVldGluZyByb29tLiAgVG8gdGhlIGBhNGVhc3RgMg0KbGllcyB0aGUgYCFHb2RzYDIgbW9ydGFsIGJvYXJkIHJvb20sIGFuZCB0aGUgYCFHb2RzIHBvc3Qgb2ZmaWNlIGlzIG9mZg0KdG8gdGhlIGBhd2VzdGAyLiAgYDNVcGAyIGlzIHRoZSB0aGUgYCVRdWVzdG9yc2AyIG1lZXRpbmcgY2hhbWJlci4NCkxvb2tpbmcgYDVkb3duIHlvdSBjYW4gc2VlIHRoZSBodXNzbGUgYW5kIGJ1c3RsZSBvZiBDYWVtbHlucyBPdmFsIFBsYXphLg0K"

print("Room 1000:")
name_1000 = base64.b64decode(room_1000_name_b64).decode("latin-1")
desc_1000 = base64.b64decode(room_1000_desc_b64).decode("latin-1")
print(f"  Name raw: {repr(name_1000)}")
print(f"  Name clean: {name_1000.rstrip(chr(0))}")
print(f"  Desc raw: {repr(desc_1000)}")
print()

print("Room 1204:")
name_1204 = base64.b64decode(room_1204_name_b64).decode("latin-1")
desc_1204 = base64.b64decode(room_1204_desc_b64).decode("latin-1")
print(f"  Name raw: {repr(name_1204)}")
print(f"  Name clean: {name_1204.rstrip(chr(0))}")
print(f"  Desc raw: {repr(desc_1204[:100])}...")
