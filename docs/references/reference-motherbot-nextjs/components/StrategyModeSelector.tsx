// app/motherbot/components/StrategyModeSelector.tsx
"use client";

import { Brain, GitBranch, Shield } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { BotStrategyMode } from "../types";

interface StrategyModeSelectorProps {
  strategyMode: BotStrategyMode;
  onStrategyModeChange: (mode: BotStrategyMode) => void;
  disabled?: boolean;
}

const STRATEGY_MODES = [
  {
    mode: "independent" as const,
    icon: Brain,
    label: "Independent",
    description: "AI trades autonomously with its own capital allocation",
    color: "text-primary",
  },
  {
    mode: "shadow" as const,
    icon: GitBranch,
    label: "Shadow",
    description: "AI trades in same direction as user with buffering",
    color: "text-blue-500",
  },
  {
    mode: "hedge" as const,
    icon: Shield,
    label: "Hedge",
    description: "AI takes opposite side to hedge user positions",
    color: "text-green-500",
  },
];

export function StrategyModeSelector({
  strategyMode,
  onStrategyModeChange,
  disabled = false,
}: StrategyModeSelectorProps) {
  return (
    <div className="space-y-2">
      <div className="text-xs font-semibold text-muted-foreground">
        Trading Strategy
      </div>
      <div className="flex items-center gap-2">
        {STRATEGY_MODES.map(({ mode, icon: Icon, label, description, color }) => {
          const isActive = strategyMode === mode;

          return (
            <TooltipProvider key={mode}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => !disabled && onStrategyModeChange(mode)}
                    disabled={disabled}
                    className={`px-3 py-2 rounded-lg transition-all flex-1 flex items-center justify-center gap-2 ${
                      isActive
                        ? "bg-primary/20 border border-primary"
                        : disabled
                        ? "bg-muted/20 border border-muted opacity-50 cursor-not-allowed"
                        : "bg-card/50 border border-border hover:bg-primary/10 hover:border-primary/50"
                    }`}
                  >
                    <Icon className={`h-3.5 w-3.5 ${isActive ? "text-primary" : disabled ? "text-muted-foreground" : color}`} />
                    <span className={`text-xs font-medium ${isActive ? "text-primary" : disabled ? "text-muted-foreground" : "text-foreground"}`}>
                      {label}
                    </span>
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-[250px] z-50">
                  <div className="space-y-1">
                    <p className="font-semibold text-xs">{label} Mode</p>
                    <p className="text-[10px] text-muted-foreground">{description}</p>
                    {disabled && (
                      <p className="text-[9px] text-yellow-500 mt-1">Coming Soon</p>
                    )}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        })}
      </div>
    </div>
  );
}
