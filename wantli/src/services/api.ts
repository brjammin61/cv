import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../config/api';
import {
  User,
  Card,
  Conversation,
  Message,
  Offer,
  Transaction,
  ApiResponse,
} from '../types';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('user');
      // Redirect to login would be handled by navigation
    }
    return Promise.reject(error);
  }
);

// Authentication
export const authApi = {
  signUp: async (data: {
    email: string;
    password: string;
    name: string;
  }): Promise<ApiResponse<{ user: User; token: string }>> => {
    const response = await api.post('/auth/signup', data);
    return response.data;
  },

  signIn: async (data: {
    email: string;
    password: string;
  }): Promise<ApiResponse<{ user: User; token: string }>> => {
    const response = await api.post('/auth/signin', data);
    return response.data;
  },

  getMe: async (): Promise<ApiResponse<User>> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<ApiResponse<User>> => {
    const response = await api.put('/auth/profile', data);
    return response.data;
  },
};

// Cards
export const cardsApi = {
  getCards: async (params?: {
    sport?: string;
    minPrice?: number;
    maxPrice?: number;
    isGraded?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<Card[]>> => {
    const response = await api.get('/cards', { params });
    return response.data;
  },

  getCardById: async (id: string): Promise<ApiResponse<Card>> => {
    const response = await api.get(`/cards/${id}`);
    return response.data;
  },

  createCard: async (data: Partial<Card>): Promise<ApiResponse<Card>> => {
    const response = await api.post('/cards', data);
    return response.data;
  },

  updateCard: async (id: string, data: Partial<Card>): Promise<ApiResponse<Card>> => {
    const response = await api.put(`/cards/${id}`, data);
    return response.data;
  },

  deleteCard: async (id: string): Promise<ApiResponse<void>> => {
    const response = await api.delete(`/cards/${id}`);
    return response.data;
  },

  likeCard: async (id: string): Promise<ApiResponse<void>> => {
    const response = await api.post(`/cards/${id}/like`);
    return response.data;
  },

  getLikedCards: async (): Promise<ApiResponse<Card[]>> => {
    const response = await api.get('/cards/liked');
    return response.data;
  },

  getMyCards: async (): Promise<ApiResponse<Card[]>> => {
    const response = await api.get('/cards/my-cards');
    return response.data;
  },
};

// Messages
export const messagesApi = {
  getConversations: async (): Promise<ApiResponse<Conversation[]>> => {
    const response = await api.get('/messages/conversations');
    return response.data;
  },

  getMessages: async (otherUserId: string): Promise<ApiResponse<Message[]>> => {
    const response = await api.get(`/messages/${otherUserId}`);
    return response.data;
  },

  sendMessage: async (data: {
    receiverId: string;
    content: string;
    cardId?: string;
    offerAmount?: number;
  }): Promise<ApiResponse<Message>> => {
    const response = await api.post('/messages', data);
    return response.data;
  },

  markAsRead: async (messageId: string): Promise<ApiResponse<void>> => {
    const response = await api.put(`/messages/${messageId}/read`);
    return response.data;
  },
};

// Offers
export const offersApi = {
  createOffer: async (data: {
    cardId: string;
    amount: number;
    message?: string;
  }): Promise<ApiResponse<Offer>> => {
    const response = await api.post('/offers', data);
    return response.data;
  },

  getMyOffers: async (): Promise<ApiResponse<Offer[]>> => {
    const response = await api.get('/offers/sent');
    return response.data;
  },

  getReceivedOffers: async (): Promise<ApiResponse<Offer[]>> => {
    const response = await api.get('/offers/received');
    return response.data;
  },

  acceptOffer: async (id: string): Promise<ApiResponse<Transaction>> => {
    const response = await api.post(`/offers/${id}/accept`);
    return response.data;
  },

  rejectOffer: async (id: string): Promise<ApiResponse<void>> => {
    const response = await api.post(`/offers/${id}/reject`);
    return response.data;
  },

  counterOffer: async (
    id: string,
    amount: number
  ): Promise<ApiResponse<Offer>> => {
    const response = await api.post(`/offers/${id}/counter`, { amount });
    return response.data;
  },
};

// Transactions
export const transactionsApi = {
  getMyTransactions: async (): Promise<ApiResponse<Transaction[]>> => {
    const response = await api.get('/transactions');
    return response.data;
  },

  getTransactionById: async (id: string): Promise<ApiResponse<Transaction>> => {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
  },

  createTransaction: async (data: {
    cardId: string;
    offerId?: string;
  }): Promise<ApiResponse<Transaction>> => {
    const response = await api.post('/transactions', data);
    return response.data;
  },

  updateShipping: async (
    id: string,
    trackingNumber: string
  ): Promise<ApiResponse<Transaction>> => {
    const response = await api.put(`/transactions/${id}/shipping`, {
      trackingNumber,
    });
    return response.data;
  },

  confirmDelivery: async (id: string): Promise<ApiResponse<Transaction>> => {
    const response = await api.post(`/transactions/${id}/confirm-delivery`);
    return response.data;
  },
};

// Image Upload (Cloudinary)
export const uploadImage = async (uri: string): Promise<string> => {
  const formData = new FormData();
  const filename = uri.split('/').pop() || 'image.jpg';
  const match = /\.(\w+)$/.exec(filename);
  const type = match ? `image/${match[1]}` : 'image/jpeg';

  formData.append('file', {
    uri,
    name: filename,
    type,
  } as any);
  formData.append('upload_preset', 'wantli_cards');

  const response = await axios.post(
    `https://api.cloudinary.com/v1_1/${process.env.EXPO_PUBLIC_CLOUDINARY_CLOUD_NAME}/image/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data.secure_url;
};

export default api;
