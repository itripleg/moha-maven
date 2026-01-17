"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { TrendingUp, TrendingDown, X, RotateCcw, Trophy } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useGameEngine } from "../hooks/useGameEngine";
import { CandlestickChart } from "./CandlestickChart";
import { Leverage, Timeframe } from "@/types/game";

const INITIAL_BALANCE = 10000;

export function FibDefender() {
  const {
    candles,
    gameState,
    fibLevels,
    timeframe,
    leverage,
    currentPrice,
    rsi,
    macd,
    setTimeframe,
    setLeverage,
    openPosition,
    closePosition,
    resetGame,
  } = useGameEngine();

  const timeframes: Timeframe[] = [1, 5, 15, 30, 60];
  const leverages: Leverage[] = [1, 2, 5, 10, 25, 50];

  const currentRSI = rsi[rsi.length - 1] || 50;
  const currentMACD = macd.histogram[macd.histogram.length - 1] || 0;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
      {/* Main Chart Area */}
      <div className="space-y-4">
        {/* Chart */}
        <CandlestickChart
          candles={candles}
          fibLevels={fibLevels}
          currentPrice={currentPrice}
          timeframe={timeframe}
          position={gameState.position}
          pnl={gameState.pnl}
        />

        {/* Oscillators */}
        <div className="grid grid-cols-2 gap-4">
          {/* RSI */}
          <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold text-foreground">RSI (14)</div>
                <div
                  className={cn(
                    "text-xl font-bold",
                    currentRSI > 70 ? "text-red-500" : currentRSI < 30 ? "text-green-500" : "text-primary"
                  )}
                >
                  {currentRSI.toFixed(1)}
                </div>
              </div>
              <div className="relative h-20 bg-secondary/20 rounded overflow-hidden">
                {/* Reference lines */}
                <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
                  <line x1="0%" y1="30%" x2="100%" y2="30%" stroke="hsl(0, 72%, 55%)" strokeWidth="1" strokeDasharray="2,2" opacity="0.3" />
                  <line x1="0%" y1="50%" x2="100%" y2="50%" stroke="hsl(var(--border))" strokeWidth="1" opacity="0.2" />
                  <line x1="0%" y1="70%" x2="100%" y2="70%" stroke="hsl(145, 65%, 45%)" strokeWidth="1" strokeDasharray="2,2" opacity="0.3" />

                  {/* RSI Line */}
                  <polyline
                    points={rsi.slice(-30).map((value, i) => {
                      const x = (i / 29) * 100;
                      const y = 100 - value;
                      return `${x},${y}`;
                    }).join(' ')}
                    fill="none"
                    stroke="hsl(var(--primary))"
                    strokeWidth="2"
                    vectorEffect="non-scaling-stroke"
                  />
                </svg>
                <div className="absolute left-1 top-1 text-[8px] text-red-500 opacity-60">70</div>
                <div className="absolute left-1 top-1/2 -translate-y-1/2 text-[8px] text-muted-foreground opacity-60">50</div>
                <div className="absolute left-1 bottom-1 text-[8px] text-green-500 opacity-60">30</div>
              </div>
            </CardContent>
          </Card>

          {/* MACD */}
          <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold text-foreground">MACD</div>
                <div
                  className={cn(
                    "text-xl font-bold",
                    currentMACD > 0 ? "text-green-500" : "text-red-500"
                  )}
                >
                  {currentMACD.toFixed(2)}
                </div>
              </div>
              <div className="relative h-20 bg-secondary/20 rounded overflow-hidden">
                <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
                  {/* Zero line */}
                  <line x1="0%" y1="50%" x2="100%" y2="50%" stroke="hsl(var(--border))" strokeWidth="1" opacity="0.3" />

                  {/* MACD Histogram */}
                  {macd.histogram.slice(-30).map((value, i) => {
                    const maxAbsValue = Math.max(...macd.histogram.slice(-30).map(Math.abs));
                    const normalizedHeight = Math.min((Math.abs(value) / maxAbsValue) * 50, 50);
                    const x = (i / 29) * 100;
                    const isPositive = value >= 0;

                    return (
                      <rect
                        key={i}
                        x={`${x}%`}
                        y={isPositive ? `${50 - normalizedHeight}%` : "50%"}
                        width={`${100 / 29}%`}
                        height={`${normalizedHeight}%`}
                        fill={isPositive ? 'hsl(145, 65%, 45%)' : 'hsl(0, 72%, 55%)'}
                        opacity="0.8"
                      />
                    );
                  })}
                </svg>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Trading Sidebar */}
      <Card className="bg-card/30 backdrop-blur-sm border-primary/40">
        <CardContent className="p-6 space-y-6">
          {/* Game Over Overlay */}
          <AnimatePresence>
            {gameState.isGameOver && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="absolute inset-0 bg-background/95 backdrop-blur-sm z-50 flex flex-col items-center justify-center p-6 rounded-lg"
              >
                <Trophy className="h-16 w-16 text-red-500 mb-4" />
                <h3 className="text-2xl font-bold mb-2">Liquidated</h3>
                <div className="text-center space-y-3 mb-6">
                  <div className="text-sm text-muted-foreground">You ran out of funds</div>
                  <div className="text-lg text-muted-foreground">
                    Better luck next time!
                  </div>
                </div>
                <Button onClick={resetGame} className="w-full gap-2">
                  <RotateCcw className="h-4 w-4" />
                  Try Again
                </Button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Balance Display */}
          <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
            <div className="text-sm text-muted-foreground mb-1">Balance</div>
            <div className="text-3xl font-bold">{formatCurrency(gameState.balance)}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {((gameState.balance / INITIAL_BALANCE) * 100).toFixed(1)}% of initial
            </div>
          </div>

          {/* P&L Display */}
          {gameState.position && (
            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
              <div className="text-sm text-muted-foreground mb-1">Unrealized P&L</div>
              <div
                className={cn(
                  "text-3xl font-bold transition-colors",
                  gameState.pnl > 0 ? "text-green-500" : gameState.pnl < 0 ? "text-red-500" : "text-foreground"
                )}
              >
                {gameState.pnl >= 0 ? "+" : ""}{formatCurrency(gameState.pnl)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {((gameState.pnl / gameState.position.size) * 100).toFixed(2)}% ROI
              </div>
            </div>
          )}

          {/* Position Actions */}
          <div className="space-y-3">
            <div className="text-sm font-semibold text-foreground flex items-center gap-2">
              Position
              {gameState.position && (
                <Badge variant="outline" className="text-xs">
                  {gameState.position.type.toUpperCase()} {gameState.position.leverage}x
                </Badge>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Button
                onClick={() => openPosition('long')}
                disabled={!!gameState.position || gameState.isGameOver}
                className={cn(
                  "w-full h-12 font-semibold transition-all",
                  gameState.position?.type === 'long'
                    ? "bg-green-600 hover:bg-green-700 text-white"
                    : "bg-green-600/20 hover:bg-green-600/30 text-green-600 hover:text-green-500"
                )}
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                Long
              </Button>

              <Button
                onClick={() => openPosition('short')}
                disabled={!!gameState.position || gameState.isGameOver}
                className={cn(
                  "w-full h-12 font-semibold transition-all",
                  gameState.position?.type === 'short'
                    ? "bg-red-600 hover:bg-red-700 text-white"
                    : "bg-red-600/20 hover:bg-red-600/30 text-red-600 hover:text-red-500"
                )}
              >
                <TrendingDown className="h-4 w-4 mr-2" />
                Short
              </Button>
            </div>

            <Button
              onClick={closePosition}
              disabled={!gameState.position || gameState.isGameOver}
              variant="outline"
              className="w-full h-12 border-primary/40 hover:border-primary font-semibold"
            >
              <X className="h-4 w-4 mr-2" />
              Close Position
            </Button>
          </div>

          {/* Timeframe Selection */}
          <div className="space-y-3">
            <div className="text-sm font-semibold text-foreground">Timeframe (min)</div>
            <div className="grid grid-cols-3 gap-2">
              {timeframes.map((tf) => (
                <Button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  variant={timeframe === tf ? "default" : "outline"}
                  size="sm"
                  className="h-9"
                >
                  {tf}m
                </Button>
              ))}
            </div>
          </div>

          {/* Leverage Selection */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-foreground">Leverage</div>
              <div className="text-lg font-bold text-primary">{leverage}x</div>
            </div>
            <Slider
              value={[leverages.indexOf(leverage)]}
              onValueChange={(value) => setLeverage(leverages[value[0]])}
              max={leverages.length - 1}
              step={1}
              disabled={!!gameState.position}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>1x</span>
              <span>10x</span>
              <span>50x</span>
            </div>
            {gameState.position && (
              <div className="text-xs text-muted-foreground text-center">
                Close position to change leverage
              </div>
            )}
          </div>

          {/* Position Stats */}
          {gameState.position && (
            <div className="border-t border-border pt-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Entry Price</span>
                <span className="font-medium">${gameState.position.entryPrice.toFixed(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Current Price</span>
                <span className="font-medium">${currentPrice.toFixed(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Size</span>
                <span className="font-medium">{formatCurrency(gameState.position.size)}</span>
              </div>
            </div>
          )}

          {/* Reset Button */}
          {!gameState.isGameOver && (
            <Button
              onClick={resetGame}
              variant="ghost"
              size="sm"
              className="w-full text-xs text-muted-foreground hover:text-foreground"
            >
              <RotateCcw className="h-3 w-3 mr-2" />
              Reset Game
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
