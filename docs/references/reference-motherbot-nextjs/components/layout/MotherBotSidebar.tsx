// app/motherbot/components/layout/MotherBotSidebar.tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Brain } from "lucide-react";
import { SidebarNav, SidebarView } from "../SidebarNav";
import { DecisionCardEnhanced } from "../DecisionCardEnhanced";
import { PromptsView } from "../PromptsView";
import { StrategyModeSelector } from "../StrategyModeSelector";
import { useBotDecisions } from "../../hooks/useBotDecisions";
import type { BotStrategyMode } from "../../types";

interface MotherBotSidebarProps {
  strategyMode: BotStrategyMode;
  onStrategyModeChange: (mode: BotStrategyMode) => void;
  selectedPair: string;
}

export function MotherBotSidebar({
  strategyMode,
  onStrategyModeChange,
  selectedPair,
}: MotherBotSidebarProps) {
  const [activeView, setActiveView] = useState<SidebarView>("decisions");
  const coinFilter = selectedPair && selectedPair !== "ALL" ? selectedPair : undefined;
  const { decisions, loading } = useBotDecisions(20, coinFilter);

  return (
    <div className="space-y-4 sticky top-24">
      {/* Sidebar Navigation */}
      <SidebarNav
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* Decisions View */}
      {activeView === "decisions" && (
        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Brain className="h-4 w-4 text-primary" />
              AI Decisions
              {selectedPair && selectedPair !== "ALL" && (
                <span className="text-xs text-muted-foreground ml-2">({selectedPair.split('/')[0]})</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-32" />
                ))}
              </div>
            ) : decisions.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No trading decisions yet
              </div>
            ) : (
              decisions.map((decision) => (
                <DecisionCardEnhanced key={decision.id} decision={decision} />
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Prompts View */}
      {activeView === "prompts" && (
        <PromptsView selectedPair={selectedPair} />
      )}

      {/* Settings View */}
      {activeView === "settings" && (
        <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
          <CardHeader>
            <CardTitle className="text-base">Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <StrategyModeSelector
              strategyMode={strategyMode}
              onStrategyModeChange={onStrategyModeChange}
              disabled={true}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
