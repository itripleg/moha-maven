import React, { useMemo } from 'react';
import { Candle, FibLevel, Position } from '@/types/game';

interface CandlestickChartProps {
  candles: Candle[];
  fibLevels: FibLevel[];
  currentPrice: number;
  timeframe: number;
  position: Position | null;
  pnl: number;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  candles,
  fibLevels,
  currentPrice,
  timeframe,
  position,
  pnl,
}) => {
  const displayCandles = candles.slice(-timeframe * 10);

  const { minPrice, maxPrice, priceRange } = useMemo(() => {
    const highs = displayCandles.map(c => c.high);
    const lows = displayCandles.map(c => c.low);
    const min = Math.min(...lows);
    const max = Math.max(...highs);
    const padding = (max - min) * 0.1;
    return {
      minPrice: min - padding,
      maxPrice: max + padding,
      priceRange: max - min + padding * 2,
    };
  }, [displayCandles]);

  const chartWidth = 800;
  const chartHeight = 350;
  const candleWidth = (chartWidth - 60) / displayCandles.length;
  const bodyWidth = candleWidth * 0.7;

  const priceToY = (price: number) => {
    return chartHeight - ((price - minPrice) / priceRange) * chartHeight;
  };

  const glowingLevel = fibLevels.find(f => f.isGlowing);

  return (
    <div className="relative w-full bg-card/30 backdrop-blur-sm border border-primary/40 rounded-lg overflow-hidden">
      {/* Scanline effect */}
      <div className="absolute inset-0 pointer-events-none opacity-10"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)',
        }}
      />

      {/* Grid background */}
      <div className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `
            linear-gradient(to right, hsl(var(--border)) 1px, transparent 1px),
            linear-gradient(to bottom, hsl(var(--border)) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      <svg
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        className="w-full h-[350px]"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          {/* Glow filters */}
          <filter id="glow-cyan" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-gold" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-intense" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Fibonacci levels */}
        {fibLevels.map((fib, index) => {
          const y = priceToY(fib.price);

          return (
            <g key={index}>
              <line
                x1={50}
                y1={y}
                x2={chartWidth}
                y2={y}
                stroke={fib.color}
                strokeWidth={fib.isGlowing ? 2 : 1}
                strokeDasharray={fib.level === 0.618 ? "0" : "5,5"}
                opacity={fib.isGlowing ? 1 : 0.5}
                filter={fib.isGlowing ? "url(#glow-intense)" : "none"}
                className={fib.isGlowing ? "animate-pulse" : ""}
              />
              <text
                x={5}
                y={y + 4}
                fill={fib.color}
                fontSize="10"
                fontFamily="monospace"
                opacity={fib.isGlowing ? 1 : 0.7}
                filter={fib.isGlowing ? "url(#glow-gold)" : "none"}
              >
                {fib.label}
              </text>
              <text
                x={chartWidth - 5}
                y={y + 4}
                fill={fib.color}
                fontSize="9"
                fontFamily="monospace"
                textAnchor="end"
                opacity={0.8}
              >
                ${fib.price.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Candlesticks */}
        {displayCandles.map((candle, index) => {
          const x = 60 + index * candleWidth;
          const isGreen = candle.close >= candle.open;
          const color = isGreen ? 'hsl(145, 65%, 45%)' : 'hsl(0, 72%, 55%)';

          const bodyTop = priceToY(Math.max(candle.open, candle.close));
          const bodyBottom = priceToY(Math.min(candle.open, candle.close));
          const bodyHeight = Math.max(1, bodyBottom - bodyTop);

          const wickTop = priceToY(candle.high);
          const wickBottom = priceToY(candle.low);

          return (
            <g key={index}>
              {/* Wick */}
              <line
                x1={x + bodyWidth / 2}
                y1={wickTop}
                x2={x + bodyWidth / 2}
                y2={wickBottom}
                stroke={color}
                strokeWidth={1}
              />
              {/* Body */}
              <rect
                x={x}
                y={bodyTop}
                width={bodyWidth}
                height={bodyHeight}
                fill={isGreen ? color : 'transparent'}
                stroke={color}
                strokeWidth={1}
                filter={index === displayCandles.length - 1 ? "url(#glow-cyan)" : "none"}
              />
            </g>
          );
        })}

        {/* Entry price line */}
        {position && (
          <>
            <line
              x1={50}
              y1={priceToY(position.entryPrice)}
              x2={chartWidth}
              y2={priceToY(position.entryPrice)}
              stroke={position.type === 'long' ? 'hsl(145, 65%, 45%)' : 'hsl(0, 72%, 55%)'}
              strokeWidth={2}
              strokeDasharray="8,4"
              opacity={0.8}
            />
            <rect
              x={50}
              y={priceToY(position.entryPrice) - 10}
              width={80}
              height={20}
              fill={position.type === 'long' ? 'hsl(145, 65%, 45%)' : 'hsl(0, 72%, 55%)'}
              opacity={0.9}
              rx={3}
            />
            <text
              x={90}
              y={priceToY(position.entryPrice) + 4}
              fill="white"
              fontSize="10"
              fontFamily="monospace"
              fontWeight="bold"
              textAnchor="middle"
            >
              ENTRY ${position.entryPrice.toFixed(0)}
            </text>
          </>
        )}

        {/* Current price line */}
        <line
          x1={50}
          y1={priceToY(currentPrice)}
          x2={chartWidth}
          y2={priceToY(currentPrice)}
          stroke="hsl(175, 80%, 50%)"
          strokeWidth={1}
          strokeDasharray="3,3"
          filter="url(#glow-cyan)"
        />
        <rect
          x={chartWidth - 70}
          y={priceToY(currentPrice) - 10}
          width={65}
          height={20}
          fill="hsl(175, 80%, 50%)"
          rx={3}
        />
        <text
          x={chartWidth - 37}
          y={priceToY(currentPrice) + 4}
          fill="hsl(220, 20%, 10%)"
          fontSize="11"
          fontFamily="monospace"
          fontWeight="bold"
          textAnchor="middle"
        >
          ${currentPrice.toFixed(0)}
        </text>
      </svg>

      {/* P&L indicator */}
      {position && pnl !== 0 && (
        <div className={`absolute top-2 left-2 px-3 py-2 rounded border ${
          pnl > 0 ? 'bg-green-600/20 border-green-600 text-green-600' : 'bg-red-600/20 border-red-600 text-red-600'
        }`}>
          <div className="text-xs font-semibold">
            {pnl > 0 ? '+' : ''}${pnl.toFixed(0)}
          </div>
          <div className="text-[10px] opacity-80">
            {((pnl / position.size) * 100).toFixed(1)}%
          </div>
        </div>
      )}

      {/* Confluence indicator */}
      {glowingLevel && (
        <div className="absolute top-2 right-2 px-3 py-1.5 bg-primary/20 border border-primary rounded text-primary text-xs font-bold">
          <div className="flex items-center gap-2">
            <span className="text-base">⚡</span>
            <div>
              <div className="font-bold">{glowingLevel.label}</div>
              <div className="text-[10px] opacity-80">Fib Level</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
