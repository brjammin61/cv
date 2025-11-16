# MonadPulse Quick Start (5 Minutes)

Get MonadPulse running on a VPS in 5 commands.

## 1. Get a VPS

- Go to digitalocean.com (or AWS, Linode, Vultr)
- Create Ubuntu 22.04 droplet ($12/month, 2GB RAM)
- Note the IP address
- SSH in: `ssh root@YOUR_IP`

## 2. Setup Server (3 minutes)

```bash
curl -o setup.sh https://raw.githubusercontent.com/brjammin61/cv/claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE/monadpulse_backend/scripts/setup_server.sh && chmod +x setup.sh && ./setup.sh
```

## 3. Deploy MonadPulse (5 minutes)

```bash
curl -o deploy.sh https://raw.githubusercontent.com/brjammin61/cv/claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE/monadpulse_backend/scripts/deploy.sh && chmod +x deploy.sh && ./deploy.sh
```

## 4. Test It

Open in your browser:
```
http://YOUR_VPS_IP
```

You should see the MonadPulse dashboard with live validator data!

## 5. Add SSL (Optional, 1 minute)

If you have a domain pointing to your VPS:

```bash
certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

Done! Your system is live at `https://yourdomain.com`

---

## What You Just Deployed

- **Backend API**: FastAPI server on port 8000
- **Frontend**: React dashboard on port 80/443
- **Database**: PostgreSQL with TimescaleDB
- **Ingestor**: Auto-updates validator data every 2 minutes
- **Reverse Proxy**: Nginx with SSL support

## Next Steps

1. Test all features in the dashboard
2. When Monad mainnet launches Nov 24, integrate the SDK
3. Share your dashboard with the Monad community
4. Start building your reputation before launching Omega Engine

## Monitoring

View live backend logs:
```bash
cd /opt/monadpulse/monadpulse_backend
docker-compose logs -f
```

Restart services:
```bash
docker-compose restart
```

## Troubleshooting

If something doesn't work:
1. Check `docker ps` - all 3 containers should be running
2. Check `systemctl status nginx` - should be active
3. Check logs: `docker-compose logs api`

For detailed help, see [DEPLOYMENT.md](./DEPLOYMENT.md)
