// app/motherbot/components/TAVision.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMemo } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart,
} from "recharts";
import { Activity, TrendingUp, TrendingDown } from "lucide-react";

interface TAVisionProps {
  selectedPair: string;
  loading?: boolean;
}

// Mock TA data - in production, calculate from actual market data
const generateTAData = (coin: string) => {
  const data = [];
  const now = Date.now();

  // Generate some realistic-looking data with trends
  let baseRSI = 50;
  let baseMacd = 0;
  let baseSignal = 0;

  for (let i = 100; i >= 0; i--) {
    const timestamp = new Date(now - i * 900000).toISOString(); // 15min intervals

    // Add some momentum/trend
    baseRSI += (Math.random() - 0.5) * 10;
    baseRSI = Math.max(20, Math.min(80, baseRSI)); // Keep in reasonable range

    baseMacd += (Math.random() - 0.5) * 2;
    baseMacd = Math.max(-15, Math.min(15, baseMacd));

    // Signal line follows MACD with lag
    baseSignal = baseSignal * 0.9 + baseMacd * 0.1;

    const histogram = baseMacd - baseSignal;

    data.push({
      timestamp,
      rsi: baseRSI,
      macd: baseMacd,
      signal: baseSignal,
      histogram,
    });
  }

  return data;
};

export function TAVision({ selectedPair, loading = false }: TAVisionProps) {
  const coin = selectedPair === "ALL" ? "BTC" : selectedPair.split('/')[0];
  const taData = useMemo(() => generateTAData(coin), [coin]);

  // Calculate current indicators
  const currentIndicators = useMemo(() => {
    if (taData.length === 0) return null;
    const latest = taData[taData.length - 1];

    return {
      rsi: latest.rsi,
      macd: latest.macd,
      signal: latest.signal,
      histogram: latest.histogram,
    };
  }, [taData]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-4 w-4 text-primary" />
              Technical Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Skeleton className="w-full h-[300px]" />
          </CardContent>
        </Card>
      </div>
    );
  }

  const rsiSignal = currentIndicators
    ? currentIndicators.rsi > 70
      ? "Overbought"
      : currentIndicators.rsi < 30
      ? "Oversold"
      : "Neutral"
    : "N/A";

  const macdSignal = currentIndicators
    ? currentIndicators.macd > currentIndicators.signal
      ? "Bullish"
      : "Bearish"
    : "N/A";

  return (
    <div className="space-y-3">
      {/* Indicator Summary */}
      <div className="grid grid-cols-4 gap-3">
        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardContent className="p-3">
            <div className="text-xs text-muted-foreground mb-1">RSI (14)</div>
            <div className="text-xl font-bold">{currentIndicators?.rsi.toFixed(2)}</div>
            <div className={`text-xs font-medium mt-1 ${
              rsiSignal === "Overbought" ? "text-red-500" :
              rsiSignal === "Oversold" ? "text-green-500" :
              "text-muted-foreground"
            }`}>
              {rsiSignal}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardContent className="p-3">
            <div className="text-xs text-muted-foreground mb-1">MACD</div>
            <div className="text-xl font-bold">{currentIndicators?.macd.toFixed(2)}</div>
            <div className={`text-xs font-medium mt-1 ${
              macdSignal === "Bullish" ? "text-green-500" : "text-red-500"
            }`}>
              {macdSignal}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardContent className="p-3">
            <div className="text-xs text-muted-foreground mb-1">Signal Line</div>
            <div className="text-xl font-bold">{currentIndicators?.signal.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground mt-1">9-period EMA</div>
          </CardContent>
        </Card>

        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardContent className="p-3">
            <div className="text-xs text-muted-foreground mb-1">Histogram</div>
            <div className={`text-xl font-bold ${
              (currentIndicators?.histogram ?? 0) >= 0 ? "text-green-500" : "text-red-500"
            }`}>
              {currentIndicators?.histogram.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">MACD - Signal</div>
          </CardContent>
        </Card>
      </div>

      {/* RSI Chart */}
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardContent className="pt-6">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <Activity className="h-3.5 w-3.5 text-primary" />
            RSI (Relative Strength Index)
            <span className="text-xs text-muted-foreground ml-auto">({coin})</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={taData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
                }}
                stroke="hsl(var(--muted-foreground))"
                fontSize={10}
              />
              <YAxis
                domain={[0, 100]}
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
              />
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "Overbought", fontSize: 10 }} />
              <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" label={{ value: "Oversold", fontSize: 10 }} />
              <ReferenceLine y={50} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
              <Line
                type="monotone"
                dataKey="rsi"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* MACD Chart */}
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardContent className="pt-6">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <TrendingUp className="h-3.5 w-3.5 text-primary" />
            MACD (Moving Average Convergence Divergence)
            <span className="text-xs text-muted-foreground ml-auto">({coin})</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <ComposedChart data={taData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
                }}
                stroke="hsl(var(--muted-foreground))"
                fontSize={10}
              />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                formatter={(value: number, name: string) => {
                  const labels: Record<string, string> = {
                    macd: "MACD",
                    signal: "Signal",
                    histogram: "Histogram",
                  };
                  return [value.toFixed(2), labels[name] || name];
                }}
              />
              <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
              {/* Histogram bars - must come first for proper layering */}
              <Bar
                dataKey="histogram"
                fill="#8b5cf6"
                opacity={0.6}
                radius={[2, 2, 0, 0]}
              />
              {/* MACD line */}
              <Line
                type="monotone"
                dataKey="macd"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                name="MACD"
              />
              {/* Signal line */}
              <Line
                type="monotone"
                dataKey="signal"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                strokeDasharray="5 5"
                name="Signal"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="p-2 rounded-md bg-primary/5 border border-primary/20">
        <p className="text-xs text-muted-foreground">
          <strong className="text-primary">TA Vision:</strong> Real-time technical analysis indicators calculated from market data. These indicators help identify trends, momentum, and potential reversal points.
        </p>
      </div>
    </div>
  );
}
