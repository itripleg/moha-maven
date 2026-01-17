// app/motherbot/components/SidebarNav.tsx
"use client";

import { Brain, FileText, Settings } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export type SidebarView = "decisions" | "prompts" | "settings";

interface SidebarNavProps {
  activeView: SidebarView;
  onViewChange: (view: SidebarView) => void;
}

const NAV_ITEMS = [
  {
    view: "decisions" as const,
    icon: Brain,
    label: "Decisions",
    description: "View all trading decisions made by the bot",
  },
  {
    view: "prompts" as const,
    icon: FileText,
    label: "Prompts",
    description: "View exact system and user prompts sent to Claude",
  },
  {
    view: "settings" as const,
    icon: Settings,
    label: "Settings",
    description: "Bot configuration and controls",
  },
];

export function SidebarNav({ activeView, onViewChange }: SidebarNavProps) {
  return (
    <div className="flex items-center gap-2 p-2 bg-card/30 backdrop-blur-sm border border-primary/40 rounded-lg">
      {NAV_ITEMS.map((item) => {
        const { view, icon: Icon, label, description } = item;
        const disabled = (item as any).disabled === true;
        const isActive = activeView === view;

        return (
          <TooltipProvider key={view}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={() => !disabled && onViewChange(view)}
                  disabled={disabled}
                  className={`px-3 py-2 rounded-lg transition-all flex-1 flex items-center justify-center gap-2 ${
                    isActive
                      ? "bg-primary/20 border border-primary"
                      : disabled
                      ? "bg-muted/20 border border-muted opacity-50 cursor-not-allowed"
                      : "bg-card/50 border border-border hover:bg-primary/10 hover:border-primary/50"
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${isActive ? "text-primary" : disabled ? "text-muted-foreground" : "text-foreground"}`} />
                  <span className={`text-xs font-medium ${isActive ? "text-primary" : disabled ? "text-muted-foreground" : "text-foreground"}`}>
                    {label}
                  </span>
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[200px] z-50">
                <div className="space-y-1">
                  <p className="font-semibold text-xs">{label}</p>
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
  );
}
