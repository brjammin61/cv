# Monad SDK Integration Guide

**Target Date:** November 24, 2025 (Mainnet Launch)
**Timeline:** You have 9 days to prepare this integration

This guide shows you exactly how to replace the mock data with real Monad validator data when mainnet launches.

---

## Overview

Currently, `monadpulse_backend/ingestor/ingestor.py` uses **mock data**. On November 24, you'll replace the mock data functions with real Monad SDK calls.

The architecture stays the same - you're just swapping the data source.

---

## Pre-Launch Preparation (Do This NOW)

### 1. Research Monad SDK Documentation

**Official Resources:**
- Monad Developer Docs: https://docs.monad.xyz/
- Monad GitHub: https://github.com/monad-labs
- Monad Discord: https://discord.gg/monad (join the #developers channel)

**What to look for:**
- How to connect to Monad RPC
- How to query validator information
- How to get block data
- How to access staking/delegation info

### 2. Set Up Monad RPC Access

You'll need RPC endpoints to query the Monad network.

**Options:**
- **Monad Foundation RPC** (likely free, public endpoint)
- **Your own Monad node** (advanced, expensive)
- **Third-party RPC provider** (Alchemy, Infura for Monad)

**Add to your `.env` file:**
```bash
MONAD_RPC_URL=https://rpc.monad.xyz  # Replace with actual endpoint
MONAD_CHAIN_ID=10143  # Replace with actual chain ID
```

### 3. Install Monad SDK

When the SDK is available, install it:

```bash
cd /opt/monadpulse/monadpulse_backend/ingestor
pip install monad-sdk  # Replace with actual package name
```

Or if they use web3.py compatible interface:
```bash
pip install web3
```

Update `requirements.txt`:
```bash
echo "monad-sdk>=1.0.0" >> requirements.txt
# OR
echo "web3>=6.0.0" >> requirements.txt
```

---

## Integration Points

You need to replace 3 functions in `ingestor/ingestor.py`:

### Function 1: `fetch_validator_data()`

**Current (Mock):**
```python
def fetch_validator_data() -> List[Dict]:
    """
    PRODUCTION: This will call the Monad SDK
    For now, returns mock data with slight randomization
    """
    validators = []
    for mock_val in MOCK_VALIDATORS:
        mev_variation = random.uniform(-0.05, 0.05)
        validators.append({
            "name": mock_val["name"],
            "mev_efficiency": max(0, mock_val["mev"] * (1 + mev_variation)),
            "is_omega_partner": mock_val["partner"]
        })
    return validators
```

**Production (Real Data):**
```python
from monad_sdk import MonadClient  # Import Monad SDK

# Initialize client (do this once, outside the function)
monad_client = MonadClient(rpc_url=os.getenv('MONAD_RPC_URL'))

def fetch_validator_data() -> List[Dict]:
    """
    Fetches real validator data from Monad network
    """
    try:
        # Get all validators from Monad staking contract
        validators_raw = monad_client.get_validators()
        
        validators = []
        for val in validators_raw:
            validators.append({
                "name": val.moniker or val.operator_address[:8],  # Validator name
                "mev_efficiency": 0.0,  # Start with 0, Omega Engine will calculate this later
                "is_omega_partner": False  # Default to false for now
            })
        
        return validators
        
    except Exception as e:
        logger.error(f"Failed to fetch validator data: {e}")
        return []  # Return empty list on error
```

**Key Data Points to Extract:**
- `validator.operator_address` - Unique validator ID
- `validator.moniker` - Validator display name
- `validator.commission` - Commission rate
- `validator.voting_power` - Current voting power
- `validator.status` - Active/jailed/unbonding
- `validator.uptime` - Block signing history

### Function 2: `fetch_chart_data()`

**Current (Mock):**
```python
def fetch_chart_data() -> List[Dict]:
    """
    PRODUCTION: This will calculate real MEV metrics over time
    For now, returns mock chart data
    """
    # Returns 14 days of mock data
    ...
```

