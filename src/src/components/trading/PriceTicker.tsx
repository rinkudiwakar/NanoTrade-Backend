import { useMarketStore } from '@/store/marketStore';
import { useUserStore } from '@/store/userStore';
import { Button } from '@/components/ui/button';
import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function PriceTicker() {
  const symbol = useMarketStore((state) => state.currentSymbol);
  const priceUsd = useMarketStore((state) => state.priceUsd);
  const conversionRate = useMarketStore((state) => state.conversionRate);
  const { session, signOut } = useUserStore();
  const navigate = useNavigate();
  
  const priceInr = priceUsd * conversionRate;
  
  const handleLogout = async () => {
    await signOut();
    navigate('/');
  };
  
  return (
    <div className="flex items-center justify-between border-b bg-card p-4">
      <div className="flex items-center gap-4">
        <div className="w-8 h-8 bg-primary/20 rounded flex items-center justify-center font-bold text-primary mr-2">
            N
        </div>
        <div className="text-xl font-bold tracking-tight">{symbol.replace('_', '/')}</div>
        <div className="flex flex-col">
          <span className="text-lg font-semibold text-green-500">
            {priceUsd > 0 ? `₹${priceInr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---'}
          </span>
          <span className="text-xs text-muted-foreground">
            {priceUsd > 0 ? `$${priceUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---'}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-muted-foreground hidden md:inline">{session?.user?.email}</span>
        <Button variant="ghost" size="icon" onClick={handleLogout} title="Log out">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
