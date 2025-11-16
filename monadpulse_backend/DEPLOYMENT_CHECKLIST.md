# MonadPulse Deployment Checklist

Copy this checklist and check off each item as you complete it.

## Pre-Deployment

- [ ] Choose VPS provider (DigitalOcean, AWS, Linode, Vultr)
- [ ] Create account and add payment method
- [ ] (Optional) Register domain name
- [ ] (Optional) Point domain DNS to VPS IP

## VPS Provisioning

- [ ] Create Ubuntu 22.04 droplet/instance
- [ ] Minimum specs: 2GB RAM, 1 CPU, 25GB storage
- [ ] Add SSH key for access
- [ ] Note the VPS IP address: `___________________`
- [ ] Successfully SSH into VPS: `ssh root@YOUR_IP`

## Server Setup

- [ ] Download setup script:
  ```bash
  curl -o setup.sh https://raw.githubusercontent.com/brjammin61/cv/claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE/monadpulse_backend/scripts/setup_server.sh
  ```
- [ ] Make executable: `chmod +x setup.sh`
- [ ] Run setup: `./setup.sh` (wait 3-5 minutes)
- [ ] Verify Docker installed: `docker --version`
- [ ] Verify Docker Compose installed: `docker-compose --version`
- [ ] Verify Nginx installed: `nginx -v`

## Deployment

- [ ] Download deploy script:
  ```bash
  curl -o deploy.sh https://raw.githubusercontent.com/brjammin61/cv/claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE/monadpulse_backend/scripts/deploy.sh
  ```
- [ ] Make executable: `chmod +x deploy.sh`
- [ ] (Optional) Edit domains in deploy.sh if using custom domain
- [ ] Run deployment: `./deploy.sh` (wait 5-10 minutes)
- [ ] Verify 3 Docker containers running: `docker ps`
- [ ] Verify Nginx running: `systemctl status nginx`

## Testing

- [ ] Test backend health: `curl http://YOUR_IP:8000/health`
- [ ] Test KPI endpoint: `curl http://YOUR_IP:8000/stats/kpi`
- [ ] Test chart endpoint: `curl http://YOUR_IP:8000/stats/chart`
- [ ] Test validators endpoint: `curl http://YOUR_IP:8000/validators/leaderboard`
- [ ] Open frontend in browser: `http://YOUR_IP`
- [ ] Verify dashboard loads with validator data
- [ ] Verify charts render correctly
- [ ] Verify auto-refresh works (wait 5 seconds)

## SSL Setup (Optional, if using domain)

- [ ] Verify DNS propagation: `nslookup yourdomain.com`
- [ ] Run certbot:
  ```bash
  certbot --nginx -d yourdomain.com -d api.yourdomain.com
  ```
- [ ] Enter email address when prompted
- [ ] Agree to terms of service
- [ ] Choose option 2 (redirect HTTP to HTTPS)
- [ ] Test HTTPS: `https://yourdomain.com`
- [ ] Test API HTTPS: `https://api.yourdomain.com/health`

## Monitoring Setup

- [ ] Bookmark backend logs command: `cd /opt/monadpulse/monadpulse_backend && docker-compose logs -f`
- [ ] Test restart: `docker-compose restart`
- [ ] Verify system comes back up
- [ ] Check Nginx logs: `tail -f /var/log/nginx/error.log`
- [ ] Save VPS IP and credentials securely

## Post-Deployment

- [ ] Share dashboard URL with 3 test users
- [ ] Monitor logs for first hour
- [ ] Test from different devices (mobile, desktop)
- [ ] Test from different browsers (Chrome, Firefox, Safari)
- [ ] Document any errors or issues
- [ ] Set calendar reminder for Nov 24 (Monad mainnet launch)

## Launch Day Preparation (Nov 24, 2025)

- [ ] Read Monad SDK integration guide in README
- [ ] Update `ingestor/ingestor.py` with real SDK calls
- [ ] Test with live Monad data
- [ ] Deploy updated code
- [ ] Verify real validator data appears
- [ ] Share in Monad Discord
- [ ] Monitor for errors
- [ ] Collect user feedback

## Maintenance Tasks

- [ ] Set up monitoring alerts (optional)
- [ ] Schedule weekly log reviews
- [ ] Plan Omega Engine development (Track 2)
- [ ] Prepare Foundation pitch materials
- [ ] Track usage metrics and user feedback

---

## Deployment Summary

**VPS IP**: `___________________`

**Domain (if used)**: `___________________`

**Frontend URL**: `___________________`

**API URL**: `___________________`

**Deployment Date**: `___________________`

**Total Cost**: $____/month

**Status**: 
- [ ] Fully deployed and operational
- [ ] Ready for mainnet integration
- [ ] Shared with community

---

**Congratulations!** 🎉

Your MonadPulse system is live and ready to track Monad validator performance.
