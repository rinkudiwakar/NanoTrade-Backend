import { useEffect, useRef } from 'react';
import { createChart, ColorType, AreaSeries } from 'lightweight-charts';

export function HeroChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#6b7280',
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      timeScale: {
        visible: false,
      },
      rightPriceScale: {
        visible: false,
      },
      handleScroll: false,
      handleScale: false,
      crosshair: {
        mode: 0,
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: '#22c55e',
      topColor: 'rgba(34, 197, 94, 0.4)',
      bottomColor: 'rgba(34, 197, 94, 0.0)',
      lineWidth: 2,
    });

    // Generate random upward trending data
    const data = [];
    let price = 50000;
    let time = Math.floor(Date.now() / 1000) - 100 * 86400;
    for (let i = 0; i < 100; i++) {
      price += Math.random() * 1000 - 400;
      data.push({ time: time as any, value: price });
      time += 86400;
    }
    
    // @ts-ignore
    series.setData(data);

    const handleResize = () => {
      chart.applyOptions({
        width: chartContainerRef.current?.clientWidth || 0,
        height: chartContainerRef.current?.clientHeight || 0,
      });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  return (
    <div className="relative w-full h-full overflow-hidden rounded-2xl border border-border/50 bg-card/40 backdrop-blur-md shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent z-10" />
        <div ref={chartContainerRef} className="absolute inset-0" />
        
        {/* Mock UI overlay on chart */}
        <div className="absolute top-6 left-6 z-20">
            <div className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">BTC / INR</div>
            <div className="text-4xl font-black tracking-tighter mt-1 text-foreground">₹52,43,100.00</div>
            <div className="flex items-center text-sm font-bold text-green-500 mt-2 bg-green-500/10 w-fit px-2 py-1 rounded">
                +4.25% (24h)
            </div>
        </div>
        
        <div className="absolute bottom-6 right-6 z-20 flex gap-3">
           <div className="bg-green-600 hover:bg-green-700 transition-colors text-white px-6 py-2.5 rounded-lg font-bold text-sm cursor-pointer shadow-lg shadow-green-900/20">
             BUY
           </div>
           <div className="bg-red-600 hover:bg-red-700 transition-colors text-white px-6 py-2.5 rounded-lg font-bold text-sm cursor-pointer shadow-lg shadow-red-900/20">
             SELL
           </div>
        </div>

        <div className="absolute top-6 right-6 z-20">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground bg-background/80 px-3 py-1.5 rounded-full border">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                Market Open
            </div>
        </div>
    </div>
  );
}
