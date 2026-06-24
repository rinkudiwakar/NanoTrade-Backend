import { useEffect, useRef } from 'react';
import { createChart, ColorType, CandlestickSeries } from 'lightweight-charts';
import { useMarketStore } from '@/store/marketStore';

export function ChartContainer() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const currentSymbol = useMarketStore((state) => state.currentSymbol);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#374151', style: 1 },
        horzLines: { color: '#374151', style: 1 },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    // Mock initial data (since there's no historical API specified yet)
    candlestickSeries.setData([
      { time: '2026-06-20', open: 60000, high: 61000, low: 59000, close: 60500 },
      { time: '2026-06-21', open: 60500, high: 62000, low: 60000, close: 61500 },
      { time: '2026-06-22', open: 61500, high: 61800, low: 60500, close: 60800 },
      { time: '2026-06-23', open: 60800, high: 63000, low: 60800, close: 62500 },
    ]);

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
  }, [currentSymbol]);

  return <div ref={chartContainerRef} className="h-full w-full bg-card" />;
}
