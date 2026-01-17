"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { RefreshCw } from "lucide-react";
import { useLivePrices, getPriceForCoin } from "../hooks/useLivePrices";

export interface TradingPair {
  symbol: string;
  display: string;
}

const TRADING_PAIRS: TradingPair[] = [
  { symbol: "ALL", display: "All" }, // View all pairs
  { symbol: "BTC/USDC:USDC", display: "BTC" },
  { symbol: "ETH/USDC:USDC", display: "ETH" },
  { symbol: "SOL/USDC:USDC", display: "SOL" },
  { symbol: "ADA/USDC:USDC", display: "ADA" },
];

interface PairSelectorProps {
  selectedPair: string;
  onSelectPair: (pair: string) => void;
  network?: "testnet" | "mainnet";
}

export function PairSelector({ selectedPair, onSelectPair, network = "testnet" }: PairSelectorProps) {
  const { prices, loading, lastUpdate } = useLivePrices(network);
  const [previousPrices, setPreviousPrices] = React.useState<Record<string, number>>({});

  // Track price changes
  React.useEffect(() => {
    if (Object.keys(prices).length > 0 && !loading) {
      setPreviousPrices(prev => {
        const newPrices: Record<string, number> = {};
        Object.keys(prices).forEach(coin => {
          const price = parseFloat(prices[coin]);
          if (!isNaN(price)) {
            newPrices[coin] = price;
          }
        });
        return Object.keys(prev).length === 0 ? newPrices : prev;
      });
    }
  }, [prices, loading]);

  const formatPrice = (price: number | null): string => {
    if (price === null) return "---";

    // Format with commas and 2 decimal places
    return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const getPriceColor = (coin: string, currentPrice: number | null): string => {
    if (currentPrice === null || loading) return 'text-muted-foreground';
    
    const cleanCoin = coin.split("/")[0];
    const prevPrice = previousPrices[cleanCoin];
    
    if (!prevPrice || prevPrice === currentPrice) return 'text-foreground';
    
    return currentPrice > prevPrice ? 'text-green-500' : 'text-red-500';
  };

  const getTimeSinceUpdate = (): string => {
    if (!lastUpdate) return "";
    const seconds = Math.floor((Date.now() - new Date(lastUpdate).getTime()) / 1000);
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m`;
  };

  return (
    <div className="flex items-center justify-between gap-4 p-3 bg-card/30 backdrop-blur-sm border border-primary/40 rounded-lg">
      <div className="flex items-center gap-2">
        <div className="flex gap-1.5">
          {TRADING_PAIRS.map((pair) => {
            const isSelected = selectedPair === pair.symbol;
            const price = pair.symbol !== "ALL" ? getPriceForCoin(prices, pair.symbol) : null;

            return (
              <button
                key={pair.symbol}
                onClick={() => onSelectPair(pair.symbol)}
                className={`
                  px-3 py-1.5 rounded-md border transition-all text-sm font-medium
                  ${isSelected
                    ? 'border-primary bg-primary/20 text-primary'
                    : 'border-primary/30 hover:border-primary/50 hover:bg-primary/5 text-foreground'
                  }
                `}
              >
                <div className="flex items-center gap-2">
                  <span>{pair.display}</span>
                  {pair.symbol !== "ALL" && (
                    <span className={`text-[10px] font-mono font-semibold ${loading ? 'animate-pulse' : ''} ${getPriceColor(pair.symbol, price)}`}>
                      {formatPrice(price)}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Live Update Badge */}
      {lastUpdate && (
        <Badge variant="outline" className="text-[9px] px-2 py-1 border-primary/30 bg-primary/5">
          <RefreshCw className="h-2.5 w-2.5 mr-1" />
          {getTimeSinceUpdate()}
        </Badge>
      )}
    </div>
  );
}
