"use client";

import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, Clock, TrendingUp, TrendingDown } from "lucide-react";
import { useBotErrors } from "../hooks/useBotErrors";
import { Skeleton } from "@/components/ui/skeleton";

function ErrorCard({ error }: { error: ReturnType<typeof useBotErrors>["errors"][0] }) {
  const { decision, error: errorMsg, timestamp } = error;
  const timeAgo = new Date(timestamp).toLocaleString();

  return (
    <Card className="border-destructive/30 bg-destructive/5">
      <CardContent className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-destructive" />
            <div>
              <div className="font-semibold text-sm">{decision.coin}</div>
              <div className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {timeAgo}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {decision.signal === "buy_to_enter" || decision.signal === "sell_to_enter" ? (
              decision.signal === "buy_to_enter" ? (
                <TrendingUp className="w-4 h-4 text-green-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500" />
              )
            ) : null}
            <span className="text-xs px-2 py-1 rounded-full bg-destructive/20 text-destructive font-medium">
              {decision.signal.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Error Message */}
        <div className="bg-background/50 rounded-md p-3 border border-destructive/20">
          <div className="text-xs font-medium text-destructive mb-1">Error:</div>
          <div className="text-sm text-foreground/90">{errorMsg}</div>
        </div>

        {/* Decision Details */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <div className="text-muted-foreground">Size</div>
            <div className="font-mono">${decision.quantity_usd.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Leverage</div>
            <div className="font-mono">{decision.leverage}x</div>
          </div>
          <div>
            <div className="text-muted-foreground">Confidence</div>
            <div className="font-mono">{(decision.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>

        {/* Justification (truncated) */}
        {decision.justification && (
          <div className="text-xs text-muted-foreground pt-2 border-t border-border/30">
            <div className="font-medium mb-1">Reasoning:</div>
            <div className="line-clamp-2">{decision.justification}</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function ErrorsTab() {
  const { errors, loading, error: fetchError } = useBotErrors();

  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (fetchError) {
    return (
      <Card className="border-destructive/30">
        <CardContent className="p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-destructive mx-auto mb-2" />
          <p className="text-sm text-destructive">{fetchError}</p>
        </CardContent>
      </Card>
    );
  }

  if (errors.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-green-500 mb-2">✓</div>
          <p className="text-sm text-muted-foreground">No execution errors found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <div className="text-sm text-muted-foreground mb-4">
        Found {errors.length} execution error{errors.length !== 1 ? "s" : ""}
      </div>
      {errors.map((error, index) => (
        <ErrorCard key={`error-${error.decision.id}-${index}`} error={error} />
      ))}
    </div>
  );
}
