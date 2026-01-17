// app/motherbot/components/PositionsAndDecisions.tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Activity, TrendingUp, TrendingDown, Brain } from "lucide-react";
import { useBotPositions } from "../hooks/useBotPositions";
import { useBotDecisions } from "../hooks/useBotDecisions";
import type { BotPosition, BotDecision } from "../types";

interface PositionsAndDecisionsProps {
  selectedPair?: string;
}

function PositionRow({ position }: { position: BotPosition }) {
  const isOpen = position.status === "open";
  const isPnlPositive = isOpen
    ? (position.unrealized_pnl || 0) >= 0
    : (position.realized_pnl || 0) >= 0;
  const pnl = isOpen ? position.unrealized_pnl : position.realized_pnl;

  return (
    <div className="grid grid-cols-4 gap-2 items-center py-2 px-2 border-b border-border/30 hover:bg-accent/10 transition-colors text-xs">
      <div className="font-semibold">{position.coin}</div>
      <div className="flex items-center gap-1">
        {position.side === "long" ? (
          <TrendingUp className="w-3 h-3 text-green-500" />
        ) : (
          <TrendingDown className="w-3 h-3 text-red-500" />
        )}
        <span className="font-mono text-[10px]">${(position.quantity_usd ?? 0).toFixed(0)}</span>
      </div>
      <div className="font-mono text-[10px]">${(position.entry_price ?? 0).toFixed(2)}</div>
      <div className={`font-semibold text-right ${isPnlPositive ? "text-green-500" : "text-red-500"}`}>
        <span className="text-xs">${Math.abs(pnl ?? 0).toFixed(2)}</span>
      </div>
    </div>
  );
}

function DecisionRow({ decision }: { decision: BotDecision }) {
  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "buy_to_enter": return "text-green-500";
      case "sell_to_enter": return "text-red-500";
      case "hold": return "text-blue-500";
      case "close": return "text-yellow-500";
      default: return "text-gray-500";
    }
  };

  return (
    <div className="p-2 border border-border/30 rounded-lg hover:border-primary/30 transition-colors bg-card/50">
      <div className="flex items-center justify-between mb-1">
        <div className="font-semibold text-xs">{decision.coin}</div>
        <span className={`text-[10px] font-semibold ${getSignalColor(decision.signal)}`}>
          {decision.signal.replace("_", " ").toUpperCase()}
        </span>
      </div>
      <div className="text-[10px] text-muted-foreground line-clamp-2">{decision.justification}</div>
    </div>
  );
}

export function PositionsAndDecisions({ selectedPair }: PositionsAndDecisionsProps) {
  const [activeTab, setActiveTab] = useState<"positions" | "decisions">("positions");
  const { positions: openPositions, loading: loadingPositions } = useBotPositions("open");
  const { decisions, loading: loadingDecisions } = useBotDecisions(10, selectedPair && selectedPair !== "ALL" ? selectedPair : undefined);

  const filteredPositions = selectedPair && selectedPair !== "ALL"
    ? openPositions.filter(p => p.coin === selectedPair)
    : openPositions;

  return (
    <Card className="bg-card/30 backdrop-blur-sm border-primary/40 h-[400px] flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Activity className="h-3.5 w-3.5 text-primary" />
          Activity
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden flex flex-col p-3">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-2 mb-2 h-8">
            <TabsTrigger value="positions" className="text-xs">
              Positions ({filteredPositions.length})
            </TabsTrigger>
            <TabsTrigger value="decisions" className="text-xs">
              AI Decisions ({decisions.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="positions" className="mt-0 flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
            {loadingPositions ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-12" />
                ))}
              </div>
            ) : filteredPositions.length === 0 ? (
              <div className="text-center py-8 text-xs text-muted-foreground">
                No open positions
              </div>
            ) : (
              <div>
                <div className="grid grid-cols-4 gap-2 px-2 py-1 text-[10px] font-semibold text-muted-foreground border-b border-border">
                  <div>COIN</div>
                  <div>SIDE/SIZE</div>
                  <div>ENTRY</div>
                  <div className="text-right">P&L</div>
                </div>
                {filteredPositions.map((position) => (
                  <PositionRow key={position.id} position={position} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="decisions" className="mt-0 flex-1 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
            {loadingDecisions ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : decisions.length === 0 ? (
              <div className="text-center py-8 text-xs text-muted-foreground">
                No trading decisions yet
              </div>
            ) : (
              decisions.map((decision) => (
                <DecisionRow key={decision.id} decision={decision} />
              ))
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
