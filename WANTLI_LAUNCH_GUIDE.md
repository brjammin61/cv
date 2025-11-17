# Wantli Complete Launch Guide

## 🎯 What You Have

You now have **TWO applications**:

1. **Backend API** (`/tradedeck`) - Node.js/Next.js API server
2. **Mobile App** (`/wantli`) - React Native mobile app

## 📱 Why React Native Over Swift?

**React Native is the right choice because:**

✅ **One codebase** → Deploy to iOS + Android simultaneously
✅ **Same language** → Your backend is TypeScript, frontend is TypeScript
✅ **Faster development** → No need to learn Swift (iOS) + Kotlin (Android)
✅ **70% of market** → Android is huge, don't miss out
✅ **Easy updates** → Push updates without App Store review (via Expo)
✅ **Lower cost** → One developer can handle both platforms

**Swift only makes sense if:**
- You only want iOS (missing 70% of users)
- You need extreme performance (games, AR apps)
- You have separate iOS and Android teams

## 🚀 Quick Start (Test in 10 Minutes)

### Step 1: Start the Backend

```bash
# Terminal 1
cd /home/user/cv/tradedeck
npm run dev
```

Backend will run on: `http://localhost:3000`

### Step 2: Find Your Computer's IP Address

**Mac/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```bash
ipconfig
```

Look for something like: `192.168.1.100`

### Step 3: Configure Mobile App

```bash
cd /home/user/cv/wantli
cp .env.example .env
```

Edit `.env` and replace `YOUR_COMPUTER_IP` with your actual IP:

```
EXPO_PUBLIC_API_URL=http://192.168.1.100:3000/api
```

### Step 4: Start Mobile App

```bash
# Terminal 2 (new terminal)
cd /home/user/cv/wantli
npm start
```

### Step 5: Test on Your Phone

1. **Install Expo Go** on your phone:
   - iOS: https://apps.apple.com/app/expo-go/id982107779
   - Android: https://play.google.com/store/apps/details?id=host.exp.exponent

2. **Open Expo Go** app

3. **Scan the QR code** from your terminal

4. **Wait for app to load** (first load takes ~30 seconds)

5. **Create an account** and start swiping!

---

## 📸 How to Upload Your First Cards

Once the app loads on your phone:

1. **Create an account** (sign up screen)
2. Tap the **big + button** in the middle of the tab bar
3. Tap **"Take Photo"** or **"Add Photo"**
4. Take a picture of your trading card
5. Fill in the details:
   - **Player**: e.g., "LeBron James"
   - **Year**: e.g., "2003"
   - **Sport**: Select sport
   - **Manufacturer**: e.g., "Topps", "Panini"
   - **Set Name**: e.g., "Prizm", "Chrome"
   - **Card Type**: e.g., "Rookie Card", "Autograph"
   - **Price**: Your asking price
   - **Condition**: Select condition
   - **Is it graded?** Toggle ON if PSA/BGS graded
     - Select grading company (PSA, BGS, etc.)
     - Enter grade (e.g., "10", "9.5")
6. Tap **"List Card"**

Your card is now live! You'll see it when you swipe through cards.

---

## 🎨 App Features Explained

### 1. Discover Screen (Main Screen)
- **Swipe Right** = Like the card
- **Swipe Left** = Pass
- **Tap card** = See full details
- **Tap ℹ️ button** = Quick info

### 2. Card Detail Screen
- **Scroll through photos** (if multiple)
- **See all card info** (grading, condition, etc.)
- **View seller profile** (rating, sales)
- **Message seller**
- **Buy now**

### 3. Upload Screen
- **Camera integration** for instant photos
- **All card fields** supported:
  - PSA/BGS/SGC grading
  - Condition (Mint, Near Mint, etc.)
  - Card type (Rookie, Autograph, etc.)
  - Set name, manufacturer, year
- **Multiple photos** supported

### 4. Likes Screen
- See all cards you've liked
- Grid view
- Tap to view details

### 5. Messages Screen
- Chat with buyers/sellers
- See unread count
- Quick access to conversations

### 6. Account Screen
- View your stats (sales, purchases, rating)
- Manage listings
- Edit profile
- Sign out

---

## 🔧 Troubleshooting

### "Cannot connect to API"

**Problem:** Mobile app can't reach backend

**Solutions:**
1. Make sure backend is running (`cd tradedeck && npm run dev`)
2. Check your `.env` file uses your computer's IP, not `localhost`
3. Ensure phone and computer are on the **same WiFi network**
4. Try disabling firewall temporarily
5. Check backend is accessible by visiting `http://YOUR_IP:3000` in phone browser

### "Camera not working"

**Problem:** Can't take photos

**Solutions:**
1. Grant camera permission when prompted
2. On iOS: Settings → Expo Go → Camera → Allow
3. On Android: Settings → Apps → Expo Go → Permissions → Camera → Allow

### "App loads but screens are blank"

