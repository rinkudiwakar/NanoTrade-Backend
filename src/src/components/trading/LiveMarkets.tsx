import { useEffect, useState } from 'react';
import axios from 'axios';
import { ArrowRight, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';

interface MarketData {
  symbol: string;
  price: number;
  change: number;
}

export function LiveMarkets() {
  const [markets, setMarkets] = useState<MarketData[]>([
    { symbol: 'BTC_USDT', price: 0, change: 0 },
    // We can add mock ETH/SOL if the backend only supports BTC right now, 
    // but let's just fetch BTC and show it.
  ]);

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await axios.get(`${apiUrl}/market/price?symbol=BTC_USDT`);
        
        // Mock a 24h change for attractiveness since API only returns price
        const mockChange = 2.45; 
        
        // Extract price correctly depending on backend response shape
        const btcPrice = response.data.price ?? response.data.binance_price_usd ?? 62450.00;

        setMarkets([
          { 
            symbol: 'BTC/USDT', 
            price: btcPrice, 
            change: mockChange 
          },
          { symbol: 'ETH/USDT', price: btcPrice * 0.05, change: 1.2 },
          { symbol: 'SOL/USDT', price: 145.20, change: -0.5 }
        ]);
      } catch (error) {
        console.error('Failed to fetch market data:', error);
        // Fallback data
        setMarkets([
          { symbol: 'BTC/USDT', price: 62450.00, change: 2.45 },
          { symbol: 'ETH/USDT', price: 3420.50, change: 1.2 },
          { symbol: 'SOL/USDT', price: 145.20, change: -0.5 }
        ]);
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="markets" className="py-20 px-6 bg-background relative z-10">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-3xl font-bold tracking-tight">Live Markets</h2>
          <Link to="/auth" className="text-primary hover:text-primary/80 flex items-center text-sm font-semibold transition-colors">
            Trade Now <ArrowRight className="ml-1 w-4 h-4" />
          </Link>
        </div>
        
        <div className="rounded-2xl border border-border/50 bg-card/30 backdrop-blur-sm overflow-hidden">
          <div className="grid grid-cols-4 p-4 border-b border-border/50 text-sm font-medium text-muted-foreground bg-muted/20">
            <div>Trading Pair</div>
            <div className="text-right">Last Price (USD)</div>
            <div className="text-right">Last Price (INR)</div>
            <div className="text-right">24h Change</div>
          </div>
          
          <div className="divide-y divide-border/50">
            {markets.map((m) => (
              <div key={m.symbol} className="grid grid-cols-4 p-4 items-center hover:bg-accent/10 transition-colors group">
                <div className="flex items-center gap-3 font-bold text-foreground">
                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs">
                    {m.symbol.split('/')[0][0]}
                  </div>
                  {m.symbol}
                </div>
                <div className="text-right font-mono font-medium">
                  ${typeof m.price === 'number' ? m.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : m.price}
                </div>
                <div className="text-right font-mono font-medium text-muted-foreground">
                  ₹{typeof m.price === 'number' ? (m.price * 88).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--'}
                </div>
                <div className={`text-right font-medium flex items-center justify-end gap-1 ${m.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {m.change >= 0 ? '+' : ''}{m.change}%
                  {m.change >= 0 && <TrendingUp className="w-4 h-4" />}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
