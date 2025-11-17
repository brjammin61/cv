#!/usr/bin/env python3
"""
Quick status checker to verify Kalshi API setup.

Run this after configuring your private key to ensure everything works.
"""

import sys
import os

print("=" * 80)
print("🔍 KALSHI API SETUP VERIFICATION")
print("=" * 80)

# Check 1: Config file exists
print("\n[1/5] Checking config file...")
try:
    from config.api_keys import KALSHI_API_KEY, KALSHI_API_BASE, KALSHI_PRIVATE_KEY_PATH
    print(f"✅ Config loaded")
    print(f"    API Key: {KALSHI_API_KEY[:20]}...")
    print(f"    Base URL: {KALSHI_API_BASE}")
    print(f"    Key Path: {KALSHI_PRIVATE_KEY_PATH}")
except ImportError as e:
    print(f"❌ Failed to load config: {e}")
    sys.exit(1)

# Check 2: Private key file exists
print("\n[2/5] Checking private key file...")
if os.path.exists(KALSHI_PRIVATE_KEY_PATH):
    print(f"✅ Private key file exists")

    # Check permissions
    stat = os.stat(KALSHI_PRIVATE_KEY_PATH)
    perms = oct(stat.st_mode)[-3:]
    print(f"    Permissions: {perms}", end="")
    if perms == '600':
        print(" ✅")
    else:
        print(" ⚠️  (Recommended: 600)")
else:
    print(f"❌ Private key file not found at: {KALSHI_PRIVATE_KEY_PATH}")
    print("   Run: python3 create_pem_file.py")
    sys.exit(1)

# Check 3: Can load private key
print("\n[3/5] Loading private key...")
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    with open(KALSHI_PRIVATE_KEY_PATH, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    print("✅ Private key loaded successfully")
    print(f"    Key size: {private_key.key_size} bits")
except Exception as e:
    print(f"❌ Failed to load private key: {e}")
    print("   The key file may be corrupted or in wrong format")
    sys.exit(1)

# Check 4: Test API connection
print("\n[4/5] Testing API connection...")
try:
    import requests
    import time
    import base64
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    # Generate signature
    timestamp_ms = int(time.time() * 1000)
    timestamp_str = str(timestamp_ms)
    method = 'GET'
    path = '/exchange/status'
    message = timestamp_str + method + path

    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    signature_b64 = base64.b64encode(signature).decode('utf-8')

    # Make request
    headers = {
        'KALSHI-ACCESS-KEY': KALSHI_API_KEY,
        'KALSHI-ACCESS-SIGNATURE': signature_b64,
        'KALSHI-ACCESS-TIMESTAMP': timestamp_str
    }

    response = requests.get(
        f"{KALSHI_API_BASE}{path}",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        print("✅ Successfully connected to Kalshi API")
        print(f"    Exchange Active: {data.get('exchange_active', 'Unknown')}")
        print(f"    Trading Active: {data.get('trading_active', 'Unknown')}")
    else:
        print(f"❌ API returned status {response.status_code}")
        print(f"    Response: {response.text[:200]}")
        if response.status_code == 403:
            print("    → This usually means the signature is invalid")
            print("    → Or the API key doesn't match the private key")
        sys.exit(1)

except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Check 5: Test connector
print("\n[5/5] Testing Kalshi connector...")
try:
    from connectors import KalshiConnector

    connector = KalshiConnector(simulate_data=False)

    if connector.connected:
        print("✅ Kalshi connector initialized successfully")
    else:
        print("❌ Connector failed to initialize")
        sys.exit(1)

except Exception as e:
    print(f"❌ Connector test failed: {e}")
    sys.exit(1)

# All checks passed!
print("\n" + "=" * 80)
print("🎉 ALL CHECKS PASSED!")
print("=" * 80)
print("\n✅ Your Kalshi API is properly configured and working!")
print("\n📋 Next steps:")
print("   1. Run: python3 discover_markets.py")
print("      → Find real market tickers")
print()
print("   2. Update config/markets.py with real tickers")
print()
print("   3. Run: python3 run_oracle_system.py --mode paper")
print("      → Start collecting real market data!")
print()
print("=" * 80)
