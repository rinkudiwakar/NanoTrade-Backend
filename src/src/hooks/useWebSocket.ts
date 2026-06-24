import { useEffect, useRef } from 'react';
import { useMarketStore } from '@/store/marketStore';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/market';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  const setPriceUsd = useMarketStore((state) => state.setPriceUsd);
  const setOrderbook = useMarketStore((state) => state.setOrderbook);
  const addTrades = useMarketStore((state) => state.addTrades);
  
  useEffect(() => {
    function connect() {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;
      
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        console.log('WebSocket connected to market stream');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'price_update' || data.event === 'price_update') {
            setPriceUsd(data.price || data.data?.price);
          } else if (data.type === 'orderbook_update' || data.event === 'orderbook_update') {
            const ob = data.orderbook || data.data;
            if (ob) setOrderbook(ob.bids, ob.asks);
          } else if (data.type === 'trade_execution' || data.event === 'trade_execution') {
            const trade = data.trade || data.data;
            if (trade) addTrades([trade]);
          }
        } catch (error) {
          console.error("Failed to parse WS message", error);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting in 3s...');
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };
      
      wsRef.current = ws;
    }
    
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [setPriceUsd, setOrderbook, addTrades]);
}
