import { create } from 'zustand';
import { supabase } from '@/lib/supabase';
import { api } from '@/services/api';
import type { Session } from '@supabase/supabase-js';

interface Holding {
  symbol: string;
  quantity: number;
}

interface Order {
  id: string;
  symbol: string;
  side: string;
  type: string;
  quantity: number;
  price: number;
  status: string;
  created_at: string;
}

interface UserState {
  session: Session | null;
  balance: number;
  holdings: Holding[];
  orders: Order[];
  isInitialized: boolean;
  setSession: (session: Session | null) => void;
  fetchPortfolio: () => Promise<void>;
  fetchOrders: () => Promise<void>;
  initializeAuth: () => void;
  signOut: () => Promise<void>;
}

export const useUserStore = create<UserState>((set, get) => ({
  session: null,
  balance: 0,
  holdings: [],
  orders: [],
  isInitialized: false,

  setSession: (session) => set({ session }),

  fetchPortfolio: async () => {
    if (!get().session) return;
    try {
      const { data } = await api.get('/portfolio');
      set({ 
        balance: data?.balance || 0, 
        holdings: Array.isArray(data?.holdings) ? data.holdings : [] 
      });
    } catch (error) {
      console.error("Failed to fetch portfolio", error);
    }
  },

  fetchOrders: async () => {
    if (!get().session) return;
    try {
      const { data } = await api.get('/orders/history');
      // Backend might return an array directly, or an object like { orders: [...] }
      const ordersArray = Array.isArray(data) ? data : (data?.orders || []);
      set({ orders: Array.isArray(ordersArray) ? ordersArray : [] });
    } catch (error) {
      console.error("Failed to fetch orders history", error);
    }
  },

  initializeAuth: () => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      set({ session, isInitialized: true });
      if (session) {
        get().fetchPortfolio();
        get().fetchOrders();
      }
    });

    supabase.auth.onAuthStateChange((_event, session) => {
      set({ session });
      if (session) {
        get().fetchPortfolio();
        get().fetchOrders();
      } else {
        set({ balance: 0, holdings: [], orders: [] });
      }
    });
  },

  signOut: async () => {
    await supabase.auth.signOut();
    set({ session: null, balance: 0, holdings: [], orders: [] });
  }
}));
