"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Brain, TrendingUp, TrendingDown, Minus, X, ChevronLeft, ChevronRight } from "lucide-react";
import { useBotDecisions } from "../hooks/useBotDecisions";
import type { BotDecision } from "../types";

function DecisionCard({ decision }: { decision: BotDecision }) {
  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "buy_to_enter":
        return "bg-green-500/10 text-green-500 border-green-500/50";
      case "sell_to_enter":
        return "bg-red-500/10 text-red-500 border-red-500/50";
      case "hold":
        return "bg-blue-500/10 text-blue-500 border-blue-500/50";
      case "close":
        return "bg-yellow-500/10 text-yellow-500 border-yellow-500/50";
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/50";
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case "buy_to_enter":
        return <TrendingUp className="w-3 h-3" />;
      case "sell_to_enter":
        return <TrendingDown className="w-3 h-3" />;
      case "hold":
        return <Minus className="w-3 h-3" />;
      case "close":
        return <X className="w-3 h-3" />;
      default:
        return null;
    }
  };

  const confidenceColor = decision.confidence >= 0.7
    ? "text-green-500"
    : decision.confidence >= 0.5
    ? "text-yellow-500"
    : "text-red-500";

  return (
    <div className="p-2 border border-border/30 rounded-lg hover:border-primary/30 transition-colors bg-card/50">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex flex-col gap-1">
          <h4 className="font-semibold text-xs">{decision.coin}</h4>
          <Badge variant="outline" className={`${getSignalColor(decision.signal)} w-fit text-[10px] px-1.5 py-0`}>
            <span className="flex items-center gap-1">
              {getSignalIcon(decision.signal)}
              {decision.signal.replace("_", " ").toUpperCase()}
            </span>
          </Badge>
        </div>
        <span className="text-[10px] text-muted-foreground">
          {new Date(decision.timestamp).toLocaleString()}
        </span>
      </div>

      {/* Details */}
      <div className="grid grid-cols-3 gap-2 mb-2 text-xs">
        <div>
          <p className="text-[10px] text-muted-foreground">Size</p>
          <p className="font-mono">${(decision.quantity_usd ?? 0).toFixed(2)}</p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground">Leverage</p>
          <p className="font-mono">{decision.leverage ?? 1}x</p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground">Confidence</p>
          <p className={`font-mono font-semibold ${confidenceColor}`}>
            {((decision.confidence ?? 0) * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Exit Plan */}
      {(decision.profit_target || decision.stop_loss) && (
        <div className="mb-2 text-xs">
          <p className="text-[10px] text-muted-foreground mb-0.5">Exit Plan</p>
          <div className="flex gap-3">
            {decision.profit_target && (
              <div>
                <span className="text-[10px] text-muted-foreground">Target: </span>
                <span className="font-mono text-green-500">
                  ${(decision.profit_target ?? 0).toFixed(2)}
                </span>
              </div>
            )}
            {decision.stop_loss && (
              <div>
                <span className="text-[10px] text-muted-foreground">Stop: </span>
                <span className="font-mono text-red-500">
                  ${(decision.stop_loss ?? 0).toFixed(2)}
                </span>
              </div>
            )}
          </div>
          {decision.invalidation_condition && (
            <p className="text-[10px] text-muted-foreground mt-0.5">
              Invalidation: {decision.invalidation_condition}
            </p>
          )}
        </div>
      )}

      {/* Justification */}
      <div className="text-xs">
        <p className="text-[10px] text-muted-foreground mb-0.5">Analysis</p>
        <p className="text-muted-foreground">{decision.justification}</p>
      </div>
    </div>
  );
}

export function DecisionsFeed({ limit = 1, selectedPair }: { limit?: number; selectedPair?: string }) {
  const [currentPage, setCurrentPage] = useState(0);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch more decisions than we display for pagination
  const totalToFetch = limit * 10;
  // Only filter by coin if a specific pair is selected (not "ALL")
  const coinFilter = selectedPair && selectedPair !== "ALL" ? selectedPair : undefined;
  const { decisions: allDecisions, loading, error } = useBotDecisions(totalToFetch, coinFilter);

  // Calculate paginated decisions
  const startIdx = currentPage * limit;
  const endIdx = startIdx + limit;
  const decisions = allDecisions.slice(startIdx, endIdx);
  const hasNext = endIdx < allDecisions.length;
  const hasPrevious = currentPage > 0;

  // Minimum swipe distance (in px) to trigger page change
  const minSwipeDistance = 50;

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;

    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && hasNext) {
      setCurrentPage(prev => prev + 1);
    }
    if (isRightSwipe && hasPrevious) {
      setCurrentPage(prev => prev - 1);
    }
  };

  const goToNextPage = () => {
    if (hasNext) setCurrentPage(prev => prev + 1);
  };

  const goToPreviousPage = () => {
    if (hasPrevious) setCurrentPage(prev => prev - 1);
  };

  // Reset to first page when coin filter changes
  useEffect(() => {
    setCurrentPage(0);
  }, [selectedPair]);

  if (loading) {
    return (
      <Card className="unified-card h-[350px] flex flex-col">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Brain className="w-4 h-4 text-primary" />
            Trading Decisions
          </CardTitle>
        </CardHeader>
        <CardContent className="p-3">
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="unified-card h-[350px] flex flex-col border-destructive/50">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Brain className="w-4 h-4 text-destructive" />
            Trading Decisions
          </CardTitle>
        </CardHeader>
        <CardContent className="p-3">
          <p className="text-destructive text-xs">{error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="unified-card h-[350px] flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Brain className="w-4 h-4 text-primary" />
          Trading Decisions
          {selectedPair && selectedPair !== "ALL" && <span className="text-xs text-muted-foreground ml-2">({selectedPair.split('/')[0]})</span>}
        </CardTitle>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={goToPreviousPage}
            disabled={!hasPrevious}
            className="h-6 w-6"
            aria-label="Previous decisions"
          >
            <ChevronLeft className="h-3 w-3" />
          </Button>
          <span className="text-[10px] text-muted-foreground px-1">
            {allDecisions.length > 0 ? `${startIdx + 1}-${Math.min(endIdx, allDecisions.length)} of ${allDecisions.length}` : '0'}
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={goToNextPage}
            disabled={!hasNext}
            className="h-6 w-6"
            aria-label="Next decisions"
          >
            <ChevronRight className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto pr-2 p-3 scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
        {allDecisions.length === 0 ? (
          <div className="text-center py-6 text-xs text-muted-foreground">
            No trading decisions yet
          </div>
        ) : (
          <div
            ref={containerRef}
            className="space-y-2"
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
          >
            {decisions.map((decision) => (
              <DecisionCard key={decision.id} decision={decision} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
