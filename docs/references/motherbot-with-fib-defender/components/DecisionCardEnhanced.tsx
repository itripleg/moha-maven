// app/motherbot/components/DecisionCardEnhanced.tsx
"use client";

import { useState } from "react";
import { Brain, GitBranch, Shield, Zap, Scale, ShieldCheck, Gauge, TrendingUp, TrendingDown, ChevronDown } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { BotDecision } from "../types";

interface DecisionCardEnhancedProps {
  decision: BotDecision;
}

const STRATEGY_ICONS = {
  independent: { icon: Brain, label: "Independent", color: "text-primary" },
  shadow: { icon: GitBranch, label: "Shadow", color: "text-blue-500" },
  hedge: { icon: Shield, label: "Hedge", color: "text-green-500" },
};

const PRESET_ICONS = {
  aggressive_small_account: { icon: Zap, label: "Aggressive (<$20)", color: "text-red-500" },
  standard: { icon: Scale, label: "Standard Balanced", color: "text-yellow-500" },
  conservative: { icon: ShieldCheck, label: "Conservative", color: "text-green-500" },
};

export function DecisionCardEnhanced({ decision }: DecisionCardEnhancedProps) {
  const [showPnL, setShowPnL] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "buy_to_enter": return "text-green-500 bg-green-500/10 border-green-500/30";
      case "sell_to_enter": return "text-red-500 bg-red-500/10 border-red-500/30";
      case "hold": return "text-blue-500 bg-blue-500/10 border-blue-500/30";
      case "close": return "text-yellow-500 bg-yellow-500/10 border-yellow-500/30";
      default: return "text-gray-500 bg-gray-500/10 border-gray-500/30";
    }
  };

  const confidenceColor = decision.confidence >= 0.7
    ? "text-green-500"
    : decision.confidence >= 0.5
    ? "text-yellow-500"
    : "text-red-500";

  // Get strategy and preset info (with fallbacks)
  const strategyInfo = STRATEGY_ICONS[decision.strategy_mode || "independent"];
  const presetInfo = PRESET_ICONS[decision.prompt_preset || "aggressive_small_account"];

  // Mock P&L data - in production, fetch from positions based on decision.id
  const mockPnL = {
    unrealized: decision.execution_status === "success" ? (Math.random() - 0.5) * 50 : null,
    realized: decision.execution_status === "success" ? null : (Math.random() - 0.5) * 30,
  };

  const pnlValue = mockPnL.unrealized ?? mockPnL.realized ?? 0;
  const isPnlPositive = pnlValue >= 0;
  const pnlType = mockPnL.unrealized !== null ? "Unrealized" : "Realized";

  return (
    <div
      className="p-3 border border-border/30 rounded-lg hover:border-primary/30 transition-colors bg-card/50 relative"
      onMouseEnter={() => setShowPnL(true)}
      onMouseLeave={() => setShowPnL(false)}
    >
      {/* P&L Overlay on Hover */}
      {showPnL && decision.execution_status === "success" && (
        <div className="absolute inset-0 bg-background/95 backdrop-blur-sm rounded-lg flex flex-col items-center justify-center border-2 border-primary z-10">
          <div className="text-center">
            <p className="text-[10px] text-muted-foreground mb-1">{pnlType} P&L</p>
            <div className={`flex items-center justify-center gap-2 text-2xl font-bold ${isPnlPositive ? "text-green-500" : "text-red-500"}`}>
              {isPnlPositive ? (
                <TrendingUp className="h-5 w-5" />
              ) : (
                <TrendingDown className="h-5 w-5" />
              )}
              <span>{isPnlPositive ? "+" : ""}${Math.abs(pnlValue).toFixed(2)}</span>
            </div>
            <p className="text-[9px] text-muted-foreground mt-1">
              {((pnlValue / decision.quantity_usd) * 100).toFixed(1)}% return
            </p>
          </div>
        </div>
      )}

      {/* Header with Icons */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="font-semibold text-sm">{decision.coin}</div>

          {/* Strategy Icon */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="p-1 rounded bg-secondary/30 cursor-help">
                  <strategyInfo.icon className={`h-3 w-3 ${strategyInfo.color}`} />
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="z-50">
                <p className="text-xs">{strategyInfo.label} Mode</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* Preset Icon */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="p-1 rounded bg-secondary/30 cursor-help">
                  <presetInfo.icon className={`h-3 w-3 ${presetInfo.color}`} />
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="z-50">
                <p className="text-xs">{presetInfo.label}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* Leverage Icon */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="p-1 rounded bg-orange-500/20 cursor-help">
                  <Gauge className="h-3 w-3 text-orange-500" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="z-50">
                <div className="text-xs">
                  <p className="font-semibold">{decision.leverage}x Leverage</p>
                  <p className="text-[10px] text-muted-foreground">
                    ${(decision.quantity_usd * decision.leverage).toFixed(2)} notional
                  </p>
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${getSignalColor(decision.signal)}`}>
          {decision.signal.replace("_", " ").toUpperCase()}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2 text-xs">
        <div>
          <span className="text-[10px] text-muted-foreground">Size</span>
          <p className="font-mono">${(decision.quantity_usd ?? 0).toFixed(2)}</p>
        </div>
        <div>
          <span className="text-[10px] text-muted-foreground">Confidence</span>
          <p className={`font-mono font-semibold ${confidenceColor}`}>
            {((decision.confidence ?? 0) * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      <div className="text-xs">
        <div className="flex items-center justify-between mb-1">
          <p className="text-[10px] text-muted-foreground">Analysis</p>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-muted-foreground hover:text-primary transition-colors"
          >
            <ChevronDown className={`h-3 w-3 transition-transform ${isExpanded ? "rotate-180" : ""}`} />
          </button>
        </div>
        <p className={`text-muted-foreground ${
          isExpanded
            ? "max-h-[200px] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60 pr-2"
            : "line-clamp-3"
        }`}>
          {decision.justification}
        </p>
      </div>

      <div className="flex items-center justify-between mt-2">
        <div className="text-[9px] text-muted-foreground">
          {new Date(decision.timestamp).toLocaleTimeString()}
        </div>
        {decision.execution_status && (
          <div className={`text-[9px] px-1.5 py-0.5 rounded ${
            decision.execution_status === "success" ? "bg-green-500/20 text-green-500" :
            decision.execution_status === "failed" ? "bg-red-500/20 text-red-500" :
            decision.execution_status === "pending" ? "bg-yellow-500/20 text-yellow-500" :
            "bg-gray-500/20 text-gray-500"
          }`}>
            {decision.execution_status}
          </div>
        )}
      </div>
    </div>
  );
}
