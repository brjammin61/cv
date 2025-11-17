# 🚀 TradeDeck Launch Guide

Complete guide to launching TradeDeck from code to customers.

## Phase 1: Technical Setup (3-5 Days)

### Day 1: Infrastructure Setup

#### 1. Domain & Hosting
**Get a Domain** ($12/year)
- Go to [Namecheap](https://namecheap.com) or [Google Domains](https://domains.google)
- Buy: `tradedeck.com` or `tradedeck.io`
- Alternative if taken: `gettradedeck.com`, `tradedeck.app`

**Deploy to Vercel** (Free tier → $20/mo Pro)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from tradedeck folder
cd tradedeck
vercel --prod

# Follow prompts:
# - Link to new project
# - Set root directory to "tradedeck"
# - Override settings: None
```

**Or Deploy to Railway** ($5/mo)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Deploy
railway login
railway init
railway up
```

#### 2. Database Setup
**Option A: Supabase** (Free tier → $25/mo)
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Copy connection string from Settings → Database
4. Add to Vercel environment variables:
   ```
   DATABASE_URL="postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres"
   ```

**Option B: Railway PostgreSQL** ($5/mo)
1. Add PostgreSQL to your Railway project
2. Copy DATABASE_URL from variables
3. Paste into Vercel environment variables

**Run Migrations**
```bash
# In your local tradedeck folder
npx prisma migrate deploy
npx prisma db seed  # If you create seed data
```

#### 3. Stripe Setup (Critical!)
**Create Stripe Account**
1. Go to [stripe.com](https://stripe.com)
2. Create account for "Marketplace/Platform"
3. Complete business verification
4. Enable Stripe Connect in Dashboard

**Get API Keys**
- Dashboard → Developers → API keys
- Copy Secret Key (sk_test_... for testing)
- Get Publishable Key (pk_test_...)
- Add to Vercel environment variables

**Setup Webhooks**
1. Dashboard → Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/api/webhooks/stripe`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `account.updated`
   - `transfer.created`
4. Copy webhook signing secret
5. Add to environment variables

#### 4. Third-Party Services

**Cloudinary** (Free tier → $99/mo)
1. [cloudinary.com](https://cloudinary.com)
2. Copy cloud name, API key, API secret
3. Add to environment variables

**Pusher** (Free tier → $49/mo)
1. [pusher.com](https://pusher.com)
2. Create Channels app
3. Copy app ID, key, secret, cluster
4. Add to environment variables

**SendGrid Email** (Free tier → $15/mo)
1. [sendgrid.com](https://sendgrid.com)
2. Create API key
3. Verify sender email/domain
4. Add to environment variables

#### 5. OAuth Providers (Optional but Recommended)

**Google OAuth**
1. [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID
4. Add authorized redirect: `https://yourdomain.com/api/auth/callback/google`
5. Copy client ID & secret

**Facebook Login**
1. [developers.facebook.com](https://developers.facebook.com)
2. Create App → Add Facebook Login
3. Add redirect URI
4. Copy app ID & secret

#### 6. Environment Variables in Vercel
Go to Project Settings → Environment Variables and add all:

```env
DATABASE_URL=postgresql://...
NEXTAUTH_SECRET=[generate with: openssl rand -base64 32]
NEXTAUTH_URL=https://yourdomain.com
STRIPE_SECRET_KEY=sk_live_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
NEXT_PUBLIC_PUSHER_KEY=...
PUSHER_APP_ID=...
PUSHER_SECRET=...
SMTP_HOST=smtp.sendgrid.net
SMTP_PASSWORD=SG.your-api-key
EMAIL_FROM=noreply@yourdomain.com
```

### Day 2-3: Testing & QA

#### Test All Features
- [ ] User signup/login (email + OAuth)
- [ ] Create card listing
- [ ] Upload images
- [ ] Swipe interface works
- [ ] Make test purchase with Stripe test card: `4242 4242 4242 4242`
- [ ] Verify escrow holds payment
- [ ] Send test messages
- [ ] Check emails arrive
- [ ] Test on mobile devices

#### Security Checklist
- [ ] HTTPS enabled (Vercel auto-enables)
- [ ] Environment variables secure
- [ ] Database credentials encrypted
- [ ] API routes protected
- [ ] File upload limits set
- [ ] Rate limiting configured
- [ ] CORS configured properly

### Day 4-5: Launch Preparation

#### Pre-Launch Content
1. **Landing Page SEO**
   - Title: "TradeDeck - The Best Place to Buy & Sell Trading Cards"
   - Meta description
   - Open Graph images

2. **Legal Pages** (Use templates)
   - Terms of Service
   - Privacy Policy
   - Seller Agreement
   - Buyer Protection

3. **Help Center**
   - How to buy
   - How to sell
   - Shipping guide
   - Escrow explained
   - FAQ

4. **Initial Listings**
   - Seed 50-100 cards from your collection or friends
   - High-quality photos
   - Competitive pricing
   - This is CRITICAL - no one uses empty marketplaces

## Phase 2: Legal & Business (Week 1-2)

### Business Structure
**LLC Formation** ($50-500)
- Register in your state (Delaware popular for startups)
- Use [Stripe Atlas](https://stripe.com/atlas) ($500 - handles everything)
- Or DIY with [LegalZoom](https://legalzoom.com) ($100-300)
- Get EIN from IRS (free, instant online)

### Bank Account
- Open business checking account
- Connect to Stripe for payouts
- Separate from personal finances

### Insurance
- General liability insurance ($500-1000/year)
- Cyber liability insurance (recommended)
- Use [Hiscox](https://hiscox.com) or [Next Insurance](https://nextinsurance.com)

### Legal Documents
**Use Templates** (Don't pay lawyers $5k yet!)
- [Termly.io](https://termly.io) - Free privacy policy generator
- [Stripe Terms Templates](https://stripe.com/legal/ssa) - Marketplace terms
- Customize for your needs

### Compliance
- **Payment Processing**: Stripe handles PCI compliance
- **Tax**: Collect sales tax if required (Stripe Tax can help)
- **1099s**: Stripe will handle for sellers over $600/year
- **AML/KYC**: Stripe Connect handles this

## Phase 3: Go-to-Market Strategy (Week 2-3)

### Beta Launch (Week 2)

#### Get Your First 100 Users

**1. Your Network (Days 1-3)**
- Email friends who collect cards
- Post in your social media
- Ask everyone to create account + list 1 card
- Goal: 20 users, 50 listings

**2. Reddit Launch (Days 4-7)**
Post in relevant subreddits:
- r/basketballcards
- r/baseballcards
- r/footballcards
- r/sportscards
- r/TradingCards

**Post Template:**
```
Title: "I built a better way to buy/sell cards (5% fees vs eBay's 13%)"

Body:
Hey everyone! I'm a collector who got tired of eBay's fees and clunky
interface, so I built TradeDeck - a mobile-first marketplace with:

✅ Only 5% fees (vs eBay's 13.25%)
✅ Swipe-to-discover cards (like Tinder)
✅ Built-in escrow protection
✅ No listing fees

It's in beta and 100% free to use. Would love your feedback!
[link to site]
```

**3. Facebook Groups (Days 4-7)**
- Join 10-20 card trading/selling groups
- Introduce yourself
- Share your platform (follow group rules!)
- Offer early access codes

**4. Twitter/X (Days 1-14)**
- Tweet daily about features
- Use hashtags: #sportscards #tradingcards #collecting
- Share user success stories
- Engage with card collecting community

**5. Product Hunt Launch (Day 14)**
- Submit to [Product Hunt](https://producthunt.com)
- Prepare launch day:
  - Get 5-10 friends to upvote
  - Respond to all comments
  - Be online all day
- Can drive 500-1000 visitors if done right

### Growth Tactics (Weeks 3-4)

#### Viral Loops
1. **Referral Program**
   - Give $10 credit for each friend invited
   - Friend gets $10 credit too
   - Track with promo codes

2. **Share Listings**
   - "Share this card" button → social media
   - Beautiful Open Graph previews
   - Drive traffic back to site

3. **Email Marketing**
   - Collect emails pre-launch
   - Weekly digest of new rare cards
   - Personalized recommendations

#### Partnerships
1. **Card Shops**
   - Reach out to local card shops
   - Offer them seller accounts
   - They get online presence, you get inventory

2. **Influencers**
   - Find YouTube/TikTok card collectors
   - Offer free listings
   - Affiliate program (5% of sales they drive)

3. **Card Shows**
   - Set up booth at local card shows
   - Sign up sellers on the spot
   - "List your cards in 60 seconds" demo

#### Content Marketing
1. **Blog Posts**
   - "Complete Guide to Grading Trading Cards"
   - "10 Most Valuable Basketball Cards 2024"
   - "How to Ship Cards Safely"
   - Rank on Google, drive organic traffic

2. **YouTube Channel**
   - "How to Use TradeDeck" tutorials
   - Card reviews
   - Market updates
   - Build authority

## Phase 4: Paid Marketing (Month 2+)

### Start Small ($500-1000/month)

**Facebook/Instagram Ads**
- Target: Card collectors, ages 25-45
- Interests: Sports, collecting, eBay
- Ad creative: Show swipe interface
- Start $20/day, scale what works

**Google Ads**
- Target keywords:
  - "sell basketball cards"
  - "buy graded cards online"
  - "trading card marketplace"
- Start $30/day

**TikTok Ads** (If budget allows)
- Show the swipe interface
- "Found my grail card in 30 seconds"
- Very visual, can go viral

### Key Metrics to Track

**Week 1-4:**
- New signups/day
- Listings created
- Transactions completed
- Average sale price
- User retention

**Target Metrics for Success:**
- Month 1: 100 users, 200 listings, 10 sales
- Month 3: 500 users, 1000 listings, 100 sales
- Month 6: 2000 users, 5000 listings, 500 sales
- Month 12: 10,000 users, 25,000 listings, 3,000 sales

**Revenue Projection:**
- Month 1: ~$500 (10 sales × $100 avg × 5%)
- Month 3: ~$5,000 (100 sales × $100 avg × 5%)
- Month 6: ~$25,000 (500 sales × $100 avg × 5%)
- Month 12: ~$150,000 (3,000 sales × $100 avg × 5%)

## Phase 5: Scale & Optimize (Month 3+)

### Build Network Effects
1. **More buyers = more sellers**
   - Focus on buyer acquisition first
   - Sellers follow the buyers

2. **More inventory = more buyers**
   - Recruit power sellers
   - Offer bulk upload tools
   - Featured seller program

### Product Improvements
Based on user feedback:
- AI card scanner (high priority!)
- Price history charts
- Saved searches with alerts
- Mobile apps (iOS/Android)
- Advanced analytics for sellers

### Fundraising (If desired)
- At 1,000 active users: Angel investors ($100k-500k)
- At 10,000 users: Seed round ($1M-3M)
- At 100,000 users: Series A ($5M-15M)

## Quick Launch Checklist

### Week 1: Deploy
- [ ] Domain purchased
- [ ] Vercel deployment complete
- [ ] Database live
- [ ] All APIs configured
- [ ] SSL certificate active
- [ ] Test purchase successful

### Week 2: Prepare
- [ ] Legal pages written
- [ ] Help center created
- [ ] 50+ cards listed
- [ ] Email template tested
- [ ] Social media accounts created
- [ ] Analytics setup (Google Analytics)

### Week 3: Launch
- [ ] Beta announcement to friends
- [ ] Reddit posts scheduled
- [ ] Facebook group outreach
- [ ] Product Hunt launch prep
- [ ] Press release written
- [ ] Support system ready

### Week 4: Grow
- [ ] Daily engagement on social
- [ ] Respond to all feedback
- [ ] Fix reported bugs
- [ ] Add requested features
- [ ] Start paid marketing
- [ ] Track metrics daily

## Budget Breakdown

### Minimum Budget ($200/mo):
- Domain: $12/year ($1/mo)
- Vercel Hobby: Free (upgrade later)
- Supabase: Free tier
- Stripe: Pay-as-you-go
- Cloudinary: Free tier
- Pusher: Free tier
- SendGrid: Free tier
- **Total: ~$1/mo to start!**

### Growth Budget ($500/mo):
- Domain: $1/mo
- Vercel Pro: $20/mo
- Supabase Pro: $25/mo
- Cloudinary: $99/mo
- Pusher: $49/mo
- SendGrid: $15/mo
- Ads: $300/mo
- **Total: ~$509/mo**

### Scale Budget ($2,000/mo):
- All services: $500/mo
- Ads: $1,500/mo
- **Total: ~$2,000/mo**

## Success Tips

1. **Start Small**: Launch with 50-100 cards, not 0
2. **Network Effects**: Focus on one sport/niche first
3. **Mobile First**: Most collectors use phones
4. **Trust & Safety**: Respond fast to disputes
5. **Community**: Build Discord/Facebook group
6. **Listen**: Users will tell you what to build
7. **Iterate Fast**: Ship weekly improvements
8. **Celebrate Wins**: Share success stories

## Resources

### Communities
- r/startups - General startup advice
- r/SaaS - SaaS-specific
- Indie Hackers - Solo founder community

### Learning
- [How to Start a Startup (YC)](https://youtube.com/playlist?list=PLQ-uHSnFig5MiLRb-l6yiCBGyqfVyVf17)
- [The Mom Test](http://momtestbook.com) - Customer interviews
- [Traction](https://tractionbook.com) - Marketing channels

### Tools
- [Stripe Atlas](https://stripe.com/atlas) - Company formation
- [Plausible](https://plausible.io) - Privacy-friendly analytics
- [Crisp](https://crisp.chat) - Customer support chat
- [Mailchimp](https://mailchimp.com) - Email marketing

## Timeline Summary

- **Week 1**: Deploy to production
- **Week 2**: Seed content, legal prep
- **Week 3**: Beta launch to network
- **Week 4**: Public launch, Reddit/PH
- **Month 2**: Paid marketing begins
- **Month 3**: 500+ users, break even
- **Month 6**: 2,000+ users, profitable
- **Month 12**: 10,000+ users, scaling

---

**You can literally launch this weekend!** 🚀

The code is production-ready. Just configure the services, deploy, and start acquiring users.

**First Goal: Get 10 real transactions in 30 days**

Good luck! 🎉
