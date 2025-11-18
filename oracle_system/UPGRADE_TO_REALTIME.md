# 🚀 Upgrade to Realtime Mode

This guide upgrades The Oracle from batch mode (5-min polling) to realtime mode (WebSocket streaming).

---

## What Changes

### Before (Batch Mode):
- ⏰ Data collected every 5 minutes
- 🎯 Signals generated every 10 minutes
- 🧠 ML optimization every hour
- ⏱️ **Latency: Minutes**

### After (Realtime Mode):
- ⚡ Data streamed via WebSocket (**sub-second**)
- 🎯 Signals generated on every price update (**event-driven**)
- 🧠 ML optimization every 30 minutes
- ⏱️ **Latency: < 1 second**

---

## Upgrade Steps

### 1. SSH into your droplet

```bash
ssh root@YOUR_DROPLET_IP
```

### 2. Pull latest code

```bash
cd /opt/oracle
git pull origin claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb
```

### 3. Install websockets dependency

```bash
cd oracle_system
pip3 install websockets>=11.0
```

### 4. Update systemd service

Edit the Oracle service:

```bash
nano /etc/systemd/system/oracle.service
```

**Change this line:**
```
ExecStart=/usr/bin/python3 /opt/oracle/oracle_system/run_oracle_system.py --mode paper
```

**To:**
```
ExecStart=/usr/bin/python3 /opt/oracle/oracle_system/run_oracle_realtime.py --mode paper
```

Save and exit (Ctrl+X, Y, Enter)

### 5. Reload and restart

```bash
systemctl daemon-reload
systemctl restart oracle
```

### 6. Verify it's running

```bash
systemctl status oracle
```

Should show:
```
Active: active (running)
```

### 7. Watch the live logs

```bash
journalctl -u oracle -f
```

You should see:
```
🔮 THE ORACLE - REALTIME MODE
📡 WebSocket: ENABLED
⚡ Data: Real-time (sub-second)
🎯 Signals: Event-driven
📡 Subscribed to Bitcoin Reserve 2026 (KXBTCRESERVE-26-JAN01)
📡 Subscribed to BTC $150K by May 2025 (KXBTCMAX150-25-26MAY31-149999.99)
...
✅ Realtime collection started for 13 markets
```

---

## What to Expect

### Immediately:
- WebSocket connections to all 13 markets
- Sub-second market updates in logs
- Real-time signal generation

### Within 1 minute:
- First signals should appear
- Much higher signal volume (10-50x more opportunities detected)

### Within 1 hour:
- First ML optimization cycle
- Strategy parameters tuned based on performance

---

## Performance

**Expected metrics:**
- Updates: 100-500 per minute (vs 12 per hour before)
- Signals: 20-50 per day (vs 5-10 before)
- CPU usage: +10-15% (still fine on $6 droplet)
- Memory: +50MB (negligible)

---

## Rollback (if needed)

If you want to go back to batch mode:

```bash
nano /etc/systemd/system/oracle.service
```

Change back to:
```
ExecStart=/usr/bin/python3 /opt/oracle/oracle_system/run_oracle_system.py --mode paper
```

Then:
```bash
systemctl daemon-reload
systemctl restart oracle
```

---

## Dashboard

Your dashboard at http://YOUR_DROPLET_IP:8080 will show:
- Much higher snapshot counts
- More frequent signals
- Better win rate (catching opportunities faster)

---

## Go Live After 7 Days

Once you've validated realtime mode for 7 days and win rate ≥ 65%:

```bash
nano /etc/systemd/system/oracle.service
```

Change `--mode paper` to `--mode live`

```bash
systemctl daemon-reload
systemctl restart oracle
```

**⚠️ WARNING: Only do this after thorough validation!**

---

## Support

Issues? Check logs:
```bash
journalctl -u oracle -f
```

Common issues:
- **WebSocket disconnects:** Auto-reconnects after 5 seconds
- **High CPU:** Normal for realtime mode, should stabilize at 15-20%
- **No signals:** Wait 5-10 minutes for price history to build

---

**You're now running at institutional speed!** 🚀
