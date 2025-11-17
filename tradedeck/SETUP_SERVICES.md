# Set Up External Services for TradeDeck

We're experiencing a network issue with Prisma binary downloads. While we resolve that, let's set up the external services you'll need. These are all FREE for development/testing.

## 1. Stripe (Payment Processing) - FREE Test Mode

**Why:** Process payments and handle marketplace transactions

1. Go to: https://stripe.com
2. Click "Sign up"
3. Create account (use your email)
4. Once logged in, go to: **Developers → API keys**
5. Copy the following and save them:
   - **Publishable key** (starts with `pk_test_`)
   - **Secret key** (starts with `sk_test_`) - Click "Reveal test key"

**Then:**
6. Go to: **Settings → Connect settings**
7. Turn ON "Connect" platform
8. Fill out basic info (you can use test data)

**Add to .env:**
```
STRIPE_SECRET_KEY="sk_test_YOUR_KEY_HERE"
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_test_YOUR_KEY_HERE"
```

---

## 2. Cloudinary (Image Hosting) - FREE Tier (25GB storage)

**Why:** Upload and host card images

1. Go to: https://cloudinary.com/users/register_free
2. Sign up with email
3. Once logged in, go to **Dashboard**
4. You'll see:
   - **Cloud name**
   - **API Key**
   - **API Secret** (click "Reveal")

**Add to .env:**
```
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME="your_cloud_name"
CLOUDINARY_API_KEY="your_api_key"
CLOUDINARY_API_SECRET="your_api_secret"
```

---

## 3. Pusher (Real-time Messaging) - FREE Tier (100 connections)

**Why:** Real-time chat and notifications

1. Go to: https://dashboard.pusher.com/accounts/sign_up
2. Sign up with email
3. Create a new app:
   - Name: "TradeDeck"
   - Cluster: Choose closest to you (e.g., "us2")
   - Frontend: Select "React"
   - Backend: Select "Node.js"
4. Go to **App Keys** tab
5. Copy:
   - **app_id**
   - **key**
   - **secret**
   - **cluster**

**Add to .env:**
```
PUSHER_APP_ID="your_app_id"
PUSHER_KEY="your_key"
PUSHER_SECRET="your_secret"
PUSHER_CLUSTER="us2"
NEXT_PUBLIC_PUSHER_KEY="your_key"  (same as PUSHER_KEY)
NEXT_PUBLIC_PUSHER_CLUSTER="us2"   (same as PUSHER_CLUSTER)
```

---

## 4. Supabase (PostgreSQL Database) - FREE Tier (500MB)

**Why:** Production-ready PostgreSQL database

1. Go to: https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (recommended) or email
4. Create a new project:
   - Name: "tradedeck"
   - Database Password: Choose a strong password (save it!)
   - Region: Choose closest to you
5. Wait 2-3 minutes for provisioning
6. Go to: **Settings → Database**
7. Scroll to "Connection string" → Select **URI**
8. Copy the connection string (replace `[YOUR-PASSWORD]` with your password)

**Add to .env:**
```
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres"
```

---

## 5. Mailtrap (Email Testing) - FREE

**Why:** Test emails during development (doesn't send real emails)

1. Go to: https://mailtrap.io/register/signup
2. Sign up with email
3. Go to **Email Testing → Inboxes → Demo inbox**
4. Under **SMTP Settings**, select **Nodemailer**
5. Copy the credentials

**Add to .env:**
```
SMTP_HOST="smtp.mailtrap.io"
SMTP_PORT="2525"
SMTP_USER="your_mailtrap_user"
SMTP_PASSWORD="your_mailtrap_password"
```

---

## Optional: OAuth Providers (for Social Login)

### Google OAuth
1. Go to: https://console.cloud.google.com
2. Create a new project
3. Go to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth client ID**
5. Application type: **Web application**
6. Authorized redirect URIs: `http://localhost:3000/api/auth/callback/google`
7. Copy Client ID and Client Secret

```
GOOGLE_CLIENT_ID="your_client_id"
GOOGLE_CLIENT_SECRET="your_client_secret"
```

### GitHub OAuth
1. Go to: https://github.com/settings/developers
2. Click **New OAuth App**
3. Application name: "TradeDeck Local"
4. Homepage URL: `http://localhost:3000`
5. Authorization callback URL: `http://localhost:3000/api/auth/callback/github`
6. Copy Client ID and generate Client Secret

```
GITHUB_CLIENT_ID="your_client_id"
GITHUB_CLIENT_SECRET="your_client_secret"
```

---

## Quick Setup Checklist

Once you have all the credentials:

1. Open `/home/user/cv/tradedeck/.env` in a text editor
2. Replace all the empty `""` values with your actual credentials
3. Save the file

Then run:
```bash
cd /home/user/cv/tradedeck
npm run dev
```

Your app will be at: http://localhost:3000

---

## Help Me Set These Up

If you'd like, you can:
1. Open each service URL in your browser
2. Sign up (they're all free)
3. Copy the credentials
4. Paste them into `.env`

Then tell me when you're done and I'll help test everything!

**Estimated time:** 15-20 minutes for all services
