import { useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function PortfolioTabs() {
  const { balance, holdings, orders, fetchPortfolio, fetchOrders } = useUserStore();

  useEffect(() => {
    fetchPortfolio();
    fetchOrders();
  }, [fetchPortfolio, fetchOrders]);

  return (
    <div className="flex h-full flex-col bg-card border-t">
      <Tabs defaultValue="positions" className="flex-1 flex flex-col">
        <TabsList className="justify-start border-b rounded-none w-full bg-transparent p-0">
          <TabsTrigger value="positions" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Positions</TabsTrigger>
          <TabsTrigger value="orders" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Orders</TabsTrigger>
          <TabsTrigger value="holdings" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Holdings</TabsTrigger>
        </TabsList>
        
        <TabsContent value="positions" className="flex-1 p-0 m-0 overflow-auto">
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground p-8 text-center">
            You don't have any open positions right now.
          </div>
        </TabsContent>
        
        <TabsContent value="orders" className="flex-1 p-0 m-0 overflow-auto">
          {orders.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground p-8 text-center">
              Your order history is empty.
            </div>
          ) : (
            <table className="w-full text-sm text-left">
              <thead className="sticky top-0 bg-card">
                <tr className="text-muted-foreground border-b text-xs">
                  <th className="py-2 pl-4 font-normal">Time</th>
                  <th className="py-2 font-normal">Symbol</th>
                  <th className="py-2 font-normal">Side</th>
                  <th className="py-2 font-normal">Type</th>
                  <th className="py-2 font-normal">Price</th>
                  <th className="py-2 font-normal">Qty</th>
                  <th className="py-2 pr-4 font-normal text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                    <td className="py-2 pl-4">{new Date(order.created_at).toLocaleTimeString()}</td>
                    <td className="py-2 font-medium">{order.symbol}</td>
                    <td className={`py-2 font-medium ${order.side === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>{order.side}</td>
                    <td className="py-2">{order.type}</td>
                    <td className="py-2">₹{order.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                    <td className="py-2">{order.quantity}</td>
                    <td className="py-2 pr-4 text-right">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        order.status === 'FILLED' ? 'bg-green-500/10 text-green-500' :
                        order.status === 'REJECTED' ? 'bg-red-500/10 text-red-500' :
                        'bg-yellow-500/10 text-yellow-500'
                      }`}>
                        {order.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </TabsContent>

        <TabsContent value="holdings" className="flex-1 p-0 m-0 overflow-auto">
          <div className="p-4 border-b bg-muted/20 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Available Margin</span>
            <div className="text-2xl font-bold text-foreground">₹{balance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>
          
          {holdings.length === 0 ? (
            <div className="flex items-center justify-center text-sm text-muted-foreground p-8 text-center">
              No assets in your portfolio.
            </div>
          ) : (
            <table className="w-full text-sm text-left">
              <thead className="sticky top-0 bg-card">
                <tr className="text-muted-foreground border-b text-xs">
                  <th className="py-2 pl-4 font-normal">Asset</th>
                  <th className="py-2 pr-4 font-normal text-right">Quantity</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((h, i) => (
                  <tr key={i} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                    <td className="py-3 pl-4 font-medium">{h.symbol}</td>
                    <td className="py-3 pr-4 text-right">{h.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
