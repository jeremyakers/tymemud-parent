#!/usr/bin/env python3
import base64

# Full base64 from the debug output
desc_b64 = "ICAgYDJPbmUgb2YgdGhlIGJ1c2llc3QgcGxhY2VzIGluIHRoZSBtdWQsIGF0IGxlYXN0IGZvciBhbiBhY3RpdmUgYCFHb2RgMiwNCmlzIG9uZSBvZiBleHRyZW1lIGltcG9ydGFuY2UuoCBUaGUgZGFyayBjaGVycnkgYWNjZW50cywgYWxvbmcgd2l0aA0KYCNnb2xkYDIgdHJpbSBiYWNrIHVwIHlvdXIgbm90aW9uIHRoYXQgb25seSByZWFsbHkgcmVhbGx5IGltcG9ydGFudA0KbWVzc2FnZXMgc2hvdWxkIGJlIHBvc3RlZCBoZXJlLqAgVG8gdGhlIGA4bm9ydGhgMiBsaWVzIHRoZSBgMUdvZHNgMg0KSW5uLqAgVG8gdGhlIGA3c291dGhgMiBpcyB0aGUgYCFHb2RzYDIgbWVldGluZyByb29tLqAgVG8gdGhlIGA0ZWFzdGAyDQpsaWVzIHRoZSBgIUdvZHNgMiBtb3J0YWwgYm9hcmQgcm9vbSwgYW5kIHRoZSBgIUdvZHMgcG9zdCBvZmZpY2UgaXMgb2ZmDQp0byB0aGUgYDF3ZXN0YDIuoCBgM1VwYDIgaXMgdGhlIHRoZSBgJVF1ZXN0b3JzYDIgbWVldGluZyBjaGFtYmVyLiANCkxvb2tpbmcgYDVkb3duIHlvdSBjYW4gc2VlIHRoZSBodXNzbGUgYW5kIGJ1c3RsZSBvZiBDYWVtbHlucyBPdmFsIFBsYXphLg0K"

try:
    decoded = base64.b64decode(desc_b64).decode()
    print(f"Decoded successfully! Length: {len(decoded)}")
    print(f"First 200 chars: {repr(decoded[:200])}")
except Exception as e:
    print(f"Error: {e}")
    # Check padding
    padding_needed = 4 - (len(desc_b64) % 4)
    if padding_needed != 4:
        print(f"Padding needed: {padding_needed}")
        fixed = desc_b64 + ("=" * padding_needed)
        try:
            decoded = base64.b64decode(fixed).decode()
            print(f"Fixed decode! Length: {len(decoded)}")
        except Exception as e2:
            print(f"Still failed: {e2}")
