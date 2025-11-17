// API Configuration for Wantli

// For development: Use your computer's local IP address
// For production: Use your deployed backend URL
export const API_BASE_URL = __DEV__
  ? 'http://localhost:3000/api' // Change to your computer's IP if testing on physical device
  : 'https://api.wantli.com/api';

export const CLOUDINARY_UPLOAD_PRESET = 'wantli_cards';
export const CLOUDINARY_CLOUD_NAME = process.env.EXPO_PUBLIC_CLOUDINARY_CLOUD_NAME || '';

export const STRIPE_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY || '';
export const PUSHER_KEY = process.env.EXPO_PUBLIC_PUSHER_KEY || '';
export const PUSHER_CLUSTER = process.env.EXPO_PUBLIC_PUSHER_CLUSTER || 'us2';
