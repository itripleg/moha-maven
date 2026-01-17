import { useState, useCallback, useEffect, useRef } from 'react';
import { Candle, GameState, Position, FibLevel, Timeframe, Leverage } from '@/types/game';

const INITIAL_BALANCE = 10000;
const TICKS_PER_CANDLE = 10;
const FIB_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
const FIB_COLORS = [
  'hsl(180, 100%, 50%)',
  'hsl(200, 100%, 55%)',
  'hsl(220, 100%, 60%)',
  'hsl(45, 100%, 55%)',
  'hsl(30, 100%, 55%)',
  'hsl(320, 100%, 60%)',
  'hsl(0, 100%, 60%)',
];

const generateTick = (prevPrice: number, volatility: number = 0.0008): number => {
  const change = (Math.random() - 0.5) * 2 * volatility * prevPrice;
  return prevPrice + change;
};

const createNewCandle = (price: number): Candle => ({
  time: Date.now(),
  open: price,
  high: price,
  low: price,
  close: price,
});

const updateCandleWithTick = (candle: Candle, newPrice: number): Candle => ({
  ...candle,
  high: Math.max(candle.high, newPrice),
  low: Math.min(candle.low, newPrice),
  close: newPrice,
});

const generateInitialCandles = (count: number, basePrice: number): Candle[] => {
  const candles: Candle[] = [];
  let price = basePrice;

  for (let i = 0; i < count; i++) {
    let candle = createNewCandle(price);
    // Simulate ticks for each historical candle
    for (let t = 0; t < TICKS_PER_CANDLE; t++) {
      price = generateTick(price);
      candle = updateCandleWithTick(candle, price);
    }
    candle.time = Date.now() - (count - i) * TICKS_PER_CANDLE * 100;
    candles.push(candle);
  }

  return candles;
};

const calculateRSI = (candles: Candle[], period: number = 14): number[] => {
  if (candles.length < period + 1) return [];

  const rsiValues: number[] = [];
  const changes = candles.slice(1).map((c, i) => c.close - candles[i].close);

  for (let i = period; i < changes.length; i++) {
    const periodChanges = changes.slice(i - period, i);
    const gains = periodChanges.filter(c => c > 0).reduce((a, b) => a + b, 0) / period;
    const losses = Math.abs(periodChanges.filter(c => c < 0).reduce((a, b) => a + b, 0)) / period;

    const rs = losses === 0 ? 100 : gains / losses;
    const rsi = 100 - (100 / (1 + rs));
    rsiValues.push(rsi);
  }

  return rsiValues;
};

const calculateMACD = (candles: Candle[]): { macd: number[]; signal: number[]; histogram: number[] } => {
  const closes = candles.map(c => c.close);

  const ema = (data: number[], period: number): number[] => {
    const k = 2 / (period + 1);
    const emaValues: number[] = [data[0]];
    for (let i = 1; i < data.length; i++) {
      emaValues.push(data[i] * k + emaValues[i - 1] * (1 - k));
    }
    return emaValues;
  };

  const ema12 = ema(closes, 12);
  const ema26 = ema(closes, 26);

  const macdLine = ema12.map((v, i) => v - ema26[i]);
  const signalLine = ema(macdLine.slice(25), 9);
  const histogram = macdLine.slice(25 + 8).map((v, i) => v - signalLine[i + 8]);

  return {
    macd: macdLine.slice(-20),
    signal: signalLine.slice(-20),
    histogram: histogram.slice(-20),
  };
};

