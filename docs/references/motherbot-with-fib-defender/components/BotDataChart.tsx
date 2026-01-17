// app/motherbot/components/BotDataChart.tsx
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useState } from "react";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useBotPositions } from "../hooks/useBotPositions";
import { useBotAccount, useBotAccountHistory } from "../hooks/useBotAccount";
import { TrendingUp, TrendingDown, Activity, DollarSign, Target } from "lucide-react";
import { TimeFrameSelector } from "./chart/TimeFrameSelector";
import { useAccountChartData } from "./chart/useAccountChartData";
import { TimeFrame } from "./chart/types";
import { motion } from "framer-motion";

interface BotDataChartProps {
  selectedPair: string;
  loading?: boolean;
}

// Format price based on value
const formatPrice = (value: number): string => {
  if (value >= 1000) {
    return value.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }
  return value.toFixed(2);
};

const COIN_COLORS: Record<string, string> = {
  BTC: "#f7931a",
  ETH: "#627eea",
  SOL: "#14f195",
  DOGE: "#c2a633",
  AVAX: "#e84142",
  LINK: "#2a5ada",
  UNI: "#ff007a",
  AAVE: "#b6509e",
};

// Generate a color for any coin not in the predefined list
const getCoinColor = (coin: string): string => {
  if (COIN_COLORS[coin]) return COIN_COLORS[coin];

  // Generate a consistent color based on coin name
  let hash = 0;
  for (let i = 0; i < coin.length; i++) {
    hash = coin.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = hash % 360;
  return `hsl(${hue}, 70%, 50%)`;
};

// Enhanced custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="p-4 bg-background/95 backdrop-blur-md border border-primary/20 rounded-xl shadow-xl"
      >
        <p className="text-sm font-medium text-muted-foreground mb-2">
          {new Date(label).toLocaleString()}
        </p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 mb-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <p className="text-lg font-bold text-primary">
              ${entry.value.toFixed(2)}
            </p>
            <span className="text-xs text-muted-foreground ml-1">
              {entry.name === "balance" ? "Balance" : entry.dataKey}
            </span>
          </div>
        ))}
      </motion.div>
    );
  }
  return null;
};

