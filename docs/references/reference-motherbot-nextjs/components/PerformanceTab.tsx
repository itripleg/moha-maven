// app/motherbot/components/PerformanceTab.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  Target,
  Award,
} from "lucide-react";
import { useBotPositions } from "../hooks/useBotPositions";
import { useBotAccount } from "../hooks/useBotAccount";
import { BalanceGraph } from "./BalanceGraph";
import type { PerformanceMetrics as PerformanceMetricsType, BalanceHistoryPoint } from "../types";

interface PerformanceTabProps {
  selectedPair?: string;
}

export function PerformanceTab({ selectedPair }: PerformanceTabProps) {
  const { positions: closedPositions, loading: loadingClosed } = useBotPositions("closed");
  const { positions: openPositions, loading: loadingOpen } = useBotPositions("open");
  const { account, loading: loadingAccount } = useBotAccount();

  // Filter positions
  const filteredClosed = selectedPair && selectedPair !== "ALL"
    ? closedPositions.filter(p => p.coin === selectedPair)
    : closedPositions;

  const filteredOpen = selectedPair && selectedPair !== "ALL"
    ? openPositions.filter(p => p.coin === selectedPair)
    : openPositions;

  const metrics: PerformanceMetricsType = useMemo(() => {
    if (!filteredClosed || filteredClosed.length === 0) {
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

    const wins = filteredClosed.filter((p) => (p.realized_pnl || 0) > 0);
    const losses = filteredClosed.filter((p) => (p.realized_pnl || 0) < 0);

    const totalWins = wins.reduce((sum, p) => sum + (p.realized_pnl || 0), 0);
    const totalLosses = Math.abs(
      losses.reduce((sum, p) => sum + (p.realized_pnl || 0), 0)
    );

    const pnls = filteredClosed.map((p) => p.realized_pnl || 0);
    const bestTrade = Math.max(...pnls, 0);
    const worstTrade = Math.min(...pnls, 0);

    return {
      total_trades: filteredClosed.length,
      winning_trades: wins.length,
      losing_trades: losses.length,
      win_rate: (wins.length / filteredClosed.length) * 100,
      avg_win: wins.length > 0 ? totalWins / wins.length : 0,
      avg_loss: losses.length > 0 ? totalLosses / losses.length : 0,
      profit_factor: totalLosses > 0 ? totalWins / totalLosses : 0,
      max_drawdown: 0,
      max_drawdown_percent: 0,
      sharpe_ratio: null,
      sortino_ratio: null,
      current_streak: 0,
      best_trade: bestTrade,
      worst_trade: worstTrade,
    };
  }, [filteredClosed]);

  // Mock balance history
  const balanceHistory: BalanceHistoryPoint[] = account
    ? [
        {
          timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
          balance_usd: 1000,
          equity_usd: 1000,
          total_pnl: 0,
        },
        {
          timestamp: new Date().toISOString(),
          balance_usd: account.balance_usd,
          equity_usd: account.equity_usd,
          total_pnl: account.total_pnl,
        },
      ]
    : [];

  if (loadingClosed || loadingOpen || loadingAccount) {
    return (
      <div className="space-y-4">
        <Skeleton className="w-full h-[300px]" />
        <Skeleton className="w-full h-[200px]" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Balance Graph */}
      <BalanceGraph data={balanceHistory} loading={loadingAccount} />

      {/* Performance Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Win Rate */}
        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                Win Rate
              </span>
              <Target className="h-3 w-3 text-primary" />
            </div>
            <p className="text-xl font-bold text-primary">
              {metrics.win_rate.toFixed(1)}%
            </p>
            <p className="text-[10px] text-muted-foreground">
              {metrics.winning_trades}W / {metrics.losing_trades}L
            </p>
          </CardContent>
        </Card>

        {/* Profit Factor */}
        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                Profit Factor
              </span>
              <Award className="h-3 w-3 text-primary" />
            </div>
            <p className="text-xl font-bold">
              {metrics.profit_factor > 0 ? metrics.profit_factor.toFixed(2) : "N/A"}
            </p>
            <p className="text-[10px] text-muted-foreground">
              {metrics.total_trades} trades
            </p>
          </CardContent>
        </Card>

        {/* Avg Win */}
        <Card className="bg-green-500/5 backdrop-blur-sm border-green-500/40">
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-green-600 dark:text-green-400 uppercase tracking-wide">
                Avg Win
              </span>
              <TrendingUp className="h-3 w-3 text-green-500" />
            </div>
            <p className="text-xl font-bold text-green-500">
              ${metrics.avg_win.toFixed(2)}
            </p>
            <p className="text-[10px] text-muted-foreground">
              Best: +${metrics.best_trade.toFixed(2)}
            </p>
          </CardContent>
        </Card>

        {/* Avg Loss */}
        <Card className="bg-red-500/5 backdrop-blur-sm border-red-500/40">
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-red-600 dark:text-red-400 uppercase tracking-wide">
                Avg Loss
              </span>
              <TrendingDown className="h-3 w-3 text-red-500" />
            </div>
            <p className="text-xl font-bold text-red-500">
              ${metrics.avg_loss.toFixed(2)}
            </p>
            <p className="text-[10px] text-muted-foreground">
              Worst: ${metrics.worst_trade.toFixed(2)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Positions - Open & Closed */}
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="open" className="w-full">
            <TabsList className="grid w-full grid-cols-2 h-8 mb-2">
              <TabsTrigger value="open" className="text-xs">
                Open ({filteredOpen.length})
              </TabsTrigger>
              <TabsTrigger value="closed" className="text-xs">
                Closed ({filteredClosed.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="open" className="mt-0">
              {filteredOpen.length === 0 ? (
                <div className="text-center py-6 text-xs text-muted-foreground">
                  No open positions
                </div>
              ) : (
                <div className="space-y-1 max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
                  <div className="grid grid-cols-6 gap-2 px-2 py-1 text-[10px] font-semibold text-muted-foreground border-b border-border sticky top-0 bg-card/30 backdrop-blur-sm">
                    <div>COIN</div>
                    <div>SIDE</div>
                    <div>SIZE</div>
                    <div>ENTRY</div>
                    <div>CURRENT</div>
                    <div className="text-right">P&L</div>
                  </div>
                  {filteredOpen.map((position) => {
                    const isPnlPositive = (position.unrealized_pnl || 0) >= 0;
                    return (
                      <div
                        key={position.id}
                        className="grid grid-cols-6 gap-2 items-center px-2 py-1.5 rounded bg-secondary/20 hover:bg-secondary/30 transition-colors"
                      >
                        <div className="font-semibold text-xs">{position.coin}</div>
                        <div className="flex items-center gap-1">
                          {position.side === "long" ? (
                            <TrendingUp className="w-3 h-3 text-green-500" />
                          ) : (
                            <TrendingDown className="w-3 h-3 text-red-500" />
                          )}
                          <span className="text-[10px]">{position.side.toUpperCase()}</span>
                        </div>
                        <div className="font-mono text-[10px]">
                          ${(position.quantity_usd ?? 0).toFixed(0)}
                        </div>
                        <div className="font-mono text-[10px]">
                          ${(position.entry_price ?? 0).toFixed(2)}
                        </div>
                        <div className="font-mono text-[10px]">
                          ${(position.current_price ?? 0).toFixed(2)}
                        </div>
                        <div className={`font-semibold text-[10px] text-right ${isPnlPositive ? "text-green-500" : "text-red-500"}`}>
                          {isPnlPositive ? "+" : ""}${(position.unrealized_pnl ?? 0).toFixed(2)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </TabsContent>

            <TabsContent value="closed" className="mt-0">
              {filteredClosed.length === 0 ? (
                <div className="text-center py-6 text-xs text-muted-foreground">
                  No closed positions
                </div>
              ) : (
                <div className="space-y-1 max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
                  <div className="grid grid-cols-6 gap-2 px-2 py-1 text-[10px] font-semibold text-muted-foreground border-b border-border sticky top-0 bg-card/30 backdrop-blur-sm">
                    <div>COIN</div>
                    <div>SIDE</div>
                    <div>SIZE</div>
                    <div>ENTRY</div>
                    <div>EXIT</div>
                    <div className="text-right">P&L</div>
                  </div>
                  {filteredClosed.map((position) => {
                    const isPnlPositive = (position.realized_pnl || 0) >= 0;
                    return (
                      <div
                        key={position.id}
                        className="grid grid-cols-6 gap-2 items-center px-2 py-1.5 rounded bg-secondary/20 hover:bg-secondary/30 transition-colors"
                      >
                        <div className="font-semibold text-xs">{position.coin}</div>
                        <div className="flex items-center gap-1">
                          {position.side === "long" ? (
                            <TrendingUp className="w-3 h-3 text-green-500" />
                          ) : (
                            <TrendingDown className="w-3 h-3 text-red-500" />
                          )}
                          <span className="text-[10px]">{position.side.toUpperCase()}</span>
                        </div>
                        <div className="font-mono text-[10px]">
                          ${(position.quantity_usd ?? 0).toFixed(0)}
                        </div>
                        <div className="font-mono text-[10px]">
                          ${(position.entry_price ?? 0).toFixed(2)}
                        </div>
                        <div className="font-mono text-[10px]">
                          ${(position.exit_price ?? 0).toFixed(2)}
                        </div>
                        <div className={`font-semibold text-[10px] text-right ${isPnlPositive ? "text-green-500" : "text-red-500"}`}>
                          {isPnlPositive ? "+" : ""}${(position.realized_pnl ?? 0).toFixed(2)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