export const useGameEngine = () => {
  const [candles, setCandles] = useState<Candle[]>(() => generateInitialCandles(60, 43000));
  const [gameState, setGameState] = useState<GameState>({
    balance: INITIAL_BALANCE,
    score: 0,
    position: null,
    isGameOver: false,
    pnl: 0,
    highScore: typeof window !== 'undefined'
      ? parseInt(localStorage.getItem('fibDefenderHighScore') || '0')
      : 0,
  });
  const [timeframe, setTimeframe] = useState<Timeframe>(1);
  const [leverage, setLeverage] = useState<Leverage>(10);
  const [fibLevels, setFibLevels] = useState<FibLevel[]>([]);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const tickCountRef = useRef<number>(0);

  const currentPrice = candles[candles.length - 1]?.close || 43000;

  const calculateFibLevels = useCallback((candleData: Candle[]): FibLevel[] => {
    const recentCandles = candleData.slice(-timeframe * 10);
    const high = Math.max(...recentCandles.map(c => c.high));
    const low = Math.min(...recentCandles.map(c => c.low));
    const range = high - low;
    const price = candleData[candleData.length - 1]?.close || 0;

    return FIB_LEVELS.map((level, index) => {
      const fibPrice = high - (range * level);
      const distance = Math.abs(price - fibPrice) / range;
      const isGlowing = distance < 0.05;

      return {
        level,
        price: fibPrice,
        label: level === 0 ? '0%' : level === 1 ? '100%' : `${(level * 100).toFixed(1)}%`,
        color: FIB_COLORS[index],
        isGlowing,
      };
    });
  }, [timeframe]);

  const calculatePnL = useCallback((position: Position | null, currentPrice: number): number => {
    if (!position) return 0;

    const priceDiff = currentPrice - position.entryPrice;
    const percentChange = priceDiff / position.entryPrice;
    const leveragedChange = percentChange * position.leverage;

    if (position.type === 'long') {
      return position.size * leveragedChange;
    } else {
      return position.size * -leveragedChange;
    }
  }, []);

  const openPosition = useCallback((type: 'long' | 'short') => {
    if (gameState.position || gameState.isGameOver) return;

    const size = gameState.balance * 0.5;
    const newPosition: Position = {
      type,
      entryPrice: currentPrice,
      leverage,
      size,
      timestamp: Date.now(),
    };

    setGameState(prev => ({
      ...prev,
      position: newPosition,
    }));
  }, [gameState.position, gameState.isGameOver, gameState.balance, currentPrice, leverage]);

  const closePosition = useCallback(() => {
    if (!gameState.position) return;

    const pnl = calculatePnL(gameState.position, currentPrice);
    const newBalance = gameState.balance + pnl;
    const newScore = gameState.score + Math.max(0, Math.floor(pnl));

    if (newBalance <= 0) {
      const newHighScore = Math.max(gameState.highScore, newScore);
      if (typeof window !== 'undefined') {
        localStorage.setItem('fibDefenderHighScore', newHighScore.toString());
      }

      setGameState(prev => ({
        ...prev,
        position: null,
        balance: 0,
        isGameOver: true,
        pnl: 0,
        score: newScore,
        highScore: newHighScore,
      }));
    } else {
      setGameState(prev => ({
        ...prev,
        position: null,
        balance: newBalance,
        pnl: 0,
        score: newScore,
      }));
    }
  }, [gameState, currentPrice, calculatePnL]);

  const resetGame = useCallback(() => {
    setCandles(generateInitialCandles(60, 43000));
    setGameState({
      balance: INITIAL_BALANCE,
      score: 0,
      position: null,
      isGameOver: false,
      pnl: 0,
      highScore: typeof window !== 'undefined'
        ? parseInt(localStorage.getItem('fibDefenderHighScore') || '0')
        : 0,
    });
  }, []);

  useEffect(() => {
    if (gameState.isGameOver) return;

    intervalRef.current = setInterval(() => {
      tickCountRef.current += 1;

      setCandles(prev => {
        const lastCandle = prev[prev.length - 1];
        const newPrice = generateTick(lastCandle.close);

        if (tickCountRef.current >= TICKS_PER_CANDLE) {
          // Start a new candle
          tickCountRef.current = 0;
          const newCandle = createNewCandle(newPrice);
          return [...prev.slice(-59), newCandle];
        } else {
          // Update the current candle with new tick
          const updatedCandle = updateCandleWithTick(lastCandle, newPrice);
          return [...prev.slice(0, -1), updatedCandle];
        }
      });
    }, 100);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [gameState.isGameOver]);

  useEffect(() => {
    setFibLevels(calculateFibLevels(candles));
  }, [candles, calculateFibLevels]);

  useEffect(() => {
    if (gameState.position) {
      const pnl = calculatePnL(gameState.position, currentPrice);
      const potentialBalance = gameState.balance + pnl;

      if (potentialBalance <= gameState.balance * -0.9) {
        const newHighScore = Math.max(gameState.highScore, gameState.score);
        if (typeof window !== 'undefined') {
          localStorage.setItem('fibDefenderHighScore', newHighScore.toString());
        }

        setGameState(prev => ({
          ...prev,
          isGameOver: true,
          position: null,
          balance: 0,
          pnl: 0,
          highScore: newHighScore,
        }));
      } else {
        setGameState(prev => ({ ...prev, pnl }));
      }
    }
  }, [currentPrice, gameState.position, gameState.balance, gameState.score, gameState.highScore, calculatePnL]);

  const rsi = calculateRSI(candles);
  const macd = calculateMACD(candles);

  return {
    candles,
    gameState,
    fibLevels,
    timeframe,
    leverage,
    currentPrice,
    rsi,
    macd,
    setTimeframe,
    setLeverage,
    openPosition,
    closePosition,
    resetGame,
  };
};
