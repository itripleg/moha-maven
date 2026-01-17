"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Terminal, Cpu, MessageSquare, Clock } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useBotPositions } from "../hooks/useBotPositions";
import { useBotDebug } from "../hooks/useBotDebug";
import { useBotErrors } from "../hooks/useBotErrors";
import type { BotPosition } from "../types";

function PositionRow({ position }: { position: BotPosition }) {
  const isOpen = position.status === "open";
  const isPnlPositive = isOpen
    ? (position.unrealized_pnl || 0) >= 0
    : (position.realized_pnl || 0) >= 0;

  const pnl = isOpen ? position.unrealized_pnl : position.realized_pnl;

  return (
    <div className="grid grid-cols-5 gap-2 items-center py-2 px-2 border-b border-border/30 hover:bg-accent/10 transition-colors text-xs">
      {/* Coin */}
      <div className="font-semibold">{position.coin}</div>

      {/* Side - Icon only */}
      <div className="flex items-center justify-center">
        {position.side === "long" ? (
          <TrendingUp className="w-4 h-4 text-green-500" />
        ) : (
          <TrendingDown className="w-4 h-4 text-red-500" />
        )}
      </div>

      {/* Size & Leverage */}
      <div>
        <div className="font-mono text-xs">${(position.quantity_usd ?? 0).toFixed(2)}</div>
        <div className="text-[10px] text-muted-foreground">{position.leverage ?? 1}x</div>
      </div>

      {/* Entry Price */}
      <div className="font-mono text-xs">
        ${(position.entry_price ?? 0).toFixed(2)}
      </div>

      {/* P&L */}
      <div className={`font-semibold text-right ${isPnlPositive ? "text-green-500" : "text-red-500"}`}>
        <div className="flex items-center justify-end gap-1">
          {pnl !== null && pnl !== undefined ? (
            <>
              <span className="text-xs">${Math.abs(pnl).toFixed(2)}</span>
              {isPnlPositive ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
            </>
          ) : (
            "N/A"
          )}
        </div>
      </div>
    </div>
  );
}

interface BotActivityPanelProps {
  selectedPair?: string;
}

export function BotActivityPanel({ selectedPair }: BotActivityPanelProps) {
  const [activeTab, setActiveTab] = useState<"open" | "closed" | "errors" | "config" | "debug">("open");
  const { positions: openPositions, loading: loadingOpen } = useBotPositions("open");
  const { positions: closedPositions, loading: loadingClosed } = useBotPositions("closed");
  const { debugInfo, loading: loadingDebug } = useBotDebug();
  const { errors } = useBotErrors();

  // Filter positions by selected pair (unless "ALL" is selected)
  const filteredOpenPositions = selectedPair && selectedPair !== "ALL"
    ? openPositions.filter(p => p.coin === selectedPair)
    : openPositions;
  const filteredClosedPositions = selectedPair && selectedPair !== "ALL"
    ? closedPositions.filter(p => p.coin === selectedPair)
    : closedPositions;
  const filteredErrors = selectedPair && selectedPair !== "ALL"
    ? errors.filter(e => e.decision.coin === selectedPair)
    : errors;

  const positions = activeTab === "open" ? filteredOpenPositions : filteredClosedPositions;
  const loading = activeTab === "open" ? loadingOpen : loadingClosed;

  return (
    <Card className="unified-card h-[350px] flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Positions</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden flex flex-col p-3">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-5 mb-2 h-8">
            <TabsTrigger value="open" className="text-xs">
              Open ({filteredOpenPositions.length})
            </TabsTrigger>
            <TabsTrigger value="closed" className="text-xs">
              Closed ({filteredClosedPositions.length})
            </TabsTrigger>
            <TabsTrigger value="errors" className="text-xs">
              Errors ({filteredErrors.length})
            </TabsTrigger>
            <TabsTrigger value="config" className="text-xs">
              Config
            </TabsTrigger>
            <TabsTrigger value="debug" className="text-xs">
              Debug
            </TabsTrigger>
          </TabsList>

          <TabsContent value="open" className="mt-0 flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
            {loading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : positions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No open positions
              </div>
            ) : (
              <div>
                {/* Header */}
                <div className="grid grid-cols-5 gap-3 px-2 sm:px-4 py-2 text-xs font-semibold text-muted-foreground border-b border-border">
                  <div>COIN</div>
                  <div className="text-center">SIDE</div>
                  <div>SIZE</div>
                  <div>ENTRY</div>
                  <div className="text-right hidden sm:block">UNREALIZED P&L</div>
                  <div className="text-right sm:hidden">P&L</div>
                </div>
                {/* Rows */}
                {positions.map((position) => (
                  <PositionRow key={position.id} position={position} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="closed" className="mt-0 flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
            {loading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : positions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No closed positions
              </div>
            ) : (
              <div>
                {/* Header */}
                <div className="grid grid-cols-5 gap-3 px-2 sm:px-4 py-2 text-xs font-semibold text-muted-foreground border-b border-border">
                  <div>COIN</div>
                  <div className="text-center">SIDE</div>
                  <div>SIZE</div>
                  <div>ENTRY</div>
                  <div className="text-right hidden sm:block">REALIZED P&L</div>
                  <div className="text-right sm:hidden">P&L</div>
                </div>
                {/* Rows */}
                {positions.map((position) => (
                  <PositionRow key={position.id} position={position} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="errors" className="mt-0 flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
            {filteredErrors.length === 0 && selectedPair ? (
              <div className="text-center py-6 text-xs text-muted-foreground">
                No errors for {selectedPair.split('/')[0]}
              </div>
            ) : (
              <div className="space-y-2">
                {filteredErrors.map((error, index) => {
                  const { decision, error: errorMsg, timestamp } = error;
                  const timeAgo = new Date(timestamp).toLocaleString();

                  return (
                    <div key={`error-${decision.id}-${index}`} className="p-2 border border-destructive/30 rounded-lg bg-destructive/5">
                      <div className="flex items-start justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <div>
                            <div className="font-semibold text-xs">{decision.coin}</div>
                            <div className="text-[10px] text-muted-foreground">{timeAgo}</div>
                          </div>
                        </div>
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-destructive/20 text-destructive font-medium">
                          {decision.signal.toUpperCase()}
                        </span>
                      </div>
                      <div className="bg-background/50 rounded-md p-2 border border-destructive/20">
                        <div className="text-[10px] font-medium text-destructive mb-0.5">Error:</div>
                        <div className="text-xs text-foreground/90">{errorMsg}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="config" className="mt-0 flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
            <div className="space-y-2">
              <div className="p-2 border border-border rounded-lg">
                <h3 className="font-semibold text-xs mb-2">Bot Configuration</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Trading Mode</span>
                    <div className="flex gap-1">
                      <button className="px-2 py-0.5 text-xs rounded-md bg-green-500/10 text-green-500 border border-green-500/50">
                        Live (Testnet)
                      </button>
                      <button className="px-2 py-0.5 text-xs rounded-md hover:bg-accent">
                        Paper
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Max Position Size</span>
                    <input
                      type="number"
                      defaultValue="300"
                      className="w-20 px-1.5 py-0.5 text-xs rounded-md border border-border bg-background"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Max Leverage</span>
                    <input
                      type="number"
                      defaultValue="5"
                      className="w-20 px-1.5 py-0.5 text-xs rounded-md border border-border bg-background"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Analysis Interval</span>
                    <span className="text-xs">180s</span>
                  </div>
                </div>
              </div>
              <div className="text-[10px] text-muted-foreground">
                Note: Configuration changes require bot restart
              </div>
            </div>
          </TabsContent>

          <TabsContent value="debug" className="mt-0 flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                <span>Latest prompts sent to Claude</span>
                {debugInfo.latest_prompt && (
                  <span className="flex items-center gap-1 text-[10px]">
                    <Clock className="w-2.5 h-2.5" />
                    {new Date(debugInfo.latest_prompt.timestamp).toLocaleString()}
                  </span>
                )}
              </div>

              {loadingDebug ? (
                <Skeleton className="h-32" />
              ) : !debugInfo.latest_prompt ? (
                <div className="p-2 border border-border rounded-lg bg-accent/5">
                  <div className="text-[10px] font-mono text-muted-foreground mb-1">
                    No recent prompts available
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    Prompts will appear here after the next analysis cycle
                  </div>
                </div>
              ) : (
                <Accordion type="single" collapsible className="w-full space-y-1">
                  <AccordionItem value="user-prompt" className="border border-border rounded-lg bg-card/50 px-1.5">
                    <AccordionTrigger className="hover:no-underline py-2">
                      <div className="flex items-center gap-1.5 text-xs font-medium text-blue-400">
                        <MessageSquare className="w-3 h-3" />
                        User Prompt (Context)
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pt-1 pb-2">
                      <div className="relative group">
                        <button
                          onClick={() => navigator.clipboard.writeText(debugInfo.latest_prompt?.user_prompt || "")}
                          className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity px-1.5 py-0.5 text-[10px] bg-muted text-muted-foreground rounded hover:bg-accent"
                        >
                          Copy
                        </button>
                        <pre className="text-[10px] font-mono whitespace-pre-wrap bg-background p-2 rounded border border-border max-h-[200px] overflow-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
                          {debugInfo.latest_prompt.user_prompt}
                        </pre>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="system-prompt" className="border border-border rounded-lg bg-card/50 px-1.5">
                    <AccordionTrigger className="hover:no-underline py-2">
                      <div className="flex items-center gap-1.5 text-xs font-medium text-purple-400">
                        <Cpu className="w-3 h-3" />
                        System Prompt (Instructions)
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pt-1 pb-2">
                      <div className="relative group">
                        <button
                          onClick={() => navigator.clipboard.writeText(debugInfo.latest_prompt?.system_prompt || "")}
                          className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity px-1.5 py-0.5 text-[10px] bg-muted text-muted-foreground rounded hover:bg-accent"
                        >
                          Copy
                        </button>
                        <pre className="text-[10px] font-mono whitespace-pre-wrap bg-background p-2 rounded border border-border max-h-[200px] overflow-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
                          {debugInfo.latest_prompt.system_prompt}
                        </pre>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="response" className="border border-border rounded-lg bg-card/50 px-1.5">
                    <AccordionTrigger className="hover:no-underline py-2">
                      <div className="flex items-center gap-1.5 text-xs font-medium text-green-400">
                        <Terminal className="w-3 h-3" />
                        Claude's Response
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pt-1 pb-2">
                      <div className="relative group">
                        <button
                          onClick={() => navigator.clipboard.writeText(
                            typeof debugInfo.latest_prompt?.response === 'string'
                              ? debugInfo.latest_prompt.response
                              : JSON.stringify(debugInfo.latest_prompt?.response, null, 2)
                          )}
                          className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity px-1.5 py-0.5 text-[10px] bg-muted text-muted-foreground rounded hover:bg-accent"
                        >
                          Copy
                        </button>
                        <pre className="text-[10px] font-mono whitespace-pre-wrap bg-background p-2 rounded border border-border max-h-[200px] overflow-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
                          {typeof debugInfo.latest_prompt.response === 'string'
                            ? debugInfo.latest_prompt.response
                            : JSON.stringify(debugInfo.latest_prompt.response, null, 2)}
                        </pre>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
