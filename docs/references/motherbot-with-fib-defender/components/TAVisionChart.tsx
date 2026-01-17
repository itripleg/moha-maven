// app/motherbot/components/TAVisionChart.tsx
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { useState, useMemo } from "react";
import { useMockData } from "../hooks/useMockData";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell
} from "recharts";

export type HighlightedIndicator =
  | 'rsi' | 'macd' | 'signal' | 'histogram'
  | 'ema9' | 'ema21' | 'ema50'
  | 'fib236' | 'fib382' | 'fib500' | 'fib618' | 'fib786'
  | null;

interface TAVisionChartProps {
  selectedPair: string;
  loading?: boolean;
}

// Custom shape for Candlestick
const CandleStick = (props: any) => {
  const { x, y, width, height, payload, yAxis } = props;
  const { open, close, high, low } = payload;
  
  const isGreen = close >= open;
  const color = isGreen ? 'hsl(145, 65%, 45%)' : 'hsl(0, 72%, 55%)';
  
  // Calculate coordinates using the Y-axis scale function
  const yOpen = yAxis.scale(open);
  const yClose = yAxis.scale(close);
  const yHigh = yAxis.scale(high);
  const yLow = yAxis.scale(low);
  
  const bodyTop = Math.min(yOpen, yClose);
  const bodyHeight = Math.max(Math.abs(yOpen - yClose), 2); // Min 2px height
  
  return (
    <g>
      {/* Wick */}
      <line
        x1={x + width / 2}
        y1={yHigh}
        x2={x + width / 2}
        y2={yLow}
        stroke={color}
        strokeWidth={1}
      />
      {/* Body */}
      <rect
        x={x + 2}
        y={bodyTop}
        width={width - 4}
        height={bodyHeight}
        fill={color}
        stroke={color}
        rx={1}
      />
    </g>
  );
};

