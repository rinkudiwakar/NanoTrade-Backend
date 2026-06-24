import React, { useState } from 'react';
import { useMarketStore } from '@/store/marketStore';
import { api } from '@/services/api';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function OrderForm() {
  const currentSymbol = useMarketStore((state) => state.currentSymbol);
  const priceUsd = useMarketStore((state) => state.priceUsd);
  const conversionRate = useMarketStore((state) => state.conversionRate);
  
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [type, setType] = useState<'LIMIT' | 'MARKET'>('LIMIT');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  
  const currentPriceInr = priceUsd * conversionRate;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        symbol: currentSymbol,
        side,
        type,
        quantity: parseFloat(quantity),
        price: type === 'LIMIT' ? parseFloat(price) : currentPriceInr,
      };
      const res = await api.post('/orders', payload);
      alert('Order placed: ' + res.data.status);
    } catch (error) {
      alert('Failed to place order.');
    }
  };

  return (
    <div className="flex flex-col h-full border-t border-r bg-card p-4">
      <div className="flex gap-2 mb-4">
        <Button 
          variant={side === 'BUY' ? 'default' : 'outline'} 
          className={side === 'BUY' ? 'bg-green-600 text-white hover:bg-green-700 flex-1' : 'flex-1'}
          onClick={() => setSide('BUY')}
        >BUY</Button>
        <Button 
          variant={side === 'SELL' ? 'default' : 'outline'} 
          className={side === 'SELL' ? 'bg-red-600 text-white hover:bg-red-700 flex-1' : 'flex-1'}
          onClick={() => setSide('SELL')}
        >SELL</Button>
      </div>
      
      <Tabs value={type} onValueChange={(v) => setType(v as 'LIMIT' | 'MARKET')} className="w-full">
        <TabsList className="w-full grid grid-cols-2 mb-4">
          <TabsTrigger value="LIMIT">Limit</TabsTrigger>
          <TabsTrigger value="MARKET">Market</TabsTrigger>
        </TabsList>
      </Tabs>
      
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 flex-1">
        {type === 'LIMIT' && (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Price (INR)</label>
            <Input 
              type="number" 
              step="0.01" 
              value={price} 
              onChange={e => setPrice(e.target.value)} 
              placeholder={currentPriceInr.toFixed(2)} 
              required={type === 'LIMIT'}
            />
          </div>
        )}
        
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Quantity ({currentSymbol.split('_')[0]})</label>
          <Input 
            type="number" 
            step="0.0001" 
            value={quantity} 
            onChange={e => setQuantity(e.target.value)} 
            placeholder="0.00" 
            required
          />
        </div>
        
        <div className="mt-auto pt-4">
          <Button type="submit" className={`w-full ${side === 'BUY' ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-red-600 hover:bg-red-700 text-white'}`}>
            {side} {currentSymbol.split('_')[0]}
          </Button>
        </div>
      </form>
    </div>
  );
}
