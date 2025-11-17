# TradeDeck Quick Start Guide

Follow these steps in order to get TradeDeck running locally and ready for deployment.

## Step 1: Install Dependencies

```bash
cd /home/user/cv/tradedeck
npm install
```

This installs all required packages including Next.js, Prisma, Stripe, etc.

## Step 2: Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Now you need to edit the `.env` file. Here's what you need:

### Required Services (Sign up for free tiers):

1. **Database (Supabase - Free)**
   - Go to: https://supabase.com
   - Create new project
   - Get connection string from Settings → Database
   - Set `DATABASE_URL=postgresql://...`

2. **Stripe (Free for testing)**
   - Go to: https://stripe.com
   - Get API keys from Developers → API keys
   - Set `STRIPE_SECRET_KEY=sk_test_...`
   - Set `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...`

3. **Cloudinary (Free tier)**
   - Go to: https://cloudinary.com
   - Get credentials from Dashboard
   - Set `CLOUDINARY_CLOUD_NAME=...`
   - Set `CLOUDINARY_API_KEY=...`
   - Set `CLOUDINARY_API_SECRET=...`

4. **Pusher (Free tier)**
   - Go to: https://pusher.com
   - Create new app
   - Set `PUSHER_APP_ID=...`
   - Set `PUSHER_KEY=...`
   - Set `PUSHER_SECRET=...`
   - Set `PUSHER_CLUSTER=us2` (or your cluster)
   - Set `NEXT_PUBLIC_PUSHER_KEY=...` (same as PUSHER_KEY)
   - Set `NEXT_PUBLIC_PUSHER_CLUSTER=us2` (same as PUSHER_CLUSTER)

5. **Email (Optional - use Mailtrap for testing)**
   - Go to: https://mailtrap.io (free)
   - Get SMTP credentials
   - Set `EMAIL_HOST=smtp.mailtrap.io`
   - Set `EMAIL_PORT=2525`
   - Set `EMAIL_USER=...`
   - Set `EMAIL_PASSWORD=...`
   - Set `EMAIL_FROM=noreply@tradedeck.com`

6. **NextAuth**
   - Set `NEXTAUTH_URL=http://localhost:3000`
   - Run: `openssl rand -base64 32` to generate a secret
   - Set `NEXTAUTH_SECRET=<generated-secret>`

### Optional OAuth Providers:

**Google OAuth** (optional):
- Go to: https://console.cloud.google.com
- Create OAuth credentials
- Set `GOOGLE_CLIENT_ID=...`
- Set `GOOGLE_CLIENT_SECRET=...`

**Facebook OAuth** (optional):
- Go to: https://developers.facebook.com
- Create app
- Set `FACEBOOK_CLIENT_ID=...`
- Set `FACEBOOK_CLIENT_SECRET=...`

**GitHub OAuth** (optional):
- Go to: https://github.com/settings/developers
- Create OAuth app
- Set `GITHUB_CLIENT_ID=...`
- Set `GITHUB_CLIENT_SECRET=...`

## Step 3: Set Up Database

```bash
# Generate Prisma client
npx prisma generate

# Push database schema (creates tables)
npx prisma db push

# Seed database with demo data
npm run seed
```

This creates:
- Admin user: `admin@tradedeck.com` / `admin123`
- Demo seller: `seller@tradedeck.com` / `seller123`
- 6 sample trading cards

## Step 4: Run Development Server

```bash
npm run dev
```

Your app will be running at: http://localhost:3000

## Step 5: Test the Application

1. Visit http://localhost:3000
2. Sign in as admin: `admin@tradedeck.com` / `admin123`
3. Visit http://localhost:3000/admin to see admin dashboard
4. Visit http://localhost:3000/launch-checklist to see launch roadmap
5. Browse sample cards and test the swipe interface

## Step 6: Deploy to Production (When Ready)

```bash
# Run the automated deployment script
./scripts/deploy.sh
```

This will:
- Check environment variables
- Generate secrets
- Run migrations
- Deploy to Vercel

---

## Quick Reference

- **Local app**: http://localhost:3000
- **Admin dashboard**: http://localhost:3000/admin
- **Launch checklist**: http://localhost:3000/launch-checklist
- **Help center**: http://localhost:3000/help
- **Prisma Studio** (view database): `npx prisma studio`

## Minimal Setup (Just to See It Running)

If you just want to see the UI without full functionality:

1. Install dependencies: `npm install`
2. Create `.env` with just: `NEXTAUTH_SECRET="test-secret-for-development-only"`
3. Comment out database calls in code temporarily
4. Run: `npm run dev`

This won't have working auth or database, but you'll see the UI/UX.

## Troubleshooting

**Port already in use?**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

**Database connection error?**
- Check `DATABASE_URL` is correct
- Make sure Supabase project is active

**Prisma errors?**
```bash
# Reset Prisma
npx prisma generate
npx prisma db push --force-reset
npm run seed
```

## Need Help?

Check `/tradedeck/PRODUCTION_SETUP.md` for detailed production deployment guide.
