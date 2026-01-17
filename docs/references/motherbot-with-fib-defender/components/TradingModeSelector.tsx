// app/motherbot/components/TradingModeSelector.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Brain,
  GitBranch,
  Shield,
  Info,
} from "lucide-react";
import type { BotStrategyMode } from "../types";

interface TradingModeSelectorProps {
  selectedMode: BotStrategyMode;
  onModeChange: (mode: BotStrategyMode) => void;
}

const TRADING_MODES: Array<{
  mode: BotStrategyMode;
  icon: typeof Brain;
  label: string;
  description: string;
  color: string;
}> = [
  {
    mode: "independent",
    icon: Brain,
    label: "Independent",
    description:
      "AI acts autonomously using its own memory and decision-making. Perfect for evaluation and testing strategies.",
    color: "text-primary",
  },
  {
    mode: "shadow",
    icon: GitBranch,
    label: "Shadow",
    description:
      "AI trades in the same direction as you with configurable aggression. Buffers your positions with varying amounts (safer or more aggressive).",
    color: "text-blue-500",
  },
  {
    mode: "hedge",
    icon: Shield,
    label: "Hedge",
    description:
      "AI takes the opposite side of your trades as a hedge. You can choose which side to keep.",
    color: "text-green-500",
  },
];

export function TradingModeSelector({
  selectedMode,
  onModeChange,
}: TradingModeSelectorProps) {
  return (
    <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Brain className="h-3.5 w-3.5 text-primary" />
          Trading Strategy
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {TRADING_MODES.map(({ mode, icon: Icon, label, description, color }) => {
          const isSelected = selectedMode === mode;

          return (
            <TooltipProvider key={mode}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={isSelected ? "default" : "outline"}
                    className={`w-full justify-start gap-2 h-auto p-2 transition-all ${
                      isSelected
                        ? "bg-primary/20 border-primary/40 hover:bg-primary/30"
                        : "hover:bg-primary/10"
                    }`}
                    onClick={() => onModeChange(mode)}
                  >
                    <Icon className={`h-3.5 w-3.5 ${isSelected ? "text-primary" : color}`} />
                    <div className="flex-1 text-left">
                      <div className="font-semibold text-xs">{label}</div>
                    </div>
                    {mode !== "independent" && (
                      <Badge variant="secondary" className="text-[8px] px-1.5 py-0">
                        Soon
                      </Badge>
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="left" className="max-w-[250px]">
                  <div className="space-y-1">
                    <p className="font-semibold text-xs">{label} Mode</p>
                    <p className="text-[10px] text-muted-foreground">
                      {description}
                    </p>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        })}

        {/* Info Note */}
        <div className="mt-2 p-1.5 rounded-md bg-primary/5 border border-primary/20">
          <div className="flex items-start gap-1.5">
            <Info className="h-2.5 w-2.5 text-primary mt-0.5 flex-shrink-0" />
            <p className="text-[8px] text-muted-foreground leading-tight">
              <strong className="text-primary">Independent</strong> mode active. Shadow/Hedge coming soon.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
