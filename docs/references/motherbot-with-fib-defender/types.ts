/**
 * TypeScript types for LLM Trading Bot
 * Based on SQLite database schema from llm-trading-bot/web/database.py
 */

export interface BotAccountState {
  balance_usd: number;
  equity_usd: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_pnl: number;
  sharpe_ratio: number | null;
  num_positions: number;
  timestamp: string | null;
}

export interface BotPosition {
  id: number;
  coin: string;
  side: "long" | "short";
  quantity_usd: number;
  leverage: number;
  entry_price: number;
  entry_time: string;
  exit_price: number | null;
  exit_time: string | null;
  realized_pnl: number | null;
  status: "open" | "closed" | "failed";
  current_price?: number;
  unrealized_pnl?: number;
  failure_reason?: string;
}

export interface BotDecision {
  id: number;
  timestamp: string;
  coin: string;
  signal: "buy_to_enter" | "sell_to_enter" | "hold" | "close";
  quantity_usd: number;
  leverage: number;
  confidence: number;
  profit_target: number | null;
  stop_loss: number | null;
  invalidation_condition: string | null;
  justification: string;
  raw_response: string | null;
  user_prompt?: string | null;
  system_prompt?: string | null;
  // Strategy configuration
  strategy_mode?: BotStrategyMode;
  prompt_preset?: "aggressive_small_account" | "standard" | "conservative";
  // Execution tracking
  execution_status?: "pending" | "success" | "failed" | "skipped";
  execution_error?: string | null;
  execution_timestamp?: string | null;
  created_at: string;
}

export interface BotStatus {
  id: number;
  timestamp: string;
  status: "running" | "stopped" | "error" | "paused";
  message: string;
  trades_today: number;
  pnl_today: number;
  created_at: string;
}

export interface BotControlResponse {
  success: boolean;
  message: string;
  status?: string;
}

export interface AccountHistoryPoint {
  timestamp: string;
  balance_usd: number;
  equity_usd: number;
  total_pnl: number;
}

export type TradingMode = "paper" | "live";

// New: Bot trading strategy modes
export type BotStrategyMode = "independent" | "shadow" | "hedge";

export interface BotStrategyConfig {
  mode: BotStrategyMode;
  enabled: boolean;
  // Shadow mode: AI trades in same direction with buffering
  shadow_aggression?: number; // 0-100, how aggressive vs safe
  shadow_buffer_percent?: number; // % buffer on position size
  // Hedge mode: AI takes opposite side
  hedge_ratio?: number; // 0-1, how much to hedge (1 = full hedge)
  // Independent mode: AI acts on its own
  independent_capital_allocation?: number; // USD allocated for independent trading
}

export interface BotConfig {
  mode: TradingMode;
  strategy: BotStrategyConfig;
  flask_url: string;
  polling_interval: number; // milliseconds
}

export interface BalanceHistoryPoint {
  timestamp: string;
  balance_usd: number;
  equity_usd: number;
  total_pnl: number;
  ath_balance?: number; // All-time high balance
}

export interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number; // percentage
  avg_win: number; // USD
  avg_loss: number; // USD
  profit_factor: number; // total_wins / total_losses
  max_drawdown: number; // USD
  max_drawdown_percent: number; // percentage
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  current_streak: number; // positive for wins, negative for losses
  best_trade: number; // USD
  worst_trade: number; // USD
}
