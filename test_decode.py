#!/usr/bin/env python3
"""Manual decode test for room 1204."""

import base64

name_b64 = "VGhlIGAhR29kc2AyIEJvYXJkIFJvb21gNwAA"
desc_b64 = "ICAgYDJPbmUgb2YgdGhlIGJ1c2llc3QgcGxhY2VzIGluIHRoZSBtdWQsIGF0IGxlYXN0IGZvciBhbiBhY3RpdmUgYCFHb2RgMiwNCmlzIG9uZSBvZiBleHRyZW1lIGltcG9ydGF"

try:
    name = base64.b64decode(name_b64).decode()
    print(f"Name: {repr(name)}")
except Exception as e:
    print(f"Name decode error: {e}")

try:
    desc = base64.b64decode(desc_b64).decode()
    print(f"Desc: {repr(desc[:100])}...")
except Exception as e:
    print(f"Desc decode error: {e}")
