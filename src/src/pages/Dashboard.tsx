import { Watchlist } from '@/components/trading/Watchlist';
import { ChartContainer } from '@/components/trading/ChartContainer';
import { OrderBook } from '@/components/trading/OrderBook';
import { TradeFeed } from '@/components/trading/TradeFeed';
import { OrderForm } from '@/components/trading/OrderForm';
import { PortfolioTabs } from '@/components/trading/PortfolioTabs';
import { PriceTicker } from '@/components/trading/PriceTicker';
import { useWebSocket } from '@/hooks/useWebSocket';

export function Dashboard() {
  useWebSocket(); // Initialize WS connection

  return (
    <div className="flex h-screen w-full flex-col bg-background text-foreground overflow-hidden">
      <PriceTicker />
      
      {/* Main Grid Layout */}
      <div className="grid h-[calc(100vh-73px)] grid-cols-[250px_1fr_300px]">
        {/* Left Sidebar */}
        <div className="flex flex-col h-full border-r overflow-hidden">
          <div className="flex-1 min-h-[50%] overflow-hidden">
            <Watchlist />
          </div>
          <div className="h-[350px]">
            <OrderForm />
          </div>
        </div>

        {/* Center Main Area */}
        <div className="flex flex-col h-full overflow-hidden">
          <div className="flex-1 bg-card border-b relative">
            <div className="absolute inset-0">
              <ChartContainer />
            </div>
          </div>
          <div className="h-[300px]">
            <PortfolioTabs />
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="flex flex-col h-full border-l overflow-hidden">
          <div className="flex-1 overflow-hidden">
            <OrderBook />
          </div>
          <div className="h-[300px] border-t">
            <TradeFeed />
          </div>
        </div>
      </div>
    </div>
  );
}