**Production (Real Data):**
```python
def fetch_chart_data() -> List[Dict]:
    """
    Fetches historical MEV data for charts
    """
    try:
        # Get blocks from last 14 days
        end_block = monad_client.get_latest_block_number()
        blocks_per_day = 43200  # Assuming 2-second blocks: 86400/2
        start_block = end_block - (blocks_per_day * 14)
        
        chart_data = []
        
        # Sample every N blocks to get daily data points
        for day in range(14):
            block_num = start_block + (blocks_per_day * day)
            
            # Get block data
            block = monad_client.get_block(block_num)
            
            # Calculate MEV for that day (sum of all validator MEV)
            # This is placeholder - Omega Engine will calculate real MEV
            total_mev = calculate_daily_mev(block, blocks_per_day)
            
            chart_data.append({
                "date": (datetime.now() - timedelta(days=13-day)).strftime("%Y-%m-%d"),
                "mev": total_mev
            })
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Failed to fetch chart data: {e}")
        return []
```

### Function 3: `fetch_network_stats()`

**Current (Mock):**
```python
def fetch_network_stats() -> Dict:
    """
    PRODUCTION: This will get real network statistics
    For now, returns mock stats
    """
    return {
        "total_validators": 150,
        "total_mev": 1250000.0,
        "omega_partners": 3,
        "avg_efficiency": 85.7
    }
```

**Production (Real Data):**
```python
def fetch_network_stats() -> Dict:
    """
    Fetches real-time network statistics from Monad
    """
    try:
        # Get validator set
        validators = monad_client.get_validators()
        
        # Get network info
        network_info = monad_client.get_network_info()
        
        # Calculate stats
        total_validators = len([v for v in validators if v.status == 'active'])
        omega_partners = len([v for v in validators if v.is_omega_partner])  # You'll flag these
        
        # Total MEV will come from Omega Engine analysis
        total_mev = 0.0  # Placeholder
        avg_efficiency = 0.0  # Placeholder
        
        return {
            "total_validators": total_validators,
            "total_mev": total_mev,
            "omega_partners": omega_partners,
            "avg_efficiency": avg_efficiency
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch network stats: {e}")
        return {
            "total_validators": 0,
            "total_mev": 0.0,
            "omega_partners": 0,
            "avg_efficiency": 0.0
        }
```

---

## Step-by-Step Integration (Nov 24)

### Step 1: Get Monad SDK Access (Morning of Nov 24)

1. Check Monad Discord #announcements for RPC endpoints
2. Check Monad docs for SDK installation
3. Join #developers channel and ask for help if needed

### Step 2: Update Environment Variables

SSH into your VPS:
```bash
ssh root@143.110.144.231
cd /opt/monadpulse/monadpulse_backend
```

Add Monad RPC to `.env`:
```bash
echo "MONAD_RPC_URL=https://rpc.monad.xyz" >> .env
echo "MONAD_CHAIN_ID=10143" >> .env
```

### Step 3: Install SDK

```bash
cd /opt/monadpulse/monadpulse_backend/ingestor
pip install monad-sdk
# OR
pip install web3
```

Update requirements:
```bash
pip freeze | grep monad > requirements.txt
```

### Step 4: Update Code

Edit `ingestor/ingestor.py`:
```bash
cd /opt/monadpulse
git pull  # Get any updates
nano monadpulse_backend/ingestor/ingestor.py
```

Replace the 3 mock functions with real SDK calls (see examples above).

### Step 5: Test Locally First

```bash
cd /opt/monadpulse/monadpulse_backend/ingestor
python ingestor.py
```

Watch for errors. If it crashes, check:
- RPC URL is correct
- SDK is installed
- Network is actually live

### Step 6: Deploy to Production

```bash
cd /opt/monadpulse/monadpulse_backend
docker-compose down
docker-compose up -d --build
```

### Step 7: Verify Real Data

Check logs:
```bash
docker-compose logs -f ingestor
```

You should see:
```
INFO | INGESTOR | Fetched 150 validators from Monad network
INFO | INGESTOR | Updated 150 validators
```

