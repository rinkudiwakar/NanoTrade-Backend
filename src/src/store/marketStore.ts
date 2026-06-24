import { create } from 'zustand';

export interface OrderBookEntry {
  price: number;
  quantity: number;
}

export interface Trade {
  id: string;
  price: number;
  quantity: number;
  side: string;
  timestamp: string;
}

interface MarketState {
  currentSymbol: string;
  priceUsd: number;
  conversionRate: number; // For INR conversion
  orderbook: { bids: OrderBookEntry[], asks: OrderBookEntry[] };
  recentTrades: Trade[];
  
  // Computed values can be derived in components, but we keep state simple
  setCurrentSymbol: (symbol: string) => void;
  setPriceUsd: (price: number) => void;
  setConversionRate: (rate: number) => void;
  setOrderbook: (bids: OrderBookEntry[], asks: OrderBookEntry[]) => void;
  addTrades: (trades: Trade[]) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  currentSymbol: 'BTC_USDT',
  priceUsd: 0,
  conversionRate: 90, // Fallback conversion rate
  orderbook: { bids: [], asks: [] },
  recentTrades: [],
  
  setCurrentSymbol: (symbol) => set({ currentSymbol: symbol }),
  setPriceUsd: (price) => set({ priceUsd: price }),
  setConversionRate: (rate) => set({ conversionRate: rate }),
  setOrderbook: (bids, asks) => set({ orderbook: { bids, asks } }),
  addTrades: (trades) => set((state) => ({
    recentTrades: [...trades, ...state.recentTrades].slice(0, 100) // Keep latest 100 trades
  }))
}));
