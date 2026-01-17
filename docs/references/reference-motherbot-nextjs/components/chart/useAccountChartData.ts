// app/motherbot/components/chart/useAccountChartData.ts
import { useMemo } from "react";
import { TimeFrame, ChartDataPoint, ProcessedChartData } from "./types";
import { parseISO, isAfter, subHours, subDays } from "date-fns";

// Current prices for buy-and-hold comparison
const CURRENT_PRICES: Record<string, number> = {
  BTC: 95000,
  ETH: 3500,
  SOL: 185,
  AVAX: 42,
  LINK: 22,
  UNI: 12,
  AAVE: 280,
  DOGE: 0.35,
};

// Time frame filters
const TIME_FRAME_FILTERS = {
  "1h": (timestamp: number) => isAfter(timestamp, subHours(new Date(), 1)),
  "6h": (timestamp: number) => isAfter(timestamp, subHours(new Date(), 6)),
  "1d": (timestamp: number) => isAfter(timestamp, subDays(new Date(), 1)),
  "7d": (timestamp: number) => isAfter(timestamp, subDays(new Date(), 7)),
  "30d": (timestamp: number) => isAfter(timestamp, subDays(new Date(), 30)),
  all: () => true,
};

// Date format based on timeframe
const TIME_FRAME_FORMATS = {
  "1h": "time", // HH:mm
  "6h": "time", // HH:mm
  "1d": "datetime", // MMM d, HH:mm
  "7d": "datetime", // MMM d, HH:mm
  "30d": "date", // MMM d
  all: "date", // MMM d
};

// Calculate tick interval to prevent duplicate labels
const calculateTickInterval = (dataLength: number): number => {
  if (dataLength <= 5) return 0; // Show all ticks
  if (dataLength <= 10) return 1; // Show every other tick
  if (dataLength <= 20) return Math.floor(dataLength / 10); // Show ~10 ticks
  if (dataLength <= 50) return Math.floor(dataLength / 8); // Show ~8 ticks
  return Math.floor(dataLength / 6); // Show ~6 ticks for large datasets
};

// Generate buy-and-hold comparison data
const generateBuyAndHoldData = (
  accountHistory: any[],
  coin: string
): ChartDataPoint[] => {
  if (accountHistory.length === 0) return [];

  const startBalance = accountHistory[0]?.balance_usd || 1000;
  const currentPrice = CURRENT_PRICES[coin] || 50;
  const priceMultiplier = 0.85; // 15% appreciation
  const startingPrice = currentPrice * priceMultiplier;

  return accountHistory.map((point, index) => {
    const progress = index / (accountHistory.length - 1 || 1);
    const priceAtTime = startingPrice + (progress * (currentPrice - startingPrice));
    const buyAndHoldBalance = startBalance * (priceAtTime / startingPrice);

    return {
      timestamp: point.timestamp,
      balance: point.balance_usd,
      buyAndHold: buyAndHoldBalance,
    };
  });
};

export const useAccountChartData = (
  accountHistory: any[],
  selectedPair: string,
  timeFrame: TimeFrame = "all"
): ProcessedChartData => {
  return useMemo(() => {
    if (accountHistory.length === 0) {
      return {
        points: [],
        timeFrame,
        tickInterval: 0,
        dateFormat: TIME_FRAME_FORMATS[timeFrame],
      };
    }

    // Reverse to get chronological order (oldest first)
    const chronologicalHistory = [...accountHistory].reverse();

    // Filter by timeframe
    const filter = TIME_FRAME_FILTERS[timeFrame];
    const filteredHistory = chronologicalHistory.filter((point) => {
      const pointTime = parseISO(point.timestamp).getTime();
      return filter(pointTime);
    });

    // Generate chart data
    let points: ChartDataPoint[];
    if (selectedPair === "ALL") {
      // Show actual account balance over time
      points = filteredHistory.map(point => ({
        timestamp: point.timestamp,
        balance: point.balance_usd || point.equity_usd || 0,
      }));
    } else {
      // Show account balance vs buy-and-hold for selected coin
      const coin = selectedPair.split('/')[0];
      points = generateBuyAndHoldData(filteredHistory, coin);
    }

    // Calculate tick interval
    const tickInterval = calculateTickInterval(points.length);

    return {
      points,
      timeFrame,
      tickInterval,
      dateFormat: TIME_FRAME_FORMATS[timeFrame],
    };
  }, [accountHistory, selectedPair, timeFrame]);
};
