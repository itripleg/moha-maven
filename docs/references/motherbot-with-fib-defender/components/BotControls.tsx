"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Slider } from "@/components/ui/slider";
import { Play, Square, AlertOctagon } from "lucide-react";
import { useBotControls } from "../hooks/useBotStatus";
import { useToast } from "@/hooks/use-toast";

export function BotControls() {
  const { startBot, stopBot, emergencyStop, controlling } = useBotControls();
  const { toast } = useToast();
  const [lastAction, setLastAction] = useState<string | null>(null);

  const handleStart = async () => {
    const result = await startBot();
    setLastAction("start");
    toast({
      title: result.success ? "Bot Started" : "Failed to Start",
      description: result.message,
      variant: result.success ? "default" : "destructive",
    });
  };

  const handleStop = async () => {
    const result = await stopBot();
    setLastAction("stop");
    toast({
      title: result.success ? "Bot Stopped" : "Failed to Stop",
      description: result.message,
      variant: result.success ? "default" : "destructive",
    });
  };

  const handleEmergencyStop = async () => {
    const result = await emergencyStop();
    setLastAction("emergency");
    toast({
      title: result.success ? "Emergency Stop Activated" : "Emergency Stop Failed",
      description: result.message,
      variant: result.success ? "default" : "destructive",
    });
  };

  return (
    <Card className="unified-card">
      <CardHeader>
        <CardTitle>Bot Controls</CardTitle>
        <CardDescription>
          Start, stop, or emergency halt the trading bot
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-6">
          {/* Controls Row */}
          <div className="flex flex-wrap gap-3">
            {/* Start Button */}
            <Button
              onClick={handleStart}
              disabled={controlling}
              variant="default"
              className="bg-green-600 hover:bg-green-700"
            >
              <Play className="w-4 h-4 mr-2" />
              Start Bot
            </Button>

            {/* Stop Button */}
            <Button
              onClick={handleStop}
              disabled={controlling}
              variant="secondary"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop Bot
            </Button>

            {/* Emergency Stop Button with Confirmation */}
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  disabled={controlling}
                  variant="destructive"
                >
                  <AlertOctagon className="w-4 h-4 mr-2" />
                  Emergency Stop
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Emergency Stop Bot?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will immediately halt the bot and close all open positions.
                    This action should only be used in emergency situations.
                    Are you absolutely sure?
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleEmergencyStop}
                    className="bg-destructive hover:bg-destructive/90"
                  >
                    Emergency Stop
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>

          {/* Settings Row */}
          <div className="space-y-4 pt-2 border-t border-border/40">
            <PositionSlider />
          </div>

          {lastAction && (
            <p className="text-xs text-muted-foreground">
              Last action: {lastAction} • {new Date().toLocaleTimeString()}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function PositionSlider() {
  const [value, setValue] = useState([50]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          Position Size
        </label>
        <span className="text-xs font-mono text-muted-foreground">{value}%</span>
      </div>
      <Slider
        defaultValue={[50]}
        max={100}
        min={1}
        step={1}
        value={value}
        onValueChange={setValue}
        className="w-full"
      />
      <p className="text-[10px] text-muted-foreground">
        Percentage of available balance per trade
      </p>
    </div>
  );
}

// Add Slider import - we need to create/import the UI component first if it doesn't exist.
// Assuming it exists in @/components/ui/slider based on conventions, but I'll add the import line in a separate edit or assume standard shadcn/ui.
// Wait, I need to add the import to the top of the file too. Adding it here inside the replace block would be messy.
// Let's split this into two edits: one for imports, one for the component body.
// Actually, I'll do a multi-replace.
