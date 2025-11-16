export interface Card {
  id: string;
  title: string;
  player: string;
  year: number;
  sport: 'basketball' | 'baseball' | 'football' | 'soccer' | 'other';
  set: string;
  cardNumber: string;
  condition: 'mint' | 'near-mint' | 'excellent' | 'good' | 'fair' | 'poor';
  graded: boolean;
  grade?: number;
  gradingCompany?: 'PSA' | 'BGS' | 'SGC' | 'CGC';
  price: number;
  imageUrl: string;
  images?: string[];
  sellerId: string;
  sellerName: string;
  sellerRating: number;
  description?: string;
  category: string;
  era: string;
  featured?: boolean;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  rating: number;
  totalSales: number;
  totalPurchases: number;
  memberSince: Date;
}

export interface Message {
  id: string;
  senderId: string;
  receiverId: string;
  cardId?: string;
  content: string;
  timestamp: Date;
  read: boolean;
}

export interface Transaction {
  id: string;
  cardId: string;
  buyerId: string;
  sellerId: string;
  price: number;
  status: 'pending' | 'paid' | 'shipped' | 'delivered' | 'completed' | 'disputed';
  escrowStatus: 'held' | 'released' | 'refunded';
  trackingNumber?: string;
  authenticationRequired: boolean;
  authenticationStatus?: 'pending' | 'approved' | 'rejected';
  createdAt: Date;
  updatedAt: Date;
}

export interface Filter {
  sport?: string;
  player?: string;
  era?: string;
  category?: string;
  graded?: boolean;
  minPrice?: number;
  maxPrice?: number;
  condition?: string[];
}

export interface Offer {
  id: string;
  cardId: string;
  buyerId: string;
  amount: number;
  status: 'pending' | 'accepted' | 'rejected' | 'countered';
  counterAmount?: number;
  createdAt: Date;
}
