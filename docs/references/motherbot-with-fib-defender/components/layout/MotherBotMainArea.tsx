// app/motherbot/components/layout/MotherBotMainArea.tsx
"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BotDataChart } from "../BotDataChart";
import { TAVisionChart } from "../TAVisionChart";
import { TradingViewWidget } from "../TradingViewWidget";
import { PairSelector } from "../PairSelector";
import { FibDefender } from "../FibDefender";
import {
  TrendingUp,
  Activity,
  BarChart3,
} from "lucide-react";
import type { BotStrategyMode } from "../../types";

interface MotherBotMainAreaProps {
  strategyMode: BotStrategyMode;
  selectedPair: string;
  onSelectPair: (pair: string) => void;
}

export function MotherBotMainArea({
  strategyMode,
  selectedPair,
  onSelectPair,
}: MotherBotMainAreaProps) {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="space-y-4">
      {/* Pair Selector */}
      <PairSelector
        selectedPair={selectedPair}
        onSelectPair={onSelectPair}
        network="testnet"
      />

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 h-9 bg-card/30 border border-primary/40">
          <TabsTrigger value="overview" className="gap-1.5 text-xs">
            <BarChart3 className="h-3.5 w-3.5" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="ta-vision" className="gap-1.5 text-xs">
            <Activity className="h-3.5 w-3.5" />
            TA Vision
          </TabsTrigger>
          <TabsTrigger value="tradingview" className="gap-1.5 text-xs">
            <TrendingUp className="h-3.5 w-3.5" />
            TradingView
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab - Historical Price Data */}
        <TabsContent value="overview" className="mt-4">
          <BotDataChart selectedPair={selectedPair} />
        </TabsContent>

        {/* TA Vision Tab - Technical Analysis or Fib Defender Game */}
        <TabsContent value="ta-vision" className="mt-4">
          {selectedPair === "ALL" ? (
            <FibDefender />
          ) : (
            <TAVisionChart selectedPair={selectedPair} />
          )}
        </TabsContent>

        {/* TradingView Tab - TradingView Widget */}
        <TabsContent value="tradingview" className="mt-4">
          <TradingViewWidget selectedPair={selectedPair} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
