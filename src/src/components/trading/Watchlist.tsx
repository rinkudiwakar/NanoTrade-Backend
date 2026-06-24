import { useMarketStore } from '@/store/marketStore';

const ASSETS = [
  { id: 'BTC_USDT', name: 'Bitcoin', symbol: 'BTC' },
  { id: 'ETH_USDT', name: 'Ethereum', symbol: 'ETH' },
  { id: 'SOL_USDT', name: 'Solana', symbol: 'SOL' }
];

export function Watchlist() {
  const currentSymbol = useMarketStore((state) => state.currentSymbol);
  const setSymbol = useMarketStore((state) => state.setCurrentSymbol);
  const priceUsd = useMarketStore((state) => state.priceUsd);
  const conversionRate = useMarketStore((state) => state.conversionRate);
  
  return (
    <div className="flex h-full flex-col border-r bg-card">
      <div className="border-b p-4">
        <h2 className="text-sm font-semibold text-muted-foreground">Watchlist</h2>
      </div>
      <div className="flex-1 overflow-auto">
        {ASSETS.map((asset) => {
          const isSelected = currentSymbol === asset.id;
          // Only the active symbol shows live price for now
          const displayPrice = isSelected ? priceUsd * conversionRate : 0; 
          return (
            <div
              key={asset.id}
              onClick={() => setSymbol(asset.id)}
              className={`flex cursor-pointer items-center justify-between border-b p-3 transition-colors hover:bg-accent/50 ${isSelected ? 'bg-accent' : ''}`}
            >
              <div>
                <div className="font-medium text-sm">{asset.symbol}/INR</div>
                <div className="text-xs text-muted-foreground">{asset.name}</div>
              </div>
              <div className="text-right">
                <div className="font-medium text-sm">
                  {displayPrice > 0 ? `₹${displayPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '---'}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  );
}
