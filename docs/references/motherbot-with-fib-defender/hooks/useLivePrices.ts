// app/motherbot/hooks/useLivePrices.ts
"use client";

import { useState, useEffect, useCallback } from "react";
import type { HLNetwork } from "@/types/hyperliquid";

interface LivePricesData {
  network: HLNetwork;
  timestamp: string;
  prices: Record<string, string>;
}

interface UseLivePricesReturn {
  prices: Record<string, string>;
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
  refresh: () => Promise<void>;
}


const POLL_INTERVAL = 3000; // 3 seconds - safe for public market data


export function useLivePrices(network: HLNetwork = "testnet"): UseLivePricesReturn {
  const [prices, setPrices] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const fetchPrices = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`/api/hl_debug/prices?network=${network}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch prices: ${response.statusText}`);
      }

      const data: LivePricesData = await response.json();
      setPrices(data.prices);
      setLastUpdate(data.timestamp);
      setLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(errorMessage);
      setLoading(false);
      console.error("[useLivePrices] Error:", err);
    }
  }, [network]);

  // Initial fetch
  useEffect(() => {
    fetchPrices();
  }, [fetchPrices]);

  // Poll every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchPrices();
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [fetchPrices]);

  return {
    prices,
    loading,
    error,
    lastUpdate,
    refresh: fetchPrices,
  };
}

/**
 * Get price for a specific coin from the prices map
 */
export function getPriceForCoin(
  prices: Record<string, string>,
  coin: string
): number | null {
  // Handle both "BTC" and "BTC/USDC:USDC" formats
  const cleanCoin = coin.split("/")[0];
  const priceStr = prices[cleanCoin];

  if (!priceStr) return null;

  const price = parseFloat(priceStr);
  return isNaN(price) ? null : price;
}
