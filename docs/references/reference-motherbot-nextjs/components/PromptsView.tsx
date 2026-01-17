// app/motherbot/components/PromptsView.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { FileText, Copy, MessageSquare, Cpu, Terminal, Clock } from "lucide-react";
import { useBotDebug } from "../hooks/useBotDebug";
import { useToast } from "@/hooks/use-toast";

interface PromptsViewProps {
  selectedPair?: string;
}

export function PromptsView({ selectedPair }: PromptsViewProps) {
  const { debugInfo, loading } = useBotDebug();
  const { toast } = useToast();

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: `${label} copied to clipboard`,
    });
  };

  if (loading) {
    return (
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4 text-primary" />
            Claude Prompts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[400px]" />
        </CardContent>
      </Card>
    );
  }

  if (!debugInfo.latest_prompt) {
    return (
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4 text-primary" />
            Claude Prompts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-sm text-muted-foreground">
              No prompts available yet
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Prompts will appear here after the next analysis cycle
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4 text-primary" />
            Claude Prompts
          </CardTitle>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {new Date(debugInfo.latest_prompt.timestamp).toLocaleString()}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
        <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
          <p className="text-xs text-muted-foreground">
            <strong className="text-primary">Compare to TA Vision:</strong> These are the exact prompts sent to Claude.
            Switch to the TA Vision tab to see how the indicators mentioned here appear on the chart.
          </p>
        </div>

        <Accordion type="single" collapsible className="w-full space-y-2">
          {/* User Prompt (Context) */}
          <AccordionItem value="user-prompt" className="border border-border rounded-lg bg-card/50 px-3">
            <AccordionTrigger className="hover:no-underline py-3">
              <div className="flex items-center gap-2 text-sm font-medium text-blue-400">
                <MessageSquare className="w-4 h-4" />
                User Prompt (Market Context & Data)
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-4">
              <div className="relative group">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(debugInfo.latest_prompt?.user_prompt || "", "User Prompt")}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </Button>
                <pre className="text-[10px] font-mono whitespace-pre-wrap bg-background p-3 rounded border border-border max-h-[400px] overflow-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
                  {debugInfo.latest_prompt.user_prompt}
                </pre>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* System Prompt (Instructions) */}
          <AccordionItem value="system-prompt" className="border border-border rounded-lg bg-card/50 px-3">
            <AccordionTrigger className="hover:no-underline py-3">
              <div className="flex items-center gap-2 text-sm font-medium text-purple-400">
                <Cpu className="w-4 h-4" />
                System Prompt (Trading Strategy & Rules)
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-4">
              <div className="relative group">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(debugInfo.latest_prompt?.system_prompt || "", "System Prompt")}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </Button>
                <pre className="text-[10px] font-mono whitespace-pre-wrap bg-background p-3 rounded border border-border max-h-[400px] overflow-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
                  {debugInfo.latest_prompt.system_prompt}
                </pre>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Claude's Response */}
          <AccordionItem value="response" className="border border-border rounded-lg bg-card/50 px-3">
            <AccordionTrigger className="hover:no-underline py-3">
              <div className="flex items-center gap-2 text-sm font-medium text-green-400">
                <Terminal className="w-4 h-4" />
                Claude's Response
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-4">
              <div className="relative group">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(
                    typeof debugInfo.latest_prompt?.response === 'string'
                      ? debugInfo.latest_prompt.response
                      : JSON.stringify(debugInfo.latest_prompt?.response, null, 2),
                    "Claude's Response"
                  )}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </Button>
                <pre className="text-[10px] font-mono whitespace-pre-wrap bg-background p-3 rounded border border-border max-h-[400px] overflow-auto scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-border/20 hover:scrollbar-thumb-primary/60">
                  {typeof debugInfo.latest_prompt.response === 'string'
                    ? debugInfo.latest_prompt.response
                    : JSON.stringify(debugInfo.latest_prompt.response, null, 2)}
                </pre>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
}
