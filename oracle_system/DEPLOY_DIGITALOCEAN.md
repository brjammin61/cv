# 🔮 Deploy The Oracle to DigitalOcean

Complete guide to deploying The Oracle on a DigitalOcean droplet.

---

## Step 1: Create Droplet

1. Go to https://cloud.digitalocean.com/droplets/new
2. **Choose Image:** Ubuntu 22.04 LTS x64
3. **Choose Size:** Basic - $6/month (1GB RAM, 1 vCPU) is sufficient
4. **Choose Region:** Closest to you
5. **Authentication:** SSH key (recommended) or Password
6. **Hostname:** `oracle-system` (or whatever you prefer)
7. Click **Create Droplet**

Wait 60 seconds for droplet to be created.

---

## Step 2: Get Your Droplet IP

Once created, you'll see your droplet's **public IP address**.

Example: `134.209.123.456`

Copy this IP - you'll need it!

---

## Step 3: SSH Into Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

(Replace YOUR_DROPLET_IP with the actual IP from Step 2)

If prompted about fingerprint, type `yes`

---

## Step 4: Run One-Line Setup

Once connected via SSH, run this single command:

```bash
curl -sSL https://raw.githubusercontent.com/brjammin61/cv/claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb/oracle_system/setup_droplet.sh | bash
```

**OR** if you prefer to review the script first:

```bash
# Clone the repo
git clone https://github.com/brjammin61/cv.git
cd cv
git checkout claude/build-feature-01Am47fqpC7CFtcVXLJ7VUDb

# Run setup
cd oracle_system
chmod +x setup_droplet.sh
./setup_droplet.sh
```

The setup script will:
- ✅ Install Python, pip, git, and dependencies
- ✅ Clone the Oracle repository
- ✅ Install all Python packages
- ✅ Configure your Kalshi API keys
- ✅ Set up systemd services (auto-start on boot)
- ✅ Start Oracle and Dashboard

---

## Step 5: Configure API Keys

During setup, you'll be prompted for:

```
Enter your Kalshi API Key: e31300f6-6e71-4572-8068-89d7844b66e2
Enter path to your Kalshi private key PEM file: /root/.kalshi/private_key.pem
```

**Note:** You'll need to upload your `private_key.pem` to the droplet first:

From your **local Mac**, run:
```bash
scp /Users/benmonaco/.kalshi/private_key.pem root@YOUR_DROPLET_IP:/root/.kalshi/
```

---

## Step 6: Access Your Dashboard

Once setup completes, open your browser to:

**→ http://YOUR_DROPLET_IP:8080**

You should see the beautiful Oracle dashboard! 🎉

---

## Management Commands

SSH into your droplet and use these commands:

### Check Status
```bash
systemctl status oracle
systemctl status oracle-dashboard
```

### View Logs
```bash
journalctl -u oracle -f           # Oracle logs
journalctl -u oracle-dashboard -f # Dashboard logs
```

### Restart Services
```bash
systemctl restart oracle
systemctl restart oracle-dashboard
```

### Stop Services
```bash
systemctl stop oracle
systemctl stop oracle-dashboard
```

### Start Services
```bash
systemctl start oracle
systemctl start oracle-dashboard
```

---

## File Locations on Droplet

```
/opt/oracle/                          # Oracle system
/opt/oracle/data/oracle_data.db       # Database
/opt/oracle/logs/                     # Log files
/opt/oracle/config/api_keys.py        # API configuration
/etc/systemd/system/oracle.service    # Oracle service
/etc/systemd/system/oracle-dashboard.service  # Dashboard service
```

---

## Security Notes

### Open Port 8080
Dashboard runs on port 8080. Make sure it's open:

```bash
ufw allow 8080/tcp
ufw allow 22/tcp   # SSH
ufw enable
```

### Optional: Add HTTPS (Later)
For production with a domain, you can add nginx + Let's Encrypt SSL.

---

## Troubleshooting

### Dashboard not loading?
```bash
# Check if service is running
systemctl status oracle-dashboard

# Check logs
journalctl -u oracle-dashboard -f

# Restart
systemctl restart oracle-dashboard
```

### Oracle not collecting data?
```bash
# Check if service is running
systemctl status oracle

# Check logs
journalctl -u oracle -f

# Verify API keys
cat /opt/oracle/config/api_keys.py
```

### Check if ports are open
```bash
netstat -tlnp | grep :8080
```

---

## Costs

**DigitalOcean Droplet:** ~$6/month (Basic 1GB)
**Bandwidth:** Included (1TB transfer)
**Total:** ~$6/month

**Optional upgrades:**
- 2GB RAM droplet: $12/month (better for high-volume trading)
- Backups: +20% ($1.20/month for 6GB)

---

## Next Steps After Deployment

1. ✅ Monitor for 7 days in PAPER mode
2. ✅ Verify win rate reaches 65%+
3. ✅ Review signals and performance
4. ✅ Switch to LIVE mode if satisfied

To switch to LIVE mode:
```bash
# Edit config
nano /opt/oracle/run_oracle_system.py

# Change --mode paper to --mode live

# Restart
systemctl restart oracle
```

---

## Support

If you run into issues:
1. Check logs: `journalctl -u oracle -f`
2. Verify API keys are correct
3. Ensure port 8080 is open
4. Check the GitHub repo for updates

---

**That's it! The Oracle is now running 24/7 on DigitalOcean!** 🚀
