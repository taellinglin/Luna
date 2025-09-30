#!/usr/bin/env python3
"""
recover_wallet.py - Recover encrypted wallet data
"""

import base64
import json


def try_decrypt_manually(encrypted_data):
    """Try to manually decrypt the wallet data"""
    # Your encrypted data
    encrypted_base64 = "F0sPBwsbCywXABVDT0wvAkdFWylUQEBdWgJLVENNWEBvRklGQxkNBys0Bxg8WkdDFg9MWFlWV1hbbFxRVk9NXkNtUl1LIg=="

    # Try different keys that might have been used
    possible_keys = [
        "lincoin_default_key_12345",
        "lincoin_default_key",
        "default_wallet_key",
        "lunacoin_wallet_key",
        "wallet_encryption_key",
    ]

    for key in possible_keys:
        try:
            # Prepare the key
            while len(key) < 32:
                key += key
            key = key[:32]
            key_bytes = key.encode("utf-8")

            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_base64)

            # XOR decrypt
            decrypted = bytearray()
            for i, char in enumerate(encrypted_bytes):
                decrypted.append(char ^ key_bytes[i % len(key_bytes)])

            decrypted_text = decrypted.decode("utf-8")

            # Check if it's valid JSON
            data = json.loads(decrypted_text)
            print(f"✅ Success with key: {key}")
            print(f"Decrypted data: {data}")
            return data

        except Exception as e:
            print(f"❌ Failed with key '{key}': {e}")
            continue

    print("❌ Could not decrypt with any known key")
    return None


if __name__ == "__main__":
    encrypted_data = "F0sPBwsbCywXABVDT0wvAkdFWylUQEBdWgJLVENNWEBvRklGQxkNBys0Bxg8WkdDFg9MWFlWV1hbbFxRVk9NXkNtUl1LIg=="
    result = try_decrypt_manually(encrypted_data)

    if result:
        # Save the decrypted wallet
        with open("wallet_recovered.json", "w") as f:
            json.dump(result, f, indent=2)
        print("✅ Recovery successful! Saved as wallet_recovered.json")
    else:
        print("❌ Recovery failed")
