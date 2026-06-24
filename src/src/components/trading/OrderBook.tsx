import React from 'react';
import { useMarketStore } from '@/store/marketStore';

export const OrderBook = React.memo(() => {
  const { bids, asks } = useMarketStore((state) => state.orderbook);
  const priceUsd = useMarketStore((state) => state.priceUsd);
  const conversionRate = useMarketStore((state) => state.conversionRate);

  // Take top 15 rows
  const displayAsks = asks.slice(0, 15).reverse(); // highest to lowest
  const displayBids = bids.slice(0, 15); // highest to lowest
  
  const maxVolume = Math.max(
    ...bids.map(b => b.quantity), 
    ...asks.map(a => a.quantity),
    1
  );

  return (
    <div className="flex h-full flex-col border-l bg-card text-xs">
      <div className="border-b p-3 font-semibold text-muted-foreground flex justify-between">
        <span>Order Book</span>
      </div>
      <div className="flex justify-between px-3 py-1 text-[10px] text-muted-foreground">
        <span>Price (INR)</span>
        <span>Qty</span>
      </div>
      
      {/* Asks (Red) */}
      <div className="flex flex-1 flex-col justify-end overflow-hidden">
        {displayAsks.map((ask, i) => {
          const priceInr = ask.price * conversionRate;
          const depthPct = (ask.quantity / maxVolume) * 100;
          return (
            <div key={`ask-${i}`} className="relative flex justify-between px-3 py-0.5 hover:bg-accent/50 cursor-pointer">
              <div className="absolute right-0 top-0 h-full bg-red-500/10" style={{ width: `${depthPct}%` }} />
              <span className="text-red-500 z-10">{priceInr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              <span className="z-10 text-foreground">{ask.quantity.toFixed(4)}</span>
            </div>
          );
        })}
      </div>
      
      {/* Spread / Current Price */}
      <div className="flex items-center justify-center border-y py-2 font-semibold">
        <span className="text-sm">₹{(priceUsd * conversionRate).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
      </div>
      
      {/* Bids (Green) */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {displayBids.map((bid, i) => {
          const priceInr = bid.price * conversionRate;
          const depthPct = (bid.quantity / maxVolume) * 100;
          return (
            <div key={`bid-${i}`} className="relative flex justify-between px-3 py-0.5 hover:bg-accent/50 cursor-pointer">
              <div className="absolute right-0 top-0 h-full bg-green-500/10" style={{ width: `${depthPct}%` }} />
              <span className="text-green-500 z-10">{priceInr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              <span className="z-10 text-foreground">{bid.quantity.toFixed(4)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
});

OrderBook.displayName = 'OrderBook';