export function BotDataChart({ selectedPair, loading = false }: BotDataChartProps) {
  const [timeFrame, setTimeFrame] = useState<TimeFrame>("all");
  const { positions: openPositions } = useBotPositions("open");
  const { positions: closedPositions } = useBotPositions("closed");
  const { account: accountValue, loading: accountLoading } = useBotAccount();
  const { history: accountHistory, loading: historyLoading } = useBotAccountHistory(100);

  const filteredOpen = selectedPair && selectedPair !== "ALL"
    ? openPositions.filter(p => p.coin === selectedPair.split('/')[0])
    : openPositions;

  const filteredClosed = selectedPair && selectedPair !== "ALL"
    ? closedPositions.filter(p => p.coin === selectedPair.split('/')[0]).slice(0, 5)
    : closedPositions.slice(0, 5);

  // Process chart data with timeframe
  const chartData = useAccountChartData(accountHistory, selectedPair, timeFrame);

  // Calculate analytics
  const analytics = {
    totalPnL: filteredOpen.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0) +
              filteredClosed.reduce((sum, p) => sum + (p.realized_pnl || 0), 0),
    openPositionsCount: filteredOpen.length,
    winRate: filteredClosed.length > 0
      ? (filteredClosed.filter(p => (p.realized_pnl || 0) > 0).length / filteredClosed.length) * 100
      : 0,
    currentBalance: accountValue?.equity_usd || 0,
    balanceChange: chartData.points.length >= 2
      ? ((chartData.points[chartData.points.length - 1].balance - chartData.points[0].balance) / chartData.points[0].balance) * 100
      : 0,
  };

  const primaryColor = "hsl(var(--primary))";

  if (loading || historyLoading) {
    return (
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardContent className="pt-6">
          <Skeleton className="w-full h-[500px]" />
        </CardContent>
      </Card>
    );
  }

  if (chartData.points.length === 0) {
    return (
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardContent className="pt-6">
          <div className="h-[500px] flex items-center justify-center text-muted-foreground text-sm">
            No account history available yet
          </div>
        </CardContent>
      </Card>
    );
  }

  const isComparison = selectedPair !== "ALL";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardContent className="pt-6">
          {/* Analytics Header */}
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
            {/* Current Balance and Change */}
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold text-primary">
                ${analytics.currentBalance.toFixed(2)}
              </div>
              {analytics.balanceChange !== 0 && (
                <Badge
                  variant="outline"
                  className={`flex items-center gap-1 ${
                    analytics.balanceChange > 0
                      ? "text-green-400 border-green-400/30 bg-green-400/10"
                      : "text-red-400 border-red-400/30 bg-red-400/10"
                  }`}
                >
                  {analytics.balanceChange > 0 ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  {analytics.balanceChange > 0 ? "+" : ""}
                  {analytics.balanceChange.toFixed(2)}%
                </Badge>
              )}
            </div>

            {/* Analytics Cards */}
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2 px-3 py-2 bg-primary/10 rounded-lg border border-primary/20">
                <Activity className="h-4 w-4 text-primary" />
                <div className="text-sm">
                  <span className="font-semibold text-foreground">
                    {analytics.openPositionsCount}
                  </span>
                  <span className="text-muted-foreground ml-1">Open</span>
                </div>
              </div>

              <div className="flex items-center gap-2 px-3 py-2 bg-primary/10 rounded-lg border border-primary/20">
                <DollarSign className="h-4 w-4 text-primary" />
                <div className="text-sm">
                  <span className={`font-semibold ${analytics.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {analytics.totalPnL >= 0 ? '+' : ''}${analytics.totalPnL.toFixed(2)}
                  </span>
                  <span className="text-muted-foreground ml-1">P&L</span>
                </div>
              </div>

              <div className="flex items-center gap-2 px-3 py-2 bg-primary/10 rounded-lg border border-primary/20">
                <Target className="h-4 w-4 text-primary" />
                <div className="text-sm">
                  <span className="font-semibold text-foreground">
                    {analytics.winRate.toFixed(0)}%
                  </span>
                  <span className="text-muted-foreground ml-1">Win Rate</span>
                </div>
              </div>
            </div>
          </div>

          {/* TimeFrame Selector */}
          <div className="mb-4 flex justify-end">
            <TimeFrameSelector
              currentTimeFrame={timeFrame}
              onTimeFrameChange={setTimeFrame}
            />
          </div>

          {/* Chart */}
          <div className="h-80 lg:h-96 p-6">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartData.points}
                margin={{ top: 10, right: 10, left: 0, bottom: 40 }}
              >
                <CartesianGrid
                  strokeDasharray="2 2"
                  stroke="hsl(var(--muted-foreground))"
                  strokeOpacity={0.1}
                />

                <defs>
                  <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={primaryColor} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={primaryColor} stopOpacity={0.05} />
                  </linearGradient>
                  {isComparison && (
                    <linearGradient id="comparisonGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={getCoinColor(selectedPair.split('/')[0])} stopOpacity={0.2} />
                      <stop offset="100%" stopColor={getCoinColor(selectedPair.split('/')[0])} stopOpacity={0.03} />
                    </linearGradient>
                  )}
                </defs>

                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    if (chartData.dateFormat === "time") {
                      return date.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      });
                    } else if (chartData.dateFormat === "datetime") {
                      return date.toLocaleDateString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      });
                    } else {
                      return date.toLocaleDateString([], {
                        month: "short",
                        day: "numeric",
                      });
                    }
                  }}
                  interval={chartData.tickInterval}
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  angle={-45}
                  textAnchor="end"
                  height={40}
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                />

                <YAxis
                  tickFormatter={(value) => `$${formatPrice(value)}`}
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  domain={["dataMin", "dataMax"]}
                  width={80}
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                />

                <Tooltip content={(props) => <CustomTooltip {...props} />} />

                {/* Gradient fill for balance */}
                <Area
                  type="monotone"
                  dataKey="balance"
                  stroke="none"
                  fill="url(#balanceGradient)"
                  fillOpacity={1}
                />

                {/* Balance line */}
                <Line
                  type="monotone"
                  dataKey="balance"
                  name="balance"
                  stroke={primaryColor}
                  strokeWidth={3}
                  dot={false}
                  activeDot={{
                    r: 6,
                    fill: "hsl(var(--background))",
                    stroke: primaryColor,
                    strokeWidth: 3,
                  }}
                  style={{ filter: `drop-shadow(0 2px 4px ${primaryColor}40)` }}
                />

                {/* Buy and Hold Comparison Line (only for specific coins) */}
                {isComparison && (
                  <>
                    <Area
                      type="monotone"
                      dataKey="buyAndHold"
                      stroke="none"
                      fill="url(#comparisonGradient)"
                      fillOpacity={1}
                    />
                    <Line
                      type="monotone"
                      dataKey="buyAndHold"
                      name={`${selectedPair.split('/')[0]} Buy & Hold`}
                      stroke={getCoinColor(selectedPair.split('/')[0])}
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                      activeDot={{
                        r: 5,
                        fill: "hsl(var(--background))",
                        stroke: getCoinColor(selectedPair.split('/')[0]),
                        strokeWidth: 2,
                      }}
                    />
                  </>
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Positions Display - Compact */}
          <div className="mt-6 grid grid-cols-2 gap-3">
            {/* Open Positions */}
            <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-primary flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  Open Positions
                </p>
                <Badge variant="secondary" className="text-[10px] h-5">
                  {filteredOpen.length}
                </Badge>
              </div>
              <div className="space-y-1">
                {filteredOpen.length === 0 ? (
                  <p className="text-[10px] text-muted-foreground">No open positions</p>
                ) : (
                  filteredOpen.slice(0, 3).map((pos) => {
                    const isPnlPositive = (pos.unrealized_pnl || 0) >= 0;
                    return (
                      <div key={pos.id} className="flex items-center justify-between text-[10px]">
                        <span className="font-semibold">{pos.coin}</span>
                        <span className="text-muted-foreground">{pos.side === "long" ? "↑" : "↓"} ${(pos.quantity_usd ?? 0).toFixed(0)}</span>
                        <span className={isPnlPositive ? "text-green-400" : "text-red-400"}>
                          {isPnlPositive ? "+" : ""}${(pos.unrealized_pnl ?? 0).toFixed(2)}
                        </span>
                      </div>
                    );
                  })
                )}
                {filteredOpen.length > 3 && (
                  <p className="text-[9px] text-muted-foreground pt-1">
                    +{filteredOpen.length - 3} more
                  </p>
                )}
              </div>
            </div>

            {/* Closed Positions */}
            <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-primary flex items-center gap-1">
                  <TrendingDown className="w-3 h-3" />
                  Recent Closed
                </p>
                <Badge variant="secondary" className="text-[10px] h-5">
                  {filteredClosed.length}
                </Badge>
              </div>
              <div className="space-y-1">
                {filteredClosed.length === 0 ? (
                  <p className="text-[10px] text-muted-foreground">No closed positions</p>
                ) : (
                  filteredClosed.slice(0, 3).map((pos) => {
                    const isPnlPositive = (pos.realized_pnl || 0) >= 0;
                    return (
                      <div key={pos.id} className="flex items-center justify-between text-[10px]">
                        <span className="font-semibold">{pos.coin}</span>
                        <span className="text-muted-foreground">{pos.side === "long" ? "↑" : "↓"} ${(pos.quantity_usd ?? 0).toFixed(0)}</span>
                        <span className={isPnlPositive ? "text-green-400" : "text-red-400"}>
                          {isPnlPositive ? "+" : ""}${(pos.realized_pnl ?? 0).toFixed(2)}
                        </span>
                      </div>
                    );
                  })
                )}
                {filteredClosed.length > 3 && (
                  <p className="text-[9px] text-muted-foreground pt-1">
                    +{filteredClosed.length - 3} more
                  </p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
