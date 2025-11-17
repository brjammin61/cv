export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  bio?: string;
  location?: string;
  rating: number;
  totalSales: number;
  totalPurchases: number;
  createdAt: string;
}

export interface Card {
  id: string;
  title: string;
  player: string;
  year: number;
  sport: 'BASKETBALL' | 'BASEBALL' | 'FOOTBALL' | 'SOCCER' | 'HOCKEY' | 'OTHER';
  cardType: string; // e.g., "Rookie Card", "Autograph", "Jersey Card"
  manufacturer: string; // e.g., "Topps", "Panini", "Upper Deck"
  setName?: string; // e.g., "Prizm", "Topps Chrome"
  cardNumber?: string;
  price: number;
  condition: 'MINT' | 'NEAR_MINT' | 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR';
  isGraded: boolean;
  gradingCompany?: 'PSA' | 'BGS' | 'SGC' | 'CGC' | 'OTHER';
  grade?: number | string; // e.g., 10, 9.5, "GEM MT 10"
  images: string[];
  description?: string;
  seller: User;
  sellerId: string;
  status: 'ACTIVE' | 'SOLD' | 'RESERVED' | 'REMOVED';
  views: number;
  likes: number;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  senderId: string;
  receiverId: string;
  cardId?: string;
  content: string;
  offerAmount?: number;
  read: boolean;
  createdAt: string;
}

export interface Conversation {
  id: string;
  otherUser: User;
  lastMessage: Message;
  unreadCount: number;
  card?: Card;
}

export interface Offer {
  id: string;
  cardId: string;
  card: Card;
  buyerId: string;
  buyer: User;
  amount: number;
  message?: string;
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'COUNTERED';
  createdAt: string;
}

export interface Transaction {
  id: string;
  cardId: string;
  card: Card;
  buyerId: string;
  buyer: User;
  sellerId: string;
  seller: User;
  amount: number;
  status: 'PENDING' | 'PAID' | 'SHIPPED' | 'DELIVERED' | 'COMPLETED' | 'CANCELLED' | 'DISPUTED';
  trackingNumber?: string;
  createdAt: string;
  completedAt?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  CardDetail: { cardId: string };
  UploadCard: undefined;
  EditCard: { cardId: string };
  Profile: { userId: string };
  Settings: undefined;
  Chat: { conversationId: string; otherUserId: string };
};

export type MainTabParamList = {
  Discover: undefined;
  Likes: undefined;
  Upload: undefined;
  Messages: undefined;
  Account: undefined;
};
