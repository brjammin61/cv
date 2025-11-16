# 🚀 TradeDeck Production Setup Guide

Complete guide to deploying TradeDeck to production.

## 📋 Prerequisites

- Node.js 18+ installed
- PostgreSQL database (recommended: Supabase, Railway, or Neon)
- Stripe account (for payments)
- Cloudinary account (for image uploads)
- Pusher account (for real-time features)
- Email service (SendGrid, Resend, or AWS SES)

## 1. Database Setup

### Option A: Supabase (Recommended)

1. Create a project at [supabase.com](https://supabase.com)
2. Get your connection string from Settings → Database
3. Add to `.env`:
```env
DATABASE_URL="postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"
```

### Option B: Railway

1. Create project at [railway.app](https://railway.app)
2. Add PostgreSQL service
3. Copy DATABASE_URL from variables

### Option C: Local PostgreSQL

```bash
# Install PostgreSQL
brew install postgresql # macOS
sudo apt install postgresql # Ubuntu

# Create database
createdb tradedeck

# Add to .env
DATABASE_URL="postgresql://localhost:5432/tradedeck"
```

### Run Migrations

```bash
npx prisma migrate deploy
npx prisma generate
```

## 2. Stripe Setup

### Create Stripe Account

1. Sign up at [stripe.com](https://stripe.com)
2. Get API keys from Dashboard → Developers → API keys
3. Enable Stripe Connect for marketplace functionality

### Configure Webhooks

1. Go to Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/api/webhooks/stripe`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `account.updated`
   - `transfer.created`
4. Copy webhook secret

### Environment Variables

```env
STRIPE_SECRET_KEY="sk_live_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
STRIPE_PLATFORM_FEE_PERCENT="5"
```

## 3. Authentication Setup

### NextAuth Configuration

```env
NEXTAUTH_SECRET="generated-secret-key"
NEXTAUTH_URL="https://yourdomain.com"
```

Generate secret:
```bash
openssl rand -base64 32
```

### OAuth Providers

#### Google
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID
4. Add authorized redirect: `https://yourdomain.com/api/auth/callback/google`

```env
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
```

#### Facebook
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create App → Add Facebook Login
3. Add redirect URI: `https://yourdomain.com/api/auth/callback/facebook`

```env
FACEBOOK_CLIENT_ID="your-app-id"
FACEBOOK_CLIENT_SECRET="your-app-secret"
```

#### GitHub
1. Go to Settings → Developer settings → OAuth Apps
2. Create new OAuth App
3. Add callback URL: `https://yourdomain.com/api/auth/callback/github`

```env
GITHUB_CLIENT_ID="your-client-id"
GITHUB_CLIENT_SECRET="your-client-secret"
```

## 4. Cloudinary Setup

1. Sign up at [cloudinary.com](https://cloudinary.com)
2. Go to Dashboard
3. Copy credentials:

```env
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME="your-cloud-name"
CLOUDINARY_API_KEY="your-api-key"
CLOUDINARY_API_SECRET="your-api-secret"
```

## 5. Pusher Setup

1. Sign up at [pusher.com](https://pusher.com)
2. Create Channels app
3. Get credentials:

```env
NEXT_PUBLIC_PUSHER_KEY="your-key"
NEXT_PUBLIC_PUSHER_CLUSTER="us2"
PUSHER_APP_ID="your-app-id"
PUSHER_SECRET="your-secret"
```

## 6. Email Setup

### Option A: SendGrid

```env
SMTP_HOST="smtp.sendgrid.net"
SMTP_PORT="587"
SMTP_USER="apikey"
SMTP_PASSWORD="SG.your-api-key"
EMAIL_FROM="noreply@yourdomain.com"
```

### Option B: Resend

```env
SMTP_HOST="smtp.resend.com"
SMTP_PORT="587"
SMTP_USER="resend"
SMTP_PASSWORD="re_your-api-key"
EMAIL_FROM="noreply@yourdomain.com"
```

## 7. Deployment

### Option A: Vercel (Recommended)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel --prod
```

3. Add environment variables in Vercel dashboard
4. Enable PostgreSQL connection pooling in Vercel

### Option B: Railway

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Deploy:
```bash
railway login
railway init
railway up
```

### Option C: AWS / DigitalOcean

1. Build the app:
```bash
npm run build
```

2. Start with PM2:
```bash
npm i -g pm2
pm2 start npm --name "tradedeck" -- start
pm2 save
```

## 8. Domain & SSL

### Vercel
- Automatic SSL with Let's Encrypt
- Add custom domain in project settings

### Manual Setup
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

## 9. Production Checklist

- [ ] Database deployed and migrated
- [ ] All environment variables set
- [ ] Stripe webhooks configured
- [ ] OAuth providers configured
- [ ] Email sending working
- [ ] Cloudinary images uploading
- [ ] Pusher real-time working
- [ ] SSL certificate installed
- [ ] Domain configured
- [ ] Error tracking setup (Sentry)
- [ ] Analytics setup (Google Analytics)
- [ ] Monitoring setup (Uptime Robot)
- [ ] Backup strategy configured

## 10. Post-Deployment

### Verify Everything Works

1. **Test Authentication**
   - Sign up with email
   - Login with Google/Facebook/GitHub
   - Password reset

2. **Test Listings**
   - Create card listing
   - Upload images
   - Edit/delete listing

3. **Test Transactions**
   - Make test purchase
   - Verify escrow
   - Test refund

4. **Test Real-time**
   - Send message
   - Receive notification
   - Check Pusher dashboard

5. **Test Emails**
   - Welcome email
   - Purchase confirmation
   - Sale notification

### Monitoring

```bash
# View logs (Vercel)
vercel logs

# View logs (PM2)
pm2 logs tradedeck

# Check health
curl https://yourdomain.com/api/health
```

## 11. Scaling

### Database
- Enable connection pooling
- Add read replicas for heavy traffic
- Set up automated backups

### CDN
- Vercel automatically uses CDN
- For manual: CloudFlare or AWS CloudFront

### Caching
```bash
# Install Redis
npm install @upstash/redis @upstash/ratelimit

# Add to .env
UPSTASH_REDIS_REST_URL="your-url"
UPSTASH_REDIS_REST_TOKEN="your-token"
```

## 12. Security

- [x] HTTPS enabled
- [x] CSRF protection
- [x] Rate limiting
- [x] SQL injection protection (Prisma)
- [x] XSS protection
- [ ] DDoS protection (CloudFlare)
- [ ] Regular security audits

## 13. Maintenance

### Database Backups
```bash
# Automated backups (daily)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Updates
```bash
# Update dependencies monthly
npm update
npx npm-check-updates -u
npm install
```

## 🆘 Troubleshooting

### Database Connection Issues
```bash
# Test connection
npx prisma db push
```

### Stripe Webhooks Not Working
- Check webhook endpoint URL
- Verify webhook secret
- Check Stripe dashboard logs

### Emails Not Sending
- Verify SMTP credentials
- Check spam folder
- Review email logs

### Real-time Not Working
- Check Pusher app status
- Verify credentials
- Test with Pusher debug console

## 📞 Support

- **Documentation**: [docs.tradedeck.com](https://docs.tradedeck.com)
- **Issues**: [github.com/tradedeck/issues](https://github.com)
- **Email**: support@tradedeck.com

---

**Estimated Setup Time**: 2-3 hours for first deployment

**Congratulations!** 🎉 Your production TradeDeck instance is ready!
