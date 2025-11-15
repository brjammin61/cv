"""
API Keys Configuration Template

⚠️ SECURITY WARNING ⚠️
1. Copy this file to 'api_keys.py' in the same directory
2. Fill in your actual API keys in api_keys.py
3. NEVER commit api_keys.py to version control
4. Add api_keys.py to your .gitignore file

This template shows the structure needed for API authentication.
"""

# ============================================================================
# KALSHI API CREDENTIALS
# ============================================================================
# Get your Kalshi API credentials from: https://kalshi.com/
# You will need to generate an API key from your account settings

KALSHI_API_KEY = "your_kalshi_api_key_here"

# Path to your Kalshi RSA private key file
# Kalshi requires RSA key authentication for API access
KALSHI_PRIVATE_KEY_PATH = "/path/to/your/kalshi_private_key.pem"

# Kalshi API Base URL (do not change unless using demo environment)
KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Use demo environment for testing (no real money)
KALSHI_USE_DEMO = False
KALSHI_DEMO_API_BASE = "https://demo-api.kalshi.co/trade-api/v2"


# ============================================================================
# POLYMARKET API CREDENTIALS
# ============================================================================
# Polymarket uses Ethereum wallet authentication
# You need a private key from an Ethereum wallet

# Your Ethereum wallet private key (starts with 0x)
# This wallet will need USDC on Polygon network for trading
POLYMARKET_PRIVATE_KEY = "0x_your_ethereum_private_key_here"

# Polymarket CLOB (Central Limit Order Book) API endpoint
POLYMARKET_CLOB_API = "https://clob.polymarket.com"

# Polygon RPC endpoint for on-chain operations
# You can use a public RPC or get a dedicated one from:
# - Alchemy: https://www.alchemy.com/
# - Infura: https://infura.io/
# - QuickNode: https://www.quicknode.com/
POLYGON_RPC_URL = "https://polygon-rpc.com"

# Alternative: Use a dedicated RPC provider for better performance
# POLYGON_RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY"


# ============================================================================
# OPTIONAL: DATA PROVIDER API KEYS
# ============================================================================
# For enhanced data feeds and alternative data sources

# Google Trends API (for sentiment analysis)
GOOGLE_TRENDS_API_KEY = ""

# Twitter/X API (for social sentiment)
TWITTER_API_KEY = ""
TWITTER_API_SECRET = ""
TWITTER_BEARER_TOKEN = ""

# News API (for real-time news monitoring)
NEWS_API_KEY = ""


# ============================================================================
# RISK MANAGEMENT
# ============================================================================
# Maximum capital allocation (safety limit)
MAX_TOTAL_CAPITAL_USD = 10000.0

# Maximum position size per trade (% of capital)
MAX_POSITION_SIZE_PERCENT = 10.0

# Emergency kill switch - set to True to disable all trading
EMERGENCY_STOP = False


# ============================================================================
# HELPER FUNCTION
# ============================================================================
def validate_credentials() -> bool:
    """
    Validates that all required credentials are configured.

    Returns:
        bool: True if all credentials are set, False otherwise
    """
    required = {
        'KALSHI_API_KEY': KALSHI_API_KEY,
        'KALSHI_PRIVATE_KEY_PATH': KALSHI_PRIVATE_KEY_PATH,
        'POLYMARKET_PRIVATE_KEY': POLYMARKET_PRIVATE_KEY,
    }

    missing = []
    for name, value in required.items():
        if not value or 'your_' in value.lower() or 'path/to' in value:
            missing.append(name)

    if missing:
        print("❌ Missing or invalid credentials:")
        for cred in missing:
            print(f"   - {cred}")
        return False

    print("✅ All required credentials are configured")
    return True


if __name__ == "__main__":
    validate_credentials()
