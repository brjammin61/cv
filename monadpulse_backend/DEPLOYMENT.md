# MonadPulse Production Deployment Guide

This guide walks you through deploying MonadPulse to a production server (AWS, DigitalOcean, etc.).

---

## 📋 Prerequisites

- Ubuntu 20.04+ or similar Linux server
- At least 2GB RAM, 2 CPU cores
- 20GB+ disk space
- Root or sudo access
- Domain name (optional but recommended): `api.monadpulse.io`

---

## 🚀 Step-by-Step Deployment

### Step 1: Initial Server Setup

SSH into your server:
```bash
ssh root@your-server-ip
```

Update system packages:
```bash
apt update && apt upgrade -y
```

Install required tools:
```bash
apt install -y git curl ufw
```

### Step 2: Install Docker

```bash
# Download Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run installation
sh get-docker.sh

# Enable Docker to start on boot
systemctl enable docker

# Start Docker
systemctl start docker

# Verify installation
docker --version
```

### Step 3: Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### Step 4: Setup Firewall

```bash
# Allow SSH (important - don't lock yourself out!)
ufw allow 22/tcp

# Allow HTTP & HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow API port (if you want direct access)
ufw allow 8000/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

### Step 5: Clone Repository

```bash
# Create application directory
mkdir -p /opt/monadpulse
cd /opt/monadpulse

# Clone your repository
git clone <your-repository-url> .

# Or if uploading via SCP:
# From your local machine:
# scp -r monadpulse_backend root@your-server-ip:/opt/monadpulse/
```

### Step 6: Configure Environment

```bash
cd /opt/monadpulse

# Copy example environment file
cp .env.example .env

# Edit with secure credentials
nano .env
```

**Critical**: Change the default password!

```env
# Use a strong, random password
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Production logging
LOG_LEVEL=WARNING

# Longer update interval for production
UPDATE_INTERVAL_SECONDS=120
```

Save and exit (Ctrl+X, Y, Enter in nano).

### Step 7: Launch Services

```bash
# Build and start
./launch.sh

# Or manually:
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 8: Verify Deployment

Test the API:
```bash
# Health check
curl http://localhost:8000/health

# Get KPI stats
curl http://localhost:8000/stats/kpi

# Test from external machine
curl http://your-server-ip:8000/health
```

---

## 🌐 Setup Domain and SSL (Recommended)

### Install Nginx

```bash
apt install -y nginx
```

### Configure Nginx as Reverse Proxy

Create Nginx configuration:
```bash
nano /etc/nginx/sites-available/monadpulse
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name api.monadpulse.io;  # Replace with your domain

    # CORS headers
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
ln -s /etc/nginx/sites-available/monadpulse /etc/nginx/sites-enabled/
nginx -t  # Test configuration
systemctl restart nginx
```

### Setup SSL with Let's Encrypt

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d api.monadpulse.io

# Follow prompts (use your email, agree to terms, select redirect HTTP to HTTPS)

# Test auto-renewal
certbot renew --dry-run
```

Your API is now available at: `https://api.monadpulse.io`

---

## 🔐 Security Hardening

### 1. Create Non-Root User

```bash
# Create user
adduser monadpulse

# Add to docker group
usermod -aG docker monadpulse

# Add to sudo group
usermod -aG sudo monadpulse

# Switch to new user
su - monadpulse

# Move application
sudo mv /opt/monadpulse /home/monadpulse/
sudo chown -R monadpulse:monadpulse /home/monadpulse/monadpulse
```

### 2. Disable Root SSH Login

```bash
sudo nano /etc/ssh/sshd_config
```

Change:
```
PermitRootLogin no
PasswordAuthentication no  # Use SSH keys only
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### 3. Setup Automatic Security Updates

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 📊 Monitoring and Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ingestor
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100 api
```

### Check Resource Usage

```bash
# System resources
htop

# Docker stats
docker stats

# Disk usage
df -h
docker system df
```

### Database Backup

