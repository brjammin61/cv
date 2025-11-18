# Deploy Automated Trading to Production Server

## Production Server Details
- **IP**: 159.223.201.145
- **Dashboard**: http://159.223.201.145:8080/
- **Current Status**: Collecting 6,582+ snapshots, generating 342 signals

## What Needs to be Deployed

All these features are in the git repo and need to be on production:

### ✅ Features Ready to Deploy:
1. **AutoExecutor** - Automated paper/live trading execution
2. **ML Optimizer** - Machine learning that improves over time
3. **Signal Auto-Evaluation** - Every signal is automatically evaluated
4. **Risk Management** - $50 max per trade, $250 total exposure, 3¢ min edge
5. **Politics/Economics Focus** - Markets configured for behavioral trading

### 📦 Git Commits to Pull:
```
e776446 - Implement paper trading with auto-execution and ML learning
9dd6afe - Refocus strategy on politics/economics markets only
6044d25 - Fix database schema mismatch preventing signal generation
c390fa8 - Fix market discovery and add diagnostic scripts
```

## Deployment Steps

### SSH into Production Server:
```bash
ssh root@159.223.201.145
```

### Pull Latest Code:
```bash
cd /opt/oracle/oracle_system  # or wherever Oracle is installed
git fetch origin
git pull origin claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb
```

### Verify AutoExecutor is Present:
```bash
grep -n "AutoExecutor" run_oracle_fast.py
# Should show imports and usage
```

### Restart Oracle:
```bash
# Stop current Oracle process
pkill -f "run_oracle_fast.py"

# Start with new code
nohup python3 run_oracle_fast.py > logs/oracle_live.log 2>&1 &

# Check it's running
ps aux | grep run_oracle_fast
```

### Verify Automated Trading is Active:
```bash
tail -f logs/oracle_live.log
```

Look for these log lines:
- ✅ `AutoExecutor initialized in PAPER mode`
- ✅ `ML Optimizer: ENABLED`
- ✅ `Auto-Execution: ENABLED (PAPER MODE)`
- ✅ `✅ Executing: <reason>`
- ✅ `💵 TRADE EXECUTED: PAPER | Size: $XX.XX`

### Check Dashboard:
Visit http://159.223.201.145:8080/ and verify:
- ✅ Signals are being generated
- ✅ Trades are being executed (check P&L column)
- ✅ Win rate starts tracking
- ✅ ML is learning from outcomes

## Current Risk Settings (PAPER MODE):

```python
max_position_size_usd = 50.0      # $50 max per trade
max_total_exposure_usd = 250.0    # $250 total exposure
min_edge_to_trade = 3.0           # 3¢ minimum edge
min_conviction = "MEDIUM"         # MEDIUM+ signals only
max_trades_per_day = 10           # Max 10 trades/day
```

## After 7 Days of Paper Trading:

Review performance:
```bash
cd /opt/oracle/oracle_system
python3 -c "
from modules import SignalTracker
tracker = SignalTracker()
stats = tracker.get_performance_stats()
print(f'Win Rate: {stats[\"win_rate\"]}')
print(f'Total P&L: {stats[\"total_pnl\"]}')
print(f'Trades: {stats[\"total_trades\"]}')
"
```

If performance is good (>55% win rate, positive P&L):
1. Fund your Kalshi account
2. Change mode to `ExecutionMode.LIVE` in run_oracle_fast.py
3. Restart Oracle
4. Monitor closely!

## Rollback Plan (If Issues):

```bash
cd /opt/oracle/oracle_system
git checkout ac4e915  # Previous stable version
pkill -f run_oracle_fast
nohup python3 run_oracle_fast.py > logs/oracle_live.log 2>&1 &
```

---

**IMPORTANT**: Make sure Kalshi private key is configured on production!
Check: `grep KALSHI_PRIVATE_KEY_PATH config/api_keys.py`