export function TAVisionChart({ selectedPair, loading = false }: TAVisionChartProps) {
  const [highlightedIndicator, setHighlightedIndicator] = useState<HighlightedIndicator>(null);
  
  // Visibility toggles for each indicator type
  const [visibleIndicators, setVisibleIndicators] = useState({
    ema20: true,
    ema50: true,
    rsi: true,
    macd: true,
    fib236: true,
    fib382: true,
    fib500: true,
    fib618: true,
    fib786: true,
  });

  const toggleIndicator = (key: keyof typeof visibleIndicators) => {
    setVisibleIndicators(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const { candles } = useMockData();

  // Prepare data for Recharts
  const { chartData, minPrice, maxPrice, actualHigh, actualLow, trend } = useMemo(() => {
    const displayCandles = candles.slice(-40); // Show last 40 candles
    if (displayCandles.length === 0) return { chartData: [], minPrice: 0, maxPrice: 100, actualHigh: 0, actualLow: 0, trend: 'up' };

    const prices = displayCandles.flatMap(c => [c.high, c.low]);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    
    // Calculate simple EMAs for visualization if not in mock data
    const closePrices = displayCandles.map(c => c.close);
    
    const calculateEMA = (startIdx: number, period: number, prevEMA?: number) => {
        const k = 2 / (period + 1);
        const price = closePrices[startIdx];
        if (prevEMA === undefined) return price; // Simple initialization
        return price * k + prevEMA * (1 - k);
    };

    let ema20Val = closePrices[0];
    let ema50Val = closePrices[0];
    
    const processedData = displayCandles.map((c, i) => {
        if (i > 0) {
            ema20Val = calculateEMA(i, 20, ema20Val);
            ema50Val = calculateEMA(i, 50, ema50Val);
        }
        
        // Mock RSI/MACD history generation (consistent with TAVision logic)
        return {
            ...c,
            timestamp: c.time,
            ema20: ema20Val,
            ema50: ema50Val,
            // Generate some plausible looking past indicator data based on price movement
            rsi: 50 + (c.close - c.open) / (max - min) * 1000, 
            macd: (ema20Val - ema50Val) * 0.5,
            signal: (ema20Val - ema50Val) * 0.4,
            histogram: (ema20Val - ema50Val) * 0.1,
        };
    });

    const range = max - min;
    const paddedMin = min - (range * 0.05);
    const paddedMax = max + (range * 0.05);
    
    return {
      chartData: processedData,
      minPrice: paddedMin,
      maxPrice: paddedMax,
      actualHigh: max,
      actualLow: min,
      trend: closePrices[closePrices.length - 1] > closePrices[0] ? 'up' : 'down'
    };
  }, [candles]);

  // Fib Levels
  const fibLevels = useMemo(() => {
     const range = actualHigh - actualLow;
     const levels = [];
     
     if (trend === 'up') {
        levels.push({ level: 0.236, price: actualHigh - range * 0.236, label: '23.6%', color: 'hsl(0, 80%, 60%)', key: 'fib236' });
        levels.push({ level: 0.382, price: actualHigh - range * 0.382, label: '38.2%', color: 'hsl(45, 90%, 50%)', key: 'fib382' });
        levels.push({ level: 0.500, price: actualHigh - range * 0.500, label: '50.0%', color: 'white', key: 'fib500' });
        levels.push({ level: 0.618, price: actualHigh - range * 0.618, label: '61.8%', color: 'hsl(140, 80%, 45%)', key: 'fib618' });
        levels.push({ level: 0.786, price: actualHigh - range * 0.786, label: '78.6%', color: 'hsl(180, 80%, 40%)', key: 'fib786' });
     } else {
        levels.push({ level: 0.236, price: actualLow + range * 0.236, label: '23.6%', color: 'hsl(0, 80%, 60%)', key: 'fib236' });
        levels.push({ level: 0.382, price: actualLow + range * 0.382, label: '38.2%', color: 'hsl(45, 90%, 50%)', key: 'fib382' });
        levels.push({ level: 0.500, price: actualLow + range * 0.500, label: '50.0%', color: 'white', key: 'fib500' });
        levels.push({ level: 0.618, price: actualLow + range * 0.618, label: '61.8%', color: 'hsl(140, 80%, 45%)', key: 'fib618' });
        levels.push({ level: 0.786, price: actualLow + range * 0.786, label: '78.6%', color: 'hsl(180, 80%, 40%)', key: 'fib786' });
     }
     return levels;
  }, [actualHigh, actualLow, trend]);


  if (loading) {
    return (
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardContent className="pt-6">
          <div className="h-[370px] flex items-center justify-center">
            <p className="text-muted-foreground text-sm">Loading chart...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Common Axis Style
  const axisStyle = {
    stroke: 'hsl(var(--muted-foreground))',
    fontSize: 10,
    opacity: 0.5
  };

  return (
    <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
      <CardContent className="pt-6">
        {/* Info Message */}
        <div className="mb-3 p-2 rounded-md bg-primary/5 border border-primary/20 flex justify-between items-center">
          <p className="text-xs text-muted-foreground">
            <strong className="text-primary">TA Vision:</strong> Shows the technical indicators Claude analyzes.
          </p>
          <div className="flex gap-2">
             {/* Legend Toggles */}
             {Object.keys(visibleIndicators).map(key => {
                 const k = key as keyof typeof visibleIndicators;
                 const isActive = visibleIndicators[k];
                 return (
                    <button 
                        key={key}
                        onClick={() => toggleIndicator(k)}
                        className={`text-[9px] px-1.5 py-0.5 rounded border transition-colors ${
                            isActive 
                            ? 'bg-primary/20 border-primary/40 text-primary' 
                            : 'bg-muted/10 border-muted/20 text-muted-foreground'
                        }`}
                        onMouseEnter={() => setHighlightedIndicator(key as HighlightedIndicator)}
                        onMouseLeave={() => setHighlightedIndicator(null)}
                    >
                        {key.toUpperCase()}
                    </button>
                 )
             })}
          </div>
        </div>

        {/* Main Price Chart */}
        <div className="h-[280px] w-full mb-1">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                 <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                       <feMergeNode in="coloredBlur"/>
                       <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                 </filter>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.1} />
              <XAxis 
                dataKey="timestamp" 
                tick={false} 
                axisLine={false} 
                height={0}
              />
              <YAxis 
                domain={[minPrice, maxPrice]} 
                orientation="right"
                tick={{ ...axisStyle, fontSize: 9 }}
                tickFormatter={(val) => val.toFixed(0)}
                width={40}
                axisLine={false}
              />
              <Tooltip 
                 contentStyle={{ backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))', fontSize: '12px' }}
                 labelFormatter={(ts) => new Date(ts).toLocaleTimeString()}
              />
              
              {/* Fib Levels */}
              {fibLevels.map((fib) => {
                  const isVisible = visibleIndicators[fib.key as keyof typeof visibleIndicators];
                  if (!isVisible) return null;
                  
                  return (
                    <ReferenceLine 
                        key={fib.key} 
                        y={fib.price} 
                        stroke={fib.color} 
                        strokeDasharray="3 3"
                        strokeOpacity={highlightedIndicator === fib.key ? 1 : 0.5}
                        strokeWidth={highlightedIndicator === fib.key ? 2 : 1}
                        label={{ 
                            value: fib.label, 
                            position: 'left', 
                            fill: fib.color, 
                            fontSize: 10,
                            opacity: 0.8
                        }}
                    />
                  );
              })}

              {/* EMAs */}
              {visibleIndicators.ema20 && (
                <Line 
                    type="monotone" 
                    dataKey="ema20" 
                    stroke="hsl(175, 80%, 50%)" 
                    strokeWidth={highlightedIndicator === 'ema9' ? 3 : 1.5}
                    dot={false}
                    filter={highlightedIndicator === 'ema9' ? "url(#glow)" : ""}
                />
              )}
              {visibleIndicators.ema50 && (
                <Line 
                    type="monotone" 
                    dataKey="ema50" 
                    stroke="hsl(280, 80%, 60%)" 
                    strokeWidth={highlightedIndicator === 'ema21' ? 3 : 1.5}
                    dot={false}
                    filter={highlightedIndicator === 'ema21' ? "url(#glow)" : ""}
                />
              )}

              {/* Candles */}
              <Bar 
                dataKey="close" 
                shape={<CandleStick />} 
                isAnimationActive={false}
              >
                {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill="transparent" />
                ))}
            </Bar>

            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Sub Charts Grid */}
        <div className="grid grid-cols-2 gap-2 h-[100px]">
            {/* RSI */}
            <div className="bg-secondary/10 rounded overflow-hidden relative">
                <div className="absolute top-1 left-2 text-[9px] font-mono text-muted-foreground z-10">RSI</div>
                {visibleIndicators.rsi && (
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                            <YAxis domain={[0, 100]} hide />
                            <ReferenceLine y={70} stroke="hsl(var(--destructive))" strokeDasharray="2 2" opacity={0.5} />
                            <ReferenceLine y={30} stroke="hsl(var(--success))" strokeDasharray="2 2" opacity={0.5} />
                            <Line 
                                type="monotone" 
                                dataKey="rsi" 
                                stroke="hsl(var(--primary))" 
                                strokeWidth={2} 
                                dot={false}
                                filter={highlightedIndicator === 'rsi' ? "url(#glow)" : ""}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* MACD */}
            <div className="bg-secondary/10 rounded overflow-hidden relative">
                <div className="absolute top-1 left-2 text-[9px] font-mono text-muted-foreground z-10">MACD</div>
                {visibleIndicators.macd && (
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                            <YAxis hide />
                            <Bar 
                                dataKey="histogram" 
                                fill="hsl(var(--muted-foreground))" 
                                opacity={0.3} 
                                isAnimationActive={false}
                            />
                            <Line 
                                type="monotone" 
                                dataKey="macd" 
                                stroke="#3b82f6" 
                                strokeWidth={1.5} 
                                dot={false} 
                            />
                            <Line 
                                type="monotone" 
                                dataKey="signal" 
                                stroke="#ef4444" 
                                strokeWidth={1.5} 
                                dot={false} 
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>

      </CardContent>
    </Card>
  );
}
