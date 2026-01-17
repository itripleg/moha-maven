// app/motherbot/components/layout/MotherBotHeader.tsx
"use client";

/**
 * FUTURE TRADING PARADIGMS (AI-Paired Trading)
 * 
 * The following trading modes will require separate balance tracking:
 * 
 * 1. INDEPENDENT (current): Bot trades autonomously on its own whim
 *    - Wallet: Bot's own wallet
 *    - Balance tracking: Bot balance only
 * 
 * 2. SHADOW: Bot trades alongside user, bolstering or reducing exposure
 *    - Wallet: Shared or separate
 *    - Balance tracking: Both bot and user balances
 *    - Bot mirrors user positions with size adjustments
 * 
 * 3. HEDGE: Bot takes opposite positions to give trader both sides
 *    - Wallet: Shared or separate
 *    - Balance tracking: Both bot and user balances
 *    - Bot automatically hedges user's positions
 * 
 * 4. EXIT MODE: Bot doesn't enter trades, only maximizes exits
 *    - Wallet: Shared (must see user's positions)
 *    - Balance tracking: Shared balance
 *    - Bot manages exit timing/pricing for user positions
 * 
 * 5. ENTER MODE: Bot doesn't exit trades, only finds optimal entries
 *    - Wallet: Shared (must see user's positions)
 *    - Balance tracking: Shared balance
 *    - Bot manages entry timing/pricing, user handles exits
 * 
 * Implementation requirements:
 * - Separate P&L tracking per strategy
 * - Position attribution (bot vs user)
 * - Allocation limits per strategy
 * - Real-time balance separation in header
 */

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useBotStatus } from "../../hooks/useBotStatus";
import { useBotAccount } from "../../hooks/useBotAccount";
import { useBotPositions } from "../../hooks/useBotPositions";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Cpu,
  Zap,
} from "lucide-react";
import type { BotStrategyMode } from "../../types";

interface MotherBotHeaderProps {
  strategyMode: BotStrategyMode;
  onStrategyModeChange: (mode: BotStrategyMode) => void;
}

export function MotherBotHeader({
  strategyMode,
  onStrategyModeChange,
}: MotherBotHeaderProps) {
  const { status, loading: statusLoading } = useBotStatus();
  const { account, loading: accountLoading } = useBotAccount();
  const { positions: openPositions } = useBotPositions("open");

  const isRunning = status?.status === "running";
  const totalPnl = account?.total_pnl || 0;
  const isProfitable = totalPnl >= 0;
  const numOpenPositions = openPositions.length;

  return (
    <div className="flex items-center justify-between p-4 bg-card/30 backdrop-blur-sm border border-primary/40 rounded-lg">
      {/* Title & Status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-primary/10 rounded-md border border-primary/20">
            <Cpu className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
              MotherBot
            </h1>
          </div>
        </div>

        {/* Status Badge */}
        <Badge
          variant={isRunning ? "default" : "secondary"}
          className={`gap-1 px-2 py-0.5 text-xs ${
            isRunning
              ? "bg-green-500/20 text-green-500 border-green-500/30"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {isRunning ? (
            <>
              <Zap className="h-2.5 w-2.5 animate-pulse" />
              Active
            </>
          ) : (
            <>
              <Activity className="h-2.5 w-2.5" />
              {status?.status || "Offline"}
            </>
          )}
        </Badge>
      </div>

      {/* Compact Stats */}
      <div className="flex items-center gap-6">
        {/* Balance */}
        <div className="flex items-center gap-2">
          <DollarSign className="h-3.5 w-3.5 text-primary/50" />
          <div>
            <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Balance</p>
            <p className="text-sm font-bold">${(account?.balance_usd || 0).toFixed(2)}</p>
          </div>
        </div>

        {/* Equity */}
        <div className="flex items-center gap-2">
          <Activity className="h-3.5 w-3.5 text-blue-500/50" />
          <div>
            <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Equity</p>
            <p className="text-sm font-bold">${(account?.equity_usd || 0).toFixed(2)}</p>
          </div>
        </div>

        {/* Total P&L */}
        <div className="flex items-center gap-2">
          {isProfitable ? (
            <TrendingUp className="h-3.5 w-3.5 text-green-500/50" />
          ) : (
            <TrendingDown className="h-3.5 w-3.5 text-red-500/50" />
          )}
          <div>
            <p className="text-[9px] text-muted-foreground uppercase tracking-wide">P&L</p>
            <p className={`text-sm font-bold ${isProfitable ? "text-green-500" : "text-red-500"}`}>
              {isProfitable ? "+" : ""}${totalPnl.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Open Positions */}
        <div className="flex items-center gap-2">
          <Activity className="h-3.5 w-3.5 text-purple-500/50" />
          <div>
            <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Positions</p>
            <p className="text-sm font-bold">{numOpenPositions}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
