import { useState, useEffect } from 'react';

// Local type definitions (previously imported from non-existent @/types/trading)
export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BalancePoint {
  timestamp: Date;
  userBalance: number;
  botBalance: number;
}

export interface TAIndicators {
  rsi: number;
  macd: { value: number; signal: number; histogram: number };
  fib: {
    level236: number;
    level382: number;
    level500: number;
    level618: number;
    level786: number;
  };
  ema: {
    ema9: number;
    ema21: number;
    ema50: number;
  };
  volume: number;
  trend: string;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  timestamp: Date;
  owner: 'user' | 'bot';
}

export interface BotActivity {
  id: string;
  action: 'analysis' | 'buy' | 'sell' | 'hold';
  symbol: string;
  message: string;
  timestamp: Date;
  confidence?: number;
}

export type BotMode = 'independent' | 'shadow' | 'hedge' | 'exit' | 'enter';


const generateCandles = (count: number): CandleData[] => {
  const candles: CandleData[] = [];
  let price = 2450;
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const change = (Math.random() - 0.5) * 40;
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * 15;
    const low = Math.min(open, close) - Math.random() * 15;
    
    candles.push({
      time: now - (count - i) * 15 * 60 * 1000,
      open,
      high,
      low,
      close,
      volume: Math.random() * 1000 + 500
    });
    
    price = close;
  }
  return candles;
};

const generateBalanceHistory = (count: number): BalancePoint[] => {
  const points: BalancePoint[] = [];
  let userBalance = 10000;
  let botBalance = 10000;
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    userBalance += (Math.random() - 0.48) * 100;
    botBalance += (Math.random() - 0.45) * 100;
    
    points.push({
      timestamp: new Date(now - (count - i) * 15 * 60 * 1000),
      userBalance: Math.max(userBalance, 8000),
      botBalance: Math.max(botBalance, 8000)
    });
  }
  return points;
};

export function useMockData() {
  const [mode, setMode] = useState<BotMode>('shadow');
  const [candles, setCandles] = useState<CandleData[]>(generateCandles(100));
  const [balanceHistory, setBalanceHistory] = useState<BalancePoint[]>(generateBalanceHistory(50));
  
  const currentPrice = candles[candles.length - 1]?.close ?? 2450;
  
  const [indicators, setIndicators] = useState<TAIndicators>({
    rsi: 55,
    macd: { value: 12.5, signal: 10.2, histogram: 2.3 },
    fib: {
      level236: currentPrice * 0.98,
      level382: currentPrice * 0.97,
      level500: currentPrice * 0.96,
      level618: currentPrice * 0.95,
      level786: currentPrice * 0.93
    },
    ema: {
      ema9: currentPrice * 0.995,
      ema21: currentPrice * 0.99,
      ema50: currentPrice * 0.985
    },
    volume: 1250,
    trend: 'bullish'
  });

  const [positions] = useState<Position[]>([
    {
      id: '1',
      symbol: 'ETH-PERP',
      side: 'long',
      size: 2.5,
      entryPrice: 2420,
      currentPrice,
      pnl: (currentPrice - 2420) * 2.5,
      pnlPercent: ((currentPrice - 2420) / 2420) * 100,
      timestamp: new Date(),
      owner: 'user'
    },
    {
      id: '2',
      symbol: 'ETH-PERP',
      side: 'long',
      size: 1.8,
      entryPrice: 2425,
      currentPrice,
      pnl: (currentPrice - 2425) * 1.8,
      pnlPercent: ((currentPrice - 2425) / 2425) * 100,
      timestamp: new Date(),
      owner: 'bot'
    }
  ]);

  const [activities] = useState<BotActivity[]>([
    {
      id: '1',
      action: 'analysis',
      symbol: 'ETH-PERP',
      message: 'RSI showing oversold conditions. MACD histogram turning positive.',
      timestamp: new Date(Date.now() - 30000),
      confidence: 0.85
    },
    {
      id: '2',
      action: 'buy',
      symbol: 'ETH-PERP',
      message: 'Opening long position. Shadow mode: mirroring user with 0.7x size.',
      timestamp: new Date(Date.now() - 60000),
      confidence: 0.78
    },
    {
      id: '3',
      action: 'hold',
      symbol: 'ETH-PERP',
      message: 'Maintaining position. Fibonacci 0.618 support holding.',
      timestamp: new Date(Date.now() - 120000),
      confidence: 0.72
    },
    {
      id: '4',
      action: 'analysis',
      symbol: 'BTC-PERP',
      message: 'Scanning correlated assets for divergence signals.',
      timestamp: new Date(Date.now() - 180000)
    }
  ]);

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      setCandles(prev => {
        const lastCandle = prev[prev.length - 1];
        const change = (Math.random() - 0.5) * 10;
        const newClose = lastCandle.close + change;
        
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...lastCandle,
          close: newClose,
          high: Math.max(lastCandle.high, newClose),
          low: Math.min(lastCandle.low, newClose)
        };
        return updated;
      });

      setIndicators(prev => ({
        ...prev,
        rsi: Math.min(100, Math.max(0, prev.rsi + (Math.random() - 0.5) * 5)),
        macd: {
          ...prev.macd,
          histogram: prev.macd.histogram + (Math.random() - 0.5) * 0.5
        }
      }));
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  const latestBalances = balanceHistory[balanceHistory.length - 1];

  return {
    mode,
    setMode,
    candles,
    balanceHistory,
    indicators,
    positions,
    activities,
    userBalance: latestBalances?.userBalance ?? 10000,
    botBalance: latestBalances?.botBalance ?? 10000,
    totalPnL: (latestBalances?.userBalance ?? 10000) - 10000 + (latestBalances?.botBalance ?? 10000) - 10000,
    winRate: 67.5
  };
}
