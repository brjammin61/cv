#!/usr/bin/env python3
"""
Helper script to create a PEM file from your Kalshi RSA private key.

If you have the RSA key but not as a .pem file, this script will help you create it.
"""

import os

print("=" * 80)
print("🔑 KALSHI RSA PRIVATE KEY TO PEM FILE CONVERTER")
print("=" * 80)

print("\n📋 Paste your RSA private key below.")
print("   It should look like one of these formats:")
print()
print("   Format 1 (Already in PEM format):")
print("   -----BEGIN PRIVATE KEY-----")
print("   MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...")
print("   -----END PRIVATE KEY-----")
print()
print("   Format 2 (Just the base64 string):")
print("   MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...")
print()
print("   Format 3 (RSA PRIVATE KEY format):")
print("   -----BEGIN RSA PRIVATE KEY-----")
print("   MIIEpAIBAAKCAQEA...")
print("   -----END RSA PRIVATE KEY-----")
print()
print("=" * 80)
print("Paste your key below, then press Enter twice when done:")
print("=" * 80)
print()

# Read multiline input
lines = []
while True:
    try:
        line = input()
        if line == "" and len(lines) > 0 and lines[-1] == "":
            # Two empty lines = done
            break
        lines.append(line)
    except EOFError:
        break

key_content = "\n".join(lines).strip()

# Check if it already has PEM headers
has_headers = key_content.startswith("-----BEGIN")

if has_headers:
    # Already in PEM format
    pem_content = key_content
    print("\n✅ Key is already in PEM format!")
else:
    # Need to add PEM headers
    print("\n🔧 Adding PEM headers...")

    # Remove any whitespace/newlines
    key_base64 = key_content.replace("\n", "").replace("\r", "").replace(" ", "")

    # Format with line breaks every 64 characters (PEM standard)
    formatted_lines = []
    for i in range(0, len(key_base64), 64):
        formatted_lines.append(key_base64[i:i+64])

    # Build PEM content
    pem_content = "-----BEGIN PRIVATE KEY-----\n"
    pem_content += "\n".join(formatted_lines)
    pem_content += "\n-----END PRIVATE KEY-----\n"

    print("✅ PEM headers added!")

# Decide where to save it
default_path = os.path.expanduser("~/.kalshi/private_key.pem")
print(f"\n📁 Where do you want to save the PEM file?")
print(f"   Press Enter for default: {default_path}")
print(f"   Or type a custom path:")

save_path = input().strip()
if not save_path:
    save_path = default_path

# Create directory if needed
os.makedirs(os.path.dirname(save_path), exist_ok=True)

# Write the file
with open(save_path, 'w') as f:
    f.write(pem_content)

# Set secure permissions (readable only by owner)
os.chmod(save_path, 0o600)

print()
print("=" * 80)
print("✅ SUCCESS!")
print("=" * 80)
print(f"\n🔑 PEM file created: {save_path}")
print(f"🔒 Permissions set to 600 (owner read/write only)")
print()
print("📝 Next step: Update config/api_keys.py")
print()
print(f"   KALSHI_PRIVATE_KEY_PATH = \"{save_path}\"")
print()
print("=" * 80)