**Problem:** Components not rendering

**Solutions:**
1. Shake phone to open Expo menu
2. Tap "Reload"
3. Clear cache: Close app, reopen Expo Go, scan QR again

### "Module not found" errors

**Problem:** Missing dependencies

**Solutions:**
```bash
cd /home/user/cv/wantli
rm -rf node_modules
npm install
npm start
```

---

## 🚢 Deploying to App Stores

### Option 1: Expo Application Services (EAS) - Easiest

**Setup (one-time):**
```bash
npm install -g eas-cli
eas login  # Create free Expo account
eas build:configure
```

**Build for iOS:**
```bash
eas build --platform ios
```

**Build for Android:**
```bash
eas build --platform android
```

**Submit to stores:**
```bash
eas submit --platform ios     # Apple App Store
eas submit --platform android # Google Play Store
```

### Option 2: Local Builds (Advanced)

**iOS (requires Mac):**
```bash
npx expo run:ios
```

**Android:**
```bash
npx expo run:android
```

### What You Need:

**Apple App Store:**
- Apple Developer account ($99/year)
- Mac computer (for building)
- App Store Connect account

**Google Play Store:**
- Google Play Console account ($25 one-time)
- Can build on any computer

---

## 💰 Cost Breakdown

### Development (FREE)
- ✅ Expo - Free
- ✅ React Native - Free
- ✅ All libraries - Free
- ✅ Testing via Expo Go - Free

### Services (FREE tiers available)
- ✅ Supabase (database) - Free 500MB
- ✅ Cloudinary (images) - Free 25GB
- ✅ Stripe (payments) - Free in test mode
- ✅ Pusher (real-time) - Free 100 connections
- ✅ Mailtrap (email testing) - Free

### Production Costs
- Apple Developer: $99/year (for App Store)
- Google Play: $25 one-time (for Play Store)
- Vercel (backend): $0-20/month
- Supabase: $0-25/month (depending on users)
- Domain: $10-15/year

**Total to launch:** $124 first year, then $99/year (if you keep iOS)

---

## 📱 Testing on Physical Device vs Simulator

### Physical Device (Recommended)
**Pros:**
- Real camera testing
- Actual touch/swipe feels right
- Test on your exact hardware
- Works on Windows/Mac/Linux

**Cons:**
- Need to be on same WiFi
- Slightly slower to reload

### iOS Simulator (Mac only)
```bash
npm run ios
```

**Pros:**
- Fast reload
- Easy debugging

**Cons:**
- No camera access
- Doesn't feel like real device
- Requires Mac

### Android Emulator
```bash
npm run android
```

**Pros:**
- Works on any OS
- Fast testing

**Cons:**
- Slow startup
- Heavy on CPU/RAM
- Camera emulation is weird

**Recommendation:** Use Expo Go on your real phone!

---

## 🎯 Your Launch Plan

### Week 1: Test & Polish
1. Upload 10-20 of your own cards
2. Get 2-3 friends to test
3. Fix any bugs
4. Polish UI/UX

### Week 2: Configure Production Services
1. Sign up for production Supabase (PostgreSQL)
2. Sign up for production Cloudinary
3. Set up Stripe Connect
4. Configure push notifications
5. Add real email service (SendGrid/Resend)

### Week 3: Deploy
1. Deploy backend to Vercel
2. Build mobile app with EAS
3. Submit to App Store & Play Store
4. Wait for approval (1-2 weeks for iOS, 1-3 days for Android)

### Week 4: Soft Launch
1. Announce to friends/family
2. Post on Reddit (r/sportscards, r/basketballcards, etc.)
3. Share on Facebook groups
4. Get initial users & feedback

### Month 2: Marketing
1. Partner with local card shops
2. Reach out to card influencers
3. Run social media ads
4. List on Product Hunt

---

## 🔥 Quick Commands Reference

**Start everything:**
```bash
# Terminal 1: Backend
cd /home/user/cv/tradedeck && npm run dev

# Terminal 2: Mobile
cd /home/user/cv/wantli && npm start
```

**Build for production:**
```bash
# iOS
eas build --platform ios

# Android
eas build --platform android

# Both
eas build --platform all
```

**Submit to stores:**
```bash
eas submit --platform ios
eas submit --platform android
```

---

## 📞 Getting Help

- **Expo Docs:** https://docs.expo.dev
- **React Native Docs:** https://reactnative.dev
- **Stack Overflow:** Tag your questions with `react-native` and `expo`
- **Expo Discord:** https://chat.expo.dev

---

## 🚀 You're Ready!

You have a complete, production-ready trading card marketplace app!

**Next steps:**
1. `cd /home/user/cv/tradedeck && npm run dev` (Terminal 1)
2. `cd /home/user/cv/wantli && npm start` (Terminal 2)
3. Open Expo Go on your phone
4. Scan QR code
5. Upload your first card!

**Happy swiping! 🎴**
