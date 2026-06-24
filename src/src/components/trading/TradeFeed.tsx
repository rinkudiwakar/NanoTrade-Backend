import React from 'react';
import { useMarketStore } from '@/store/marketStore';

export const TradeFeed = React.memo(() => {
  const trades = useMarketStore((state) => state.recentTrades);
  const conversionRate = useMarketStore((state) => state.conversionRate);

  return (
    <div className="flex h-full flex-col border-l border-t bg-card text-xs">
      <div className="border-b p-3 font-semibold text-muted-foreground">
        <span>Recent Trades</span>
      </div>
      <div className="flex justify-between px-3 py-1 text-[10px] text-muted-foreground">
        <span>Price (INR)</span>
        <span>Qty</span>
        <span>Time</span>
      </div>
      <div className="flex-1 overflow-auto">
        {trades.map((trade, i) => {
          const priceInr = trade.price * conversionRate;
          const isBuy = trade.side.toUpperCase() === 'BUY';
          const time = new Date(trade.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second:'2-digit' });
          
          return (
            <div key={trade.id || i} className="flex justify-between px-3 py-1 hover:bg-accent/50">
              <span className={isBuy ? 'text-green-500' : 'text-red-500'}>
                {priceInr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span>{trade.quantity.toFixed(4)}</span>
              <span className="text-muted-foreground">{time}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
});

TradeFeed.displayName = 'TradeFeed';