Check dashboard:
```
http://143.110.144.231
```

You should see real validator names!

### Step 8: Announce Launch

Post in Monad Discord #general:
```
🎉 MonadPulse is LIVE! 🎉

Track Monad validator performance in real-time:
http://143.110.144.231

Features:
✅ Real-time validator leaderboard
✅ 14-day MEV trends
✅ Network statistics
✅ Auto-updating every 60 seconds

Built with ❤️ for the Monad community!
```

---

## Troubleshooting

### Issue: "Cannot connect to RPC"

**Solution:**
- Check `MONAD_RPC_URL` is correct
- Check network is actually live
- Try alternative RPC endpoints
- Check firewall isn't blocking port 8545

### Issue: "No validators returned"

**Solution:**
- Network might not have validators yet (wait)
- Check SDK method names (might be different)
- Print raw response: `print(monad_client.get_validators())`
- Ask in Monad Discord #developers

### Issue: "SDK import error"

**Solution:**
- Check package name: `pip list | grep monad`
- Check Python version: `python --version`
- Try reinstalling: `pip uninstall monad-sdk && pip install monad-sdk`

### Issue: "Dashboard shows no data"

**Solution:**
- Check API logs: `docker-compose logs api`
- Check ingestor logs: `docker-compose logs ingestor`
- Check database: `docker exec -it monadpulse_backend-db-1 psql -U trader -d monadpulse -c "SELECT COUNT(*) FROM validators;"`

---

## Fallback Plan

If Monad SDK is delayed or broken on launch day:

### Option 1: Use Web3.py Directly

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(os.getenv('MONAD_RPC_URL')))

# Get validators from staking contract
staking_contract = w3.eth.contract(
    address='0x....',  # Monad staking contract
    abi=STAKING_ABI
)

validators = staking_contract.functions.getValidators().call()
```

### Option 2: Scrape Monad Explorer

If there's a block explorer (like monad.xyz/validators):

```python
import requests
from bs4 import BeautifulSoup

response = requests.get('https://explorer.monad.xyz/validators')
soup = BeautifulSoup(response.text, 'html.parser')
# Parse validator data from HTML
```

### Option 3: Use GraphQL API

If Monad provides a GraphQL endpoint:

```python
import requests

query = """
{
  validators {
    address
    moniker
    votingPower
    commission
  }
}
"""

response = requests.post(
    'https://graphql.monad.xyz',
    json={'query': query}
)
validators = response.json()['data']['validators']
```

---

## Success Metrics

After integration, you should see:

✅ **Real validator names** (not "Eclipse Validator", "Phantom Node", etc.)
✅ **Accurate validator count** (should match other explorers)
✅ **Dashboard updates** every 60 seconds with fresh data
✅ **No errors** in ingestor logs
✅ **Users in Discord** saying "wow this is great!"

---

## Post-Launch Monitoring

### Day 1: Watch for errors
```bash
# SSH into VPS
ssh root@143.110.144.231

# Monitor logs continuously
cd /opt/monadpulse/monadpulse_backend
docker-compose logs -f
```

### Day 2-7: Gather feedback
- Monitor Monad Discord for mentions
- Track dashboard traffic (check Nginx logs)
- Note feature requests from users

### Day 8-10: Prepare for Omega Engine
- You've proven MonadPulse works
- You've built credibility
- Now you can build the secret weapon

---

## Next Steps After Successful Integration

1. **Announce in Discord** - Get users
2. **Monitor for bugs** - Fix issues fast
3. **Gather feedback** - What do users want?
4. **Plan Omega Engine** - Time to build the premium features
5. **Approach Foundation** - Show traction, ask for grant

**You're not done on Day 1. You're just getting started.**

But if you've successfully integrated real Monad data, you've proven you can execute.

That's worth more than any business plan.

---

## Resources

- **Monad Docs:** https://docs.monad.xyz/
- **Monad Discord:** https://discord.gg/monad
- **Monad GitHub:** https://github.com/monad-labs
- **Your Dashboard:** http://143.110.144.231

Good luck! 🚀