```bash
# Create backup directory
mkdir -p /home/monadpulse/backups

# Backup database
docker-compose exec -T db pg_dump -U trader monadpulse > /home/monadpulse/backups/backup-$(date +%Y%m%d-%H%M%S).sql

# Restore from backup
cat backup.sql | docker-compose exec -T db psql -U trader monadpulse
```

### Setup Automated Backups

Create backup script:
```bash
nano /home/monadpulse/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/monadpulse/backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/monadpulse-$DATE.sql"

# Create backup
docker-compose -f /home/monadpulse/monadpulse/docker-compose.yml exec -T db pg_dump -U trader monadpulse > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Delete backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

Make executable and add to cron:
```bash
chmod +x /home/monadpulse/backup.sh

# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/monadpulse/backup.sh >> /home/monadpulse/backup.log 2>&1
```

---

## 🔄 Updates and Maintenance

### Update Application Code

```bash
cd /home/monadpulse/monadpulse

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or use the launch script
./launch.sh
```

### Update Docker Images

```bash
# Pull latest base images
docker-compose pull

# Rebuild
docker-compose up -d --build
```

### Clean Up Old Data

```bash
# Remove old Docker images
docker image prune -a

# Remove old containers
docker container prune

# Remove unused volumes (BE CAREFUL - this deletes data!)
docker volume prune
```

---

## 🚨 Troubleshooting Production Issues

### API Returns 502/503

```bash
# Check if services are running
docker-compose ps

# Check API logs
docker-compose logs api

# Restart services
docker-compose restart
```

### Database Connection Errors

```bash
# Check database health
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### High Resource Usage

```bash
# Check resource usage
docker stats

# Reduce ingestor frequency (edit .env)
UPDATE_INTERVAL_SECONDS=300  # 5 minutes instead of 1

# Restart ingestor
docker-compose restart ingestor
```

### Disk Space Issues

```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a --volumes

# Delete old logs
docker-compose logs --no-log-prefix > /dev/null
```

---

## 📈 Scaling for High Traffic

### Vertical Scaling (Easier)

Upgrade server resources:
- 4GB RAM → 8GB RAM
- 2 CPUs → 4 CPUs

No code changes needed.

### Horizontal Scaling (Advanced)

Use multiple API containers:

```yaml
# In docker-compose.yml
services:
  api:
    deploy:
      replicas: 3  # Run 3 API instances
```

Add load balancer (Nginx):
```nginx
upstream monadpulse_api {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    location / {
        proxy_pass http://monadpulse_api;
    }
}
```

---

## ✅ Production Launch Checklist

- [ ] Server setup complete
- [ ] Docker & Docker Compose installed
- [ ] Firewall configured
- [ ] Application deployed
- [ ] Strong database password set
- [ ] Domain configured (optional)
- [ ] SSL certificate installed (optional)
- [ ] Non-root user created
- [ ] Root SSH disabled
- [ ] Automatic backups configured
- [ ] Monitoring in place
- [ ] Health checks passing
- [ ] React frontend connected successfully
- [ ] Performance tested under load

---

## 🎯 Day 1 Launch Strategy

**10 Days Before Mainnet:**
1. Deploy to production server
2. Test with React frontend
3. Monitor for 24 hours

**Mainnet Day (Nov 24):**
1. Ensure all services healthy
2. Monitor logs for errors
3. Watch for traffic spikes

**Day 1-7:**
1. Monitor performance
2. Collect user feedback
3. Optimize queries if needed

**Day 15:**
1. Post MonadPulse in Monad Discord
2. Drive traffic to your dashboard

**Day 31:**
1. Approach Monad Foundation with metrics
2. Showcase validator rankings and MEV data
3. Pitch for ecosystem grant

---

## 📞 Support

If you encounter issues during deployment:
1. Check logs: `docker-compose logs -f`
2. Verify all services are healthy: `docker-compose ps`
3. Test API manually: `curl http://localhost:8000/health`
4. Review this guide for missed steps

---

**Ready to launch. Let's dominate the Monad ecosystem.**

🚀 Built for mainnet. Ready for millions of users.
