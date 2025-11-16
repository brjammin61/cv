# MonadPulse Production Deployment Guide

This guide will take you from zero to a fully running MonadPulse production system in under 15 minutes.

## Prerequisites

- A domain name (recommended but optional)
  - If using a domain: `monadpulse.io` and `api.monadpulse.io` should point to your VPS IP
  - If no domain: You can use the VPS IP address directly

## Step 1: Provision a VPS

### Recommended Providers:
- **DigitalOcean**: Droplets starting at $6/month
- **AWS Lightsail**: Starting at $5/month
- **Linode**: Starting at $5/month
- **Vultr**: Starting at $6/month

### Minimum Specs:
- **CPU**: 1 core (2 cores recommended)
- **RAM**: 2GB minimum (4GB recommended for comfort)
- **Storage**: 25GB SSD
- **OS**: Ubuntu 22.04 LTS

### Quick Setup (DigitalOcean Example):
```bash
# 1. Create account at digitalocean.com
# 2. Create new Droplet
# 3. Choose Ubuntu 22.04 LTS
# 4. Choose $12/month plan (2GB RAM, 1 CPU)
# 5. Add your SSH key
# 6. Create droplet
# 7. Note the IP address (e.g., 159.89.123.45)
```

## Step 2: Connect to Your VPS

```bash
# From your local terminal
ssh root@YOUR_VPS_IP

# Example:
ssh root@159.89.123.45
```

## Step 3: Run Server Setup Script

This installs Docker, Nginx, SSL tools, and all dependencies.

```bash
# Download and run the setup script
curl -o setup_server.sh https://raw.githubusercontent.com/brjammin61/cv/claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE/monadpulse_backend/scripts/setup_server.sh

# Make it executable
chmod +x setup_server.sh

# Run it (takes 3-5 minutes)
./setup_server.sh
```

**Expected output**: You'll see green checkmarks as each component installs.

## Step 4: Configure Domains (Optional)

If you're using custom domains, update the deploy script:

```bash
# Before running deploy.sh, edit these lines:
nano /root/deploy.sh  # Or download it first

# Change these variables (lines 25-26):
DOMAIN_API="api.monadpulse.io"      # Your API domain
DOMAIN_FRONTEND="monadpulse.io"     # Your frontend domain

# If using IP address only, set both to your VPS IP:
DOMAIN_API="159.89.123.45"
DOMAIN_FRONTEND="159.89.123.45"
```

## Step 5: Run Deployment Script

This clones the repo, builds everything, and starts the services.

```bash
# Download the deployment script
curl -o deploy.sh https://raw.githubusercontent.com/brjammin61/cv/claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE/monadpulse_backend/scripts/deploy.sh

# Make it executable
chmod +x deploy.sh

# Run it (takes 5-10 minutes)
./deploy.sh
```

**What this does:**
1. Clones the cv repository to `/opt/monadpulse`
2. Creates production `.env` file with secure password
3. Starts backend API with Docker Compose
4. Builds React frontend with npm
5. Deploys frontend to `/var/www/monadpulse`
6. Configures Nginx reverse proxy
7. Starts all services

## Step 6: Setup SSL (Recommended)

If you're using a domain name:

```bash
# Run certbot to get free SSL certificates
certbot --nginx -d api.monadpulse.io -d monadpulse.io

# Answer the prompts:
# - Enter email address
# - Agree to terms
# - Choose "2" to redirect HTTP to HTTPS
```

If you're using an IP address, skip this step (you'll use HTTP).

## Step 7: Verify Deployment

### Test Backend API:
```bash
# From your local machine
curl http://YOUR_VPS_IP:8000/health
# OR
curl https://api.monadpulse.io/health

# Expected response:
# {"status":"healthy","timestamp":"2025-11-16T12:34:56","database":"connected"}
```

### Test Frontend:
```bash
# Open in your browser:
http://YOUR_VPS_IP
# OR
https://monadpulse.io

# You should see the MonadPulse dashboard with live data
```

### Test All Endpoints:
```bash
# KPI Stats
curl http://YOUR_VPS_IP:8000/stats/kpi

# Chart Data
curl http://YOUR_VPS_IP:8000/stats/chart

# Validator Leaderboard
curl http://YOUR_VPS_IP:8000/validators/leaderboard

# Omega Partners
curl http://YOUR_VPS_IP:8000/validators/omega
```

## Step 8: Monitor Your System

### View Backend Logs:
```bash
cd /opt/monadpulse/monadpulse_backend
docker-compose logs -f
```

### Check Service Status:
```bash
# Docker containers
docker ps

# Nginx status
systemctl status nginx

# Nginx error logs
tail -f /var/log/nginx/error.log
```

### Restart Services:
```bash
# Restart backend
cd /opt/monadpulse/monadpulse_backend
docker-compose restart

# Restart Nginx
systemctl restart nginx
```

## Troubleshooting

### Backend API not responding:
```bash
# Check if containers are running
docker ps

# View backend logs
cd /opt/monadpulse/monadpulse_backend
docker-compose logs api

# Restart backend
docker-compose restart
```

### Frontend not loading:
```bash
# Check Nginx logs
tail -f /var/log/nginx/error.log

# Verify frontend files exist
ls -la /var/www/monadpulse

# Restart Nginx
systemctl restart nginx
```

### Database connection issues:
```bash
# Check database container
docker ps | grep postgres

# View database logs
cd /opt/monadpulse/monadpulse_backend
docker-compose logs db
```

### Port conflicts:
```bash
# Check what's using port 8000
lsof -i :8000

# Check what's using port 80
lsof -i :80
```

## Next Steps After Deployment

1. **Test the live dashboard** - Open it in your browser and verify all data loads
2. **Share the link** - Give the URL to others to test
3. **Monitor logs** - Watch for any errors in the first 24 hours
4. **Plan Monad SDK integration** - When mainnet launches Nov 24, you'll integrate real data

## Updating the System

When you make code changes and want to deploy them:

```bash
# SSH into your VPS
ssh root@YOUR_VPS_IP

# Run the deploy script again
cd /opt/monadpulse
./deploy.sh

# This will:
# - Pull latest code from git
# - Rebuild backend containers
# - Rebuild frontend
# - Restart all services
```

## Production URLs

After successful deployment:

- **Frontend Dashboard**: `https://monadpulse.io` (or `http://YOUR_VPS_IP`)
- **Backend API**: `https://api.monadpulse.io` (or `http://YOUR_VPS_IP:8000`)
- **API Docs**: `https://api.monadpulse.io/docs`
- **Health Check**: `https://api.monadpulse.io/health`

## Cost Estimate

- VPS: $6-12/month
- Domain: $10-15/year (optional)
- SSL: FREE (Let's Encrypt)

**Total**: $6-12/month

## Support

If you encounter issues during deployment:
1. Check the troubleshooting section above
2. Review logs: `docker-compose logs -f`
3. Ensure all ports are open: `ufw status`
4. Verify domain DNS is pointing to VPS IP

---

**You're ready to launch!** 🚀

Once deployed, your MonadPulse system will be live and accessible 24/7. The ingestor updates data every 2 minutes, and the dashboard auto-refreshes every 5 seconds.
