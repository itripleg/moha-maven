// app/motherbot/components/BotControlPanel.tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  Play,
  Pause,
  RefreshCw,
  Settings,
  Zap,
  AlertCircle,
} from "lucide-react";
import { useBotStatus } from "../hooks/useBotStatus";

export function BotControlPanel() {
  const [isProcessing, setIsProcessing] = useState(false);
  const { status, loading } = useBotStatus();
  const { toast } = useToast();

  const isRunning = status?.status === "running";

  const handleStart = async () => {
    setIsProcessing(true);
    toast({
      title: "Starting Bot",
      description: "MotherBot is initializing...",
    });
    // TODO: Implement start API call
    setTimeout(() => setIsProcessing(false), 2000);
  };

  const handleStop = async () => {
    setIsProcessing(true);
    toast({
      title: "Stopping Bot",
      description: "MotherBot is shutting down...",
      variant: "destructive",
    });
    // TODO: Implement stop API call
    setTimeout(() => setIsProcessing(false), 2000);
  };

  const handleRefresh = async () => {
    setIsProcessing(true);
    toast({
      title: "Refreshing Data",
      description: "Fetching latest bot status...",
    });
    // TODO: Implement refresh
    setTimeout(() => setIsProcessing(false), 1000);
  };

  return (
    <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Settings className="h-3.5 w-3.5 text-primary" />
          Bot Controls
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {/* Status Display */}
        <div className="p-2 rounded-md bg-primary/5 border border-primary/20">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-muted-foreground">Status</span>
            <Badge
              variant={isRunning ? "default" : "secondary"}
              className={`text-[8px] px-1.5 py-0 ${
                isRunning
                  ? "bg-green-500/20 text-green-500 border-green-500/30"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {isRunning ? "Active" : status?.status || "Offline"}
            </Badge>
          </div>
          {status?.message && (
            <p className="text-[9px] text-muted-foreground leading-tight">{status.message}</p>
          )}
        </div>

        {/* Control Buttons */}
        <div className="grid grid-cols-2 gap-2">
          {isRunning ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleStop}
              disabled={isProcessing}
              className="w-full"
            >
              <Pause className="h-3.5 w-3.5 mr-1.5" />
              Stop
            </Button>
          ) : (
            <Button
              variant="default"
              size="sm"
              onClick={handleStart}
              disabled={isProcessing}
              className="w-full bg-green-500/20 text-green-500 hover:bg-green-500/30 border-green-500/30"
            >
              <Play className="h-3.5 w-3.5 mr-1.5" />
              Start
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isProcessing}
            className="w-full"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isProcessing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Quick Stats */}
        {status && (
          <div className="grid grid-cols-2 gap-2 pt-1.5 border-t border-primary/20">
            <div>
              <p className="text-[8px] text-muted-foreground uppercase tracking-wide">
                Trades
              </p>
              <p className="text-xs font-bold">{status.trades_today || 0}</p>
            </div>
            <div>
              <p className="text-[8px] text-muted-foreground uppercase tracking-wide">
                P&L
              </p>
              <p
                className={`text-xs font-bold ${
                  (status.pnl_today || 0) >= 0 ? "text-green-500" : "text-red-500"
                }`}
              >
                {(status.pnl_today || 0) >= 0 ? "+" : ""}$
                {(status.pnl_today || 0).toFixed(2)}
              </p>
            </div>
          </div>
        )}

        {/* Warning Note */}
        <div className="p-1.5 rounded-md bg-yellow-500/5 border border-yellow-500/20">
          <div className="flex items-start gap-1.5">
            <AlertCircle className="h-2.5 w-2.5 text-yellow-500 mt-0.5 flex-shrink-0" />
            <p className="text-[8px] text-yellow-600 dark:text-yellow-400 leading-tight">
              <strong>Paper Trading:</strong> Simulated trades only.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
