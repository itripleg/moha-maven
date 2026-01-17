// app/motherbot/components/PerformanceMetrics.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useBotPositions } from "../hooks/useBotPositions";
import { useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  Target,
  Zap,
  Award,
} from "lucide-react";
import type { PerformanceMetrics as PerformanceMetricsType } from "../types";

export function PerformanceMetrics() {
  const { positions: closedPositions, loading } = useBotPositions("closed");

  const metrics: PerformanceMetricsType = useMemo(() => {
    if (!closedPositions || closedPositions.length === 0) {
      return {
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        win_rate: 0,
        avg_win: 0,
        avg_loss: 0,
        profit_factor: 0,
        max_drawdown: 0,
        max_drawdown_percent: 0,
        sharpe_ratio: null,
        sortino_ratio: null,
        current_streak: 0,
        best_trade: 0,
        worst_trade: 0,
      };
    }

    const wins = closedPositions.filter((p) => (p.realized_pnl || 0) > 0);
    const losses = closedPositions.filter((p) => (p.realized_pnl || 0) < 0);

    const totalWins = wins.reduce((sum, p) => sum + (p.realized_pnl || 0), 0);
    const totalLosses = Math.abs(
      losses.reduce((sum, p) => sum + (p.realized_pnl || 0), 0)
    );

    const pnls = closedPositions.map((p) => p.realized_pnl || 0);
    const bestTrade = Math.max(...pnls, 0);
    const worstTrade = Math.min(...pnls, 0);

    return {
      total_trades: closedPositions.length,
      winning_trades: wins.length,
      losing_trades: losses.length,
      win_rate: (wins.length / closedPositions.length) * 100,
      avg_win: wins.length > 0 ? totalWins / wins.length : 0,
      avg_loss: losses.length > 0 ? totalLosses / losses.length : 0,
      profit_factor: totalLosses > 0 ? totalWins / totalLosses : 0,
      max_drawdown: 0, // TODO: Calculate from balance history
      max_drawdown_percent: 0,
      sharpe_ratio: null, // TODO: Calculate
      sortino_ratio: null, // TODO: Calculate
      current_streak: 0, // TODO: Calculate from recent trades
      best_trade: bestTrade,
      worst_trade: worstTrade,
    };
  }, [closedPositions]);

  if (loading) {
    return (
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Award className="h-3.5 w-3.5 text-primary" />
            Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-[150px]" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Award className="h-3.5 w-3.5 text-primary" />
          Performance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {/* Win Rate */}
        <div className="p-1.5 rounded-md bg-primary/5 border border-primary/20">
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-[9px] text-muted-foreground uppercase tracking-wide">
              Win Rate
            </span>
            <Target className="h-3 w-3 text-primary" />
          </div>
          <p className="text-base font-bold text-primary">
            {metrics.win_rate.toFixed(1)}%
          </p>
          <p className="text-[9px] text-muted-foreground">
            {metrics.winning_trades}W / {metrics.losing_trades}L
          </p>
        </div>

        {/* Profit Factor */}
        <div className="grid grid-cols-2 gap-1.5">
          <div className="p-1.5 rounded-md bg-muted/20">
            <p className="text-[9px] text-muted-foreground uppercase tracking-wide mb-0.5">
              Profit Factor
            </p>
            <p className="text-xs font-bold">
              {metrics.profit_factor > 0 ? metrics.profit_factor.toFixed(2) : "N/A"}
            </p>
          </div>
          <div className="p-1.5 rounded-md bg-muted/20">
            <p className="text-[9px] text-muted-foreground uppercase tracking-wide mb-0.5">
              Total Trades
            </p>
            <p className="text-xs font-bold">{metrics.total_trades}</p>
          </div>
        </div>

        {/* Avg Win/Loss */}
        <div className="grid grid-cols-2 gap-1.5">
          <div className="p-1.5 rounded-md bg-green-500/5 border border-green-500/20">
            <div className="flex items-center gap-1 mb-0.5">
              <TrendingUp className="h-2.5 w-2.5 text-green-500" />
              <p className="text-[9px] text-green-600 dark:text-green-400 uppercase tracking-wide">
                Avg Win
              </p>
            </div>
            <p className="text-xs font-bold text-green-500">
              ${metrics.avg_win.toFixed(2)}
            </p>
          </div>
          <div className="p-1.5 rounded-md bg-red-500/5 border border-red-500/20">
            <div className="flex items-center gap-1 mb-0.5">
              <TrendingDown className="h-2.5 w-2.5 text-red-500" />
              <p className="text-[9px] text-red-600 dark:text-red-400 uppercase tracking-wide">
                Avg Loss
              </p>
            </div>
            <p className="text-xs font-bold text-red-500">
              ${metrics.avg_loss.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Best/Worst Trade */}
        <div className="grid grid-cols-2 gap-1.5">
          <div className="p-1.5 rounded-md bg-muted/20">
            <p className="text-[9px] text-muted-foreground uppercase tracking-wide mb-0.5">
              Best Trade
            </p>
            <p className="text-xs font-bold text-green-500">
              +${metrics.best_trade.toFixed(2)}
            </p>
          </div>
          <div className="p-1.5 rounded-md bg-muted/20">
            <p className="text-[9px] text-muted-foreground uppercase tracking-wide mb-0.5">
              Worst Trade
            </p>
            <p className="text-xs font-bold text-red-500">
              ${metrics.worst_trade.toFixed(2)}
            </p>
          </div>
        </div>

        {metrics.total_trades === 0 && (
          <div className="p-1.5 rounded-md bg-muted/20 text-center">
            <p className="text-[9px] text-muted-foreground">
              No trades yet. Metrics will appear once trading begins.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
