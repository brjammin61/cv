# Wantli - Trading Card Marketplace Mobile App

> Swipe. Collect. Trade.

**Wantli** is a modern React Native mobile app for buying and selling trading cards with a Tinder-style swipe interface. Built for iOS and Android.

## 🚀 Features

- **Tinder-Style Swiping** - Discover cards with intuitive swipe gestures
- **Camera Integration** - Take photos of your cards to list them instantly
- **Detailed Card Views** - Scrollable card details with all specifications
- **PSA/BGS Grading Support** - Full grading company and grade tracking
- **Real-time Messaging** - Chat with buyers and sellers
- **Secure Payments** - Stripe integration for safe transactions
- **Push Notifications** - Get notified about offers, messages, and sales
- **Beautiful UI** - Modern, gradient-filled interface

## 📱 Screenshots

*Coming soon...*

## 🛠 Tech Stack

- **React Native** via Expo
- **TypeScript** for type safety
- **React Navigation** for routing
- **Expo Camera** for card photos
- **AsyncStorage** for local data
- **Axios** for API calls
- **Framer Motion** for animations (via React Native Reanimated)

## 📋 Prerequisites

- Node.js 16+ installed
- Expo Go app on your phone ([iOS](https://apps.apple.com/app/expo-go/id982107779) | [Android](https://play.google.com/store/apps/details?id=host.exp.exponent))
- Backend API running (from `/tradedeck` folder)

## 🏃 Quick Start

### 1. Install Dependencies

```bash
cd wantli
npm install
```

### 2. Configure Environment Variables

Create `.env` file:

```bash
EXPO_PUBLIC_API_URL=http://YOUR_COMPUTER_IP:3000/api
EXPO_PUBLIC_CLOUDINARY_CLOUD_NAME=your_cloud_name
EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
EXPO_PUBLIC_PUSHER_KEY=your_pusher_key
EXPO_PUBLIC_PUSHER_CLUSTER=us2
```

**Important:** Replace `YOUR_COMPUTER_IP` with your actual local IP address (find with `ipconfig` on Windows or `ifconfig` on Mac/Linux). Don't use `localhost`!

### 3. Start the App

```bash
npm start
```

### 4. Open on Your Phone

1. Open **Expo Go** app on your phone
2. Scan the QR code from your terminal
3. Wait for the app to load
4. Start swiping!

## 📸 Card Upload Flow

1. Tap the **+** button in the tab bar
2. Take a photo or select from gallery
3. Fill in card details:
   - Player name
   - Year
   - Sport
   - Manufacturer (Topps, Panini, etc.)
   - Set name (Prizm, Chrome, etc.)
   - Card type (Rookie, Autograph, etc.)
   - Price
   - Condition
   - Grading info (PSA, BGS, grade)
4. Tap **List Card**

## 🎨 App Structure

```
wantli/
├── src/
│   ├── screens/           # All app screens
│   │   ├── AuthScreen.tsx
│   │   ├── DiscoverScreen.tsx
│   │   ├── CardDetailScreen.tsx
│   │   ├── UploadCardScreen.tsx
│   │   ├── LikesScreen.tsx
│   │   ├── MessagesScreen.tsx
│   │   └── AccountScreen.tsx
│   ├── components/        # Reusable components
│   ├── services/          # API calls
│   │   └── api.ts
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── utils/            # Helper functions
│   │   └── auth.ts
│   └── config/           # App configuration
│       └── api.ts
├── App.tsx               # Main app file with navigation
├── app.json             # Expo configuration
└── package.json         # Dependencies

```

## 🔑 API Endpoints Used

The app connects to these backend endpoints (from `/tradedeck`):

- `POST /api/auth/signup` - Create account
- `POST /api/auth/signin` - Login
- `GET /api/auth/me` - Get current user
- `GET /api/cards` - Get cards for discovery
- `POST /api/cards` - Create new listing
- `GET /api/cards/:id` - Get card details
- `POST /api/cards/:id/like` - Like a card
- `GET /api/messages/conversations` - Get chats
- `POST /api/messages` - Send message
- `POST /api/offers` - Make an offer
- `POST /api/transactions` - Create purchase

## 📦 Building for Production

### iOS (requires Mac)

```bash
npx eas build --platform ios
```

### Android

```bash
npx eas build --platform android
```

### Both

```bash
npx eas build --platform all
```

## 🚀 Publishing to App Stores

### Apple App Store

1. Sign up for [Apple Developer Program]( https://developer.apple.com/) ($99/year)
2. Build iOS app: `npx eas build --platform ios`
3. Submit via Expo: `npx eas submit --platform ios`

### Google Play Store

1. Sign up for [Google Play Console](https://play.google.com/console) ($25 one-time)
2. Build Android app: `npx eas build --platform android`
3. Submit via Expo: `npx eas submit --platform android`

## 🔧 Customization

### Change Brand Colors

Edit colors in each screen's StyleSheet:

```typescript
// Change from purple (#6366F1) to your brand color
backgroundColor: '#YOUR_COLOR'
```

### Change App Name

Edit `app.json`:

```json
{
  "expo": {
    "name": "Your App Name",
    ...
  }
}
```

### Change Bundle ID

Edit `app.json`:

```json
{
  "expo": {
    "ios": {
      "bundleIdentifier": "com.yourcompany.yourapp"
    },
    "android": {
      "package": "com.yourcompany.yourapp"
    }
  }
}
```

## 🐛 Troubleshooting

### App won't connect to API

- Make sure backend is running (`cd tradedeck && npm run dev`)
- Check that `EXPO_PUBLIC_API_URL` uses your computer's IP, not `localhost`
- Ensure phone and computer are on the same WiFi network

### Camera not working

- Grant camera permissions when prompted
- Check `app.json` has camera permissions configured

### Build errors

```bash
# Clear cache and reinstall
rm -rf node_modules
npm install
npx expo start --clear
```

## 📝 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `EXPO_PUBLIC_API_URL` | Backend API URL | `http://192.168.1.100:3000/api` |
| `EXPO_PUBLIC_CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | `wantli-cards` |
| `EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe public key | `pk_test_...` |
| `EXPO_PUBLIC_PUSHER_KEY` | Pusher app key | `your_key` |
| `EXPO_PUBLIC_PUSHER_CLUSTER` | Pusher cluster | `us2` |

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the ISC License.

## 🙏 Acknowledgments

- Expo team for amazing mobile development tools
- React Native community
- Trading card collectors worldwide

---

**Ready to launch?** Start with `npm start` and scan the QR code with Expo Go!

For backend setup, see `/tradedeck/README.md`
