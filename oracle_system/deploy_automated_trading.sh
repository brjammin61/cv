#!/bin/bash
# Deploy automated trading to production Oracle instance

set -e  # Exit on error

echo "================================================================================"
echo "🚀 DEPLOYING AUTOMATED TRADING TO PRODUCTION"
echo "================================================================================"
echo

# Check we're in the right directory
if [ ! -f "run_oracle_fast.py" ]; then
    echo "❌ Error: Not in oracle_system directory"
    echo "   Please run from /opt/oracle/oracle_system (or wherever Oracle is installed)"
    exit 1
fi

# Backup current state
echo "[1] Creating backup..."
BACKUP_DIR="backups/pre-auto-trading-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
# Copy all files except backups directory
rsync -a --exclude='backups' --exclude='logs/*.log' --exclude='data/*.db' --exclude='.git' --exclude='__pycache__' . "$BACKUP_DIR/" 2>/dev/null || \
    find . -maxdepth 1 -type f -exec cp {} "$BACKUP_DIR/" \; && \
    find . -maxdepth 1 -type d ! -name '.' ! -name 'backups' ! -name '.git' -exec cp -r {} "$BACKUP_DIR/" \;
echo "✅ Backup created: $BACKUP_DIR"
echo

# Pull latest code
echo "[2] Pulling latest code from git..."
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)
echo "   Current branch: $CURRENT_BRANCH"

# If not on the feature branch, switch to it
if [ "$CURRENT_BRANCH" != "claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb" ]; then
    echo "   Switching to feature branch..."
    git checkout claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb
fi

echo "   Pulling changes..."
git pull origin claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb
echo "✅ Code updated"
echo

# Verify critical files exist
echo "[3] Verifying automated trading components..."
MISSING=0

if ! grep -q "AutoExecutor" run_oracle_fast.py; then
    echo "❌ AutoExecutor not found in run_oracle_fast.py"
    MISSING=1
fi

if [ ! -f "modules/mod_09_auto_executor.py" ]; then
    echo "❌ modules/mod_09_auto_executor.py missing"
    MISSING=1
fi

if [ ! -f "modules/mod_10_ml_optimizer.py" ]; then
    echo "❌ modules/mod_10_ml_optimizer.py missing"
    MISSING=1
fi

if [ $MISSING -eq 1 ]; then
    echo "❌ Critical files missing. Deployment aborted."
    exit 1
fi

echo "✅ All components verified"
echo

# Check Kalshi credentials
echo "[4] Checking Kalshi credentials..."
if grep -q "/path/to/your/kalshi_private_key.pem" config/api_keys.py; then
    echo "⚠️  WARNING: Kalshi private key not configured!"
    echo "   KALSHI_PRIVATE_KEY_PATH still points to placeholder"
    echo
    echo "   Oracle will run in SIMULATION mode until you configure:"
    echo "   1. Save your Kalshi RSA private key to a secure location"
    echo "   2. Update config/api_keys.py with the correct path"
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment aborted."
        exit 1
    fi
else
    echo "✅ Kalshi credentials configured"
fi
echo

# Stop current Oracle
echo "[5] Stopping current Oracle process..."
if pgrep -f "run_oracle_fast.py" > /dev/null; then
    pkill -f "run_oracle_fast.py"
    sleep 3
    echo "✅ Oracle stopped"
else
    echo "✅ No Oracle process running"
fi
echo

# Start new Oracle with automated trading
echo "[6] Starting Oracle with automated trading..."
nohup python3 run_oracle_fast.py > logs/oracle_live.log 2>&1 &
ORACLE_PID=$!
sleep 2

if ps -p $ORACLE_PID > /dev/null; then
    echo "✅ Oracle started (PID: $ORACLE_PID)"
else
    echo "❌ Failed to start Oracle. Check logs/oracle_live.log"
    exit 1
fi
echo

# Verify automated trading is active
echo "[7] Verifying automated trading..."
sleep 3

if grep -q "AutoExecutor initialized" logs/oracle_live.log; then
    echo "✅ AutoExecutor initialized"
else
    echo "⚠️  AutoExecutor not found in logs (might need more time)"
fi

if grep -q "ML Optimizer: ENABLED" logs/oracle_live.log; then
    echo "✅ ML Optimizer enabled"
else
    echo "⚠️  ML Optimizer not found in logs"
fi

echo

# Show current status
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "================================================================================"
echo
echo "📊 Current Status:"
ps aux | grep run_oracle_fast | grep -v grep || echo "   Oracle not running"
echo
echo "📝 Next Steps:"
echo "   1. Monitor logs: tail -f logs/oracle_live.log"
echo "   2. Check dashboard: http://$(hostname -I | awk '{print $1}'):8080/"
echo "   3. Look for 'TRADE EXECUTED' messages"
echo "   4. After 7 days, review performance and consider live trading"
echo
echo "📈 Risk Settings (PAPER MODE):"
echo "   - Max per trade: \$50"
echo "   - Total exposure: \$250"
echo "   - Min edge: 3¢"
echo "   - Min conviction: MEDIUM+"
echo "   - Max trades/day: 10"
echo
echo "🔙 Rollback (if needed):"
echo "   cd $BACKUP_DIR && ./deploy.sh"
echo
echo "================================================================================"
