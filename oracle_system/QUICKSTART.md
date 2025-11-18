# 🚀 Quick Start - Deploy Oracle to DigitalOcean

**Total time: ~5 minutes**

---

## 1️⃣ Create Droplet (2 min)

1. Go to https://cloud.digitalocean.com/droplets/new
2. Choose: **Ubuntu 22.04 LTS**
3. Plan: **Basic - $6/month** (1GB RAM)
4. Click **Create Droplet**
5. Copy your droplet's **IP address**

---

## 2️⃣ Upload Your Private Key (1 min)

From your **Mac terminal**:

```bash
scp /Users/benmonaco/.kalshi/private_key.pem root@YOUR_DROPLET_IP:/root/.kalshi/
```

(Replace YOUR_DROPLET_IP with your actual IP)

When prompted, type `yes` and enter your droplet password (emailed to you).

---

## 3️⃣ SSH Into Droplet (1 min)

```bash
ssh root@YOUR_DROPLET_IP
```

---

## 4️⃣ Run Setup Script (2 min)

Copy and paste this entire command:

```bash
apt-get update && apt-get install -y git && \
git clone https://github.com/brjammin61/cv.git /opt/oracle && \
cd /opt/oracle && \
git checkout claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb && \
cd oracle_system && \
chmod +x setup_droplet.sh && \
./setup_droplet.sh
```

When prompted, enter:
- **Kalshi API Key:** `e31300f6-6e71-4572-8068-89d7844b66e2`

---

## 5️⃣ Open Dashboard ✨

In your browser, go to:

**http://YOUR_DROPLET_IP:8080**

---

## ✅ Done!

The Oracle is now:
- ✅ Running 24/7
- ✅ Collecting real Kalshi data
- ✅ Auto-starts on reboot
- ✅ Dashboard accessible from anywhere

---

## 🎮 Useful Commands

```bash
# View Oracle logs (live)
journalctl -u oracle -f

# View Dashboard logs (live)
journalctl -u oracle-dashboard -f

# Check status
systemctl status oracle
systemctl status oracle-dashboard

# Restart services
systemctl restart oracle
systemctl restart oracle-dashboard
```

---

## 📊 What Happens Next?

1. Oracle collects data for **10-15 minutes** to build price history
2. First signals will appear automatically
3. System runs in **PAPER mode** (simulated trades, real data)
4. Monitor for **7 days** to validate performance
5. If win rate ≥ 65%, switch to **LIVE mode**

---

## 🔥 Switch to Live Trading (After 7-Day Validation)

```bash
ssh root@YOUR_DROPLET_IP
nano /opt/oracle/oracle_system/run_oracle_system.py
```

Change line with `--mode paper` to `--mode live`

Save and exit (Ctrl+X, Y, Enter)

```bash
systemctl restart oracle
```

**⚠️ ONLY do this after verifying 7-day paper trading results!**

---

## 💰 Cost

- DigitalOcean Droplet: **$6/month**
- Bandwidth: **Included** (1TB)
- **Total: $6/month**

---

## 🆘 Troubleshooting

**Dashboard won't load?**
```bash
systemctl status oracle-dashboard
journalctl -u oracle-dashboard -f
```

**Oracle not collecting data?**
```bash
systemctl status oracle
journalctl -u oracle -f
```

**Check if ports are open:**
```bash
ufw status
```

Should show:
```
8080/tcp    ALLOW
22/tcp      ALLOW
```

---

**Questions? Check DEPLOY_DIGITALOCEAN.md for full details!**
