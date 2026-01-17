// app/motherbot/components/BalanceGraph.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { TrendingUp, DollarSign } from "lucide-react";
import type { BalanceHistoryPoint } from "../types";

interface BalanceGraphProps {
  data: BalanceHistoryPoint[];
  loading?: boolean;
  initialBalance?: number;
}

export function BalanceGraph({
  data,
  loading = false,
  initialBalance = 1000,
}: BalanceGraphProps) {
  // Calculate ATH (All-Time High)
  const { ath, currentBalance, drawdownPercent } = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        ath: initialBalance,
        currentBalance: initialBalance,
        drawdownPercent: 0,
      };
    }

    const balances = data.map((d) => d.equity_usd);
    const ath = Math.max(...balances, initialBalance);
    const current = data[data.length - 1]?.equity_usd || initialBalance;
    const drawdown = ((ath - current) / ath) * 100;

    return {
      ath,
      currentBalance: current,
      drawdownPercent: drawdown,
    };
  }, [data, initialBalance]);

  // Format data for chart
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return [
        {
          timestamp: new Date().toISOString(),
          balance: initialBalance,
          pnl: 0,
        },
      ];
    }

    return data.map((point) => ({
      timestamp: point.timestamp,
      balance: point.equity_usd,
      pnl: point.total_pnl,
    }));
  }, [data, initialBalance]);

  const isProfitable = currentBalance >= initialBalance;

  if (loading) {
    return (
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <TrendingUp className="h-4 w-4 text-primary" />
            Account Balance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-[300px]" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <TrendingUp className="h-4 w-4 text-primary" />
            Account Balance
          </CardTitle>
          <div className="flex items-center gap-4">
            {/* Current Balance */}
            <div className="text-right">
              <p className="text-[9px] text-muted-foreground uppercase tracking-wide">
                Current
              </p>
              <p
                className={`text-sm font-bold ${
                  isProfitable ? "text-green-500" : "text-red-500"
                }`}
              >
                ${currentBalance.toFixed(2)}
              </p>
            </div>
            {/* ATH */}
            <div className="text-right">
              <p className="text-[9px] text-muted-foreground uppercase tracking-wide">
                ATH
              </p>
              <p className="text-sm font-bold text-primary">
                ${ath.toFixed(2)}
              </p>
            </div>
            {/* Drawdown */}
            {drawdownPercent > 0 && (
              <div className="text-right">
                <p className="text-[9px] text-muted-foreground uppercase tracking-wide">
                  Drawdown
                </p>
                <p className="text-sm font-bold text-red-500">
                  -{drawdownPercent.toFixed(1)}%
                </p>
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={chartData}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="hsl(var(--border))"
              opacity={0.3}
            />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                });
              }}
              stroke="hsl(var(--muted-foreground))"
              fontSize={10}
            />
            <YAxis
              domain={[0, ath * 1.1]}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
              stroke="hsl(var(--muted-foreground))"
              fontSize={10}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                fontSize: "12px",
              }}
              labelFormatter={(value) => {
                const date = new Date(value as string);
                return date.toLocaleString();
              }}
              formatter={(value: number, name: string) => {
                if (name === "balance") {
                  return [`$${value.toFixed(2)}`, "Balance"];
                }
                return [`${value >= 0 ? "+" : ""}$${value.toFixed(2)}`, "P&L"];
              }}
            />
            {/* Reference line at initial balance */}
            <ReferenceLine
              y={initialBalance}
              stroke="hsl(var(--primary))"
              strokeDasharray="3 3"
              label={{
                value: "Start",
                position: "right",
                fontSize: 10,
                fill: "hsl(var(--primary))",
              }}
            />
            {/* Reference line at ATH */}
            <ReferenceLine
              y={ath}
              stroke="hsl(var(--primary))"
              strokeDasharray="5 5"
              label={{
                value: "ATH",
                position: "right",
                fontSize: 10,
                fill: "hsl(var(--primary))",
              }}
            />
            {/* Main balance line */}
            <Line
              type="monotone"
              dataKey="balance"
              stroke={isProfitable ? "#22c55e" : "#ef4444"}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
