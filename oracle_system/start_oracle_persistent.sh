#!/bin/bash
# Start The Oracle in persistent mode
# This keeps running even if you close your terminal or computer sleeps

cd /home/user/cv/oracle_system

# Kill any existing Oracle processes
echo "Stopping any existing Oracle processes..."
pkill -f run_oracle_system
sleep 2

# Start Oracle with nohup (no hangup)
echo "Starting Oracle in persistent mode..."
nohup python3 run_oracle_system.py --mode paper > logs/oracle_persistent.log 2>&1 &

# Get the PID
ORACLE_PID=$!
echo $ORACLE_PID > /tmp/oracle.pid

sleep 3

# Check if it started
if ps -p $ORACLE_PID > /dev/null; then
    echo "✅ Oracle started successfully!"
    echo "   PID: $ORACLE_PID"
    echo "   Log: logs/oracle_persistent.log"
    echo ""
    echo "📊 To monitor: python3 terminal_monitor.py"
    echo "⏹️  To stop: kill $ORACLE_PID (or: pkill -f run_oracle_system)"
    echo ""
    echo "The Oracle will keep running even if you:"
    echo "  - Close this terminal"
    echo "  - Close your SSH connection"
    echo "  - Put your computer to sleep"
    echo ""
    echo "It will only stop if:"
    echo "  - You manually stop it (kill command)"
    echo "  - The server restarts"
    echo "  - The process crashes"
else
    echo "❌ Failed to start Oracle"
    echo "Check logs/oracle_persistent.log for errors"
fi
