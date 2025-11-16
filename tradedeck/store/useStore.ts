import { create } from 'zustand';
import { Card, User, Filter, Message } from '@/types';

interface StoreState {
  // User state
  user: User | null;
  setUser: (user: User | null) => void;

  // Cards state
  cards: Card[];
  setCards: (cards: Card[]) => void;
  likedCards: string[];
  toggleLike: (cardId: string) => void;

  // Filter state
  filters: Filter;
  setFilters: (filters: Filter) => void;
  resetFilters: () => void;

  // Messages state
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;

  // UI state
  isSwipeMode: boolean;
  setSwipeMode: (mode: boolean) => void;
  currentCardIndex: number;
  setCurrentCardIndex: (index: number) => void;
}

export const useStore = create<StoreState>((set) => ({
  // User
  user: null,
  setUser: (user) => set({ user }),

  // Cards
  cards: [],
  setCards: (cards) => set({ cards }),
  likedCards: [],
  toggleLike: (cardId) =>
    set((state) => ({
      likedCards: state.likedCards.includes(cardId)
        ? state.likedCards.filter((id) => id !== cardId)
        : [...state.likedCards, cardId],
    })),

  // Filters
  filters: {},
  setFilters: (filters) => set({ filters }),
  resetFilters: () => set({ filters: {} }),

  // Messages
  messages: [],
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  // UI
  isSwipeMode: true,
  setSwipeMode: (mode) => set({ isSwipeMode: mode }),
  currentCardIndex: 0,
  setCurrentCardIndex: (index) => set({ currentCardIndex: index }),
}));
