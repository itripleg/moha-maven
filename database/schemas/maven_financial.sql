-- Maven Financial Tracking Schema
-- Core tables for tracking Maven's trading decisions, portfolio, and performance
-- Git-first architecture: This schema supports queryability, git files are source of truth

-- ============================================================================
-- 1. DECISIONS - Trading decisions Maven makes
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_decisions (
    id SERIAL PRIMARY KEY,

    -- Core decision data (synced from git)
    git_filename TEXT UNIQUE NOT NULL,  -- e.g., "decision_20260114_120530.md"
    decision_type TEXT NOT NULL,        -- buy, sell, hold, rebalance, allocation
    asset TEXT,                          -- BTC, ETH, etc. (nullable for portfolio-wide decisions)
    action TEXT NOT NULL,                -- Specific action taken
    reasoning TEXT NOT NULL,             -- Why this decision was made
    confidence NUMERIC(5,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),

    -- Metadata and context
    metadata JSONB DEFAULT '{}'::jsonb,
    market_context JSONB,               -- Market conditions at decision time

    -- Trade execution (linked to actual trades)
    executed BOOLEAN DEFAULT FALSE,
    execution_count INTEGER DEFAULT 0,  -- How many trades resulted from this decision

    -- Timestamps
    decided_at TIMESTAMPTZ NOT NULL,    -- When decision was made
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for maven_decisions
CREATE INDEX IF NOT EXISTS idx_maven_decisions_decided_at
    ON maven_decisions(decided_at DESC);
CREATE INDEX IF NOT EXISTS idx_maven_decisions_type
    ON maven_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_maven_decisions_asset
    ON maven_decisions(asset);
CREATE INDEX IF NOT EXISTS idx_maven_decisions_risk
    ON maven_decisions(risk_level);
CREATE INDEX IF NOT EXISTS idx_maven_decisions_metadata
    ON maven_decisions USING GIN(metadata jsonb_path_ops);


-- ============================================================================
-- 2. TRADES - Actual trade executions (linked to decisions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_trades (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER REFERENCES maven_decisions(id) ON DELETE SET NULL,

    -- Trade identification
    external_trade_id TEXT,             -- ID from exchange/bot system
    trade_source TEXT NOT NULL,         -- 'motherbot', 'worker_bot', 'simple_ta', 'manual'
    source_bot_id INTEGER,              -- Bot instance ID if applicable

    -- Trade details
    asset TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('long', 'short')),
    position_action TEXT NOT NULL CHECK (position_action IN ('open', 'close', 'increase', 'decrease')),

    -- Prices and sizing
    entry_price NUMERIC(20,8),
    exit_price NUMERIC(20,8),
    size_usd NUMERIC(20,2) NOT NULL,
    size_asset NUMERIC(20,8),
    leverage NUMERIC(5,2) DEFAULT 1.0,

    -- P&L tracking
    realized_pnl_usd NUMERIC(20,2),
    unrealized_pnl_usd NUMERIC(20,2),
    fees_usd NUMERIC(20,2) DEFAULT 0,
    net_pnl_usd NUMERIC(20,2) GENERATED ALWAYS AS (
        COALESCE(realized_pnl_usd, 0) - COALESCE(fees_usd, 0)
    ) STORED,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'liquidated', 'cancelled')),
    close_reason TEXT,                   -- 'profit_target', 'stop_loss', 'decision', 'manual', 'liquidation'

    -- Timestamps
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_pnl CHECK (status = 'open' OR realized_pnl_usd IS NOT NULL)
);

-- Indexes for maven_trades
CREATE INDEX IF NOT EXISTS idx_maven_trades_decision
    ON maven_trades(decision_id);
CREATE INDEX IF NOT EXISTS idx_maven_trades_asset
    ON maven_trades(asset);
CREATE INDEX IF NOT EXISTS idx_maven_trades_status
    ON maven_trades(status);
CREATE INDEX IF NOT EXISTS idx_maven_trades_opened
    ON maven_trades(opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_maven_trades_source
    ON maven_trades(trade_source, source_bot_id);
CREATE INDEX IF NOT EXISTS idx_maven_trades_external_id
    ON maven_trades(external_trade_id) WHERE external_trade_id IS NOT NULL;


-- ============================================================================
-- 3. PORTFOLIO_SNAPSHOTS - Point-in-time portfolio state
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_portfolio_snapshots (
    id SERIAL PRIMARY KEY,

    -- Portfolio totals
    total_value_usd NUMERIC(20,2) NOT NULL,
    available_balance_usd NUMERIC(20,2) NOT NULL,
    margin_used_usd NUMERIC(20,2) DEFAULT 0,
    unrealized_pnl_usd NUMERIC(20,2) DEFAULT 0,

    -- Utilization metrics
    margin_utilization_pct NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_value_usd > 0 THEN (margin_used_usd / total_value_usd) * 100
            ELSE 0
        END
    ) STORED,

    -- Position details (JSONB for flexibility)
    open_positions JSONB DEFAULT '[]'::jsonb,  -- Array of position objects
    position_count INTEGER DEFAULT 0,

    -- Historical comparison
    pnl_24h NUMERIC(20,2),
    pnl_7d NUMERIC(20,2),
    pnl_30d NUMERIC(20,2),
    pnl_all_time NUMERIC(20,2),

    -- Context
    snapshot_type TEXT DEFAULT 'scheduled' CHECK (snapshot_type IN ('scheduled', 'decision', 'manual', 'milestone')),
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    snapshot_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for maven_portfolio_snapshots
CREATE INDEX IF NOT EXISTS idx_maven_portfolio_snapshot_at
    ON maven_portfolio_snapshots(snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_maven_portfolio_type
    ON maven_portfolio_snapshots(snapshot_type);
CREATE INDEX IF NOT EXISTS idx_maven_portfolio_positions
    ON maven_portfolio_snapshots USING GIN(open_positions jsonb_path_ops);


-- ============================================================================
-- 4. PERFORMANCE_METRICS - Aggregated performance stats
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_performance_metrics (
    id SERIAL PRIMARY KEY,

    -- Time period
    period_type TEXT NOT NULL CHECK (period_type IN ('hour', 'day', 'week', 'month', 'all_time')),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,

    -- Trade statistics
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    breakeven_trades INTEGER DEFAULT 0,

    -- P&L metrics
    total_pnl_usd NUMERIC(20,2) DEFAULT 0,
    gross_profit_usd NUMERIC(20,2) DEFAULT 0,
    gross_loss_usd NUMERIC(20,2) DEFAULT 0,
    total_fees_usd NUMERIC(20,2) DEFAULT 0,
    net_pnl_usd NUMERIC(20,2) DEFAULT 0,

    -- Performance ratios
    win_rate_pct NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_trades > 0 THEN (winning_trades::NUMERIC / total_trades) * 100
            ELSE 0
        END
    ) STORED,
    avg_win_usd NUMERIC(20,2),
    avg_loss_usd NUMERIC(20,2),
    profit_factor NUMERIC(10,2),  -- gross_profit / abs(gross_loss)

    -- Risk metrics
    max_drawdown_usd NUMERIC(20,2),
    max_drawdown_pct NUMERIC(5,2),
    sharpe_ratio NUMERIC(10,4),

    -- Asset breakdown
    asset_performance JSONB DEFAULT '{}'::jsonb,  -- Per-asset metrics

    -- Decision quality
    decisions_made INTEGER DEFAULT 0,
    avg_decision_confidence NUMERIC(5,2),
    high_confidence_wins INTEGER DEFAULT 0,  -- Confidence >70 and profit
    low_confidence_losses INTEGER DEFAULT 0,  -- Confidence <40 and loss

    -- Timestamps
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint on period
    UNIQUE(period_type, period_start, period_end)
);

-- Indexes for maven_performance_metrics
CREATE INDEX IF NOT EXISTS idx_maven_performance_period
    ON maven_performance_metrics(period_type, period_start DESC);
CREATE INDEX IF NOT EXISTS idx_maven_performance_calculated
    ON maven_performance_metrics(calculated_at DESC);


-- ============================================================================
-- 5. MARKET_INSIGHTS - Maven's market observations and predictions
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_insights (
    id SERIAL PRIMARY KEY,

    -- Insight details
    insight_type TEXT NOT NULL,  -- 'trend', 'signal', 'risk', 'opportunity', 'reflection'
    asset TEXT,                   -- Specific asset or NULL for market-wide
    content TEXT NOT NULL,        -- The actual insight
    confidence NUMERIC(5,2) CHECK (confidence >= 0 AND confidence <= 100),

    -- Market context
    market_conditions JSONB,      -- Snapshot of market state when insight generated

    -- Validation tracking
    validated BOOLEAN,
    validation_notes TEXT,
    validated_at TIMESTAMPTZ,

    -- Metadata
    tags TEXT[],
    related_decision_id INTEGER REFERENCES maven_decisions(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for maven_insights
CREATE INDEX IF NOT EXISTS idx_maven_insights_type
    ON maven_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_maven_insights_asset
    ON maven_insights(asset);
CREATE INDEX IF NOT EXISTS idx_maven_insights_created
    ON maven_insights(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_maven_insights_tags
    ON maven_insights USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_maven_insights_validated
    ON maven_insights(validated) WHERE validated IS NOT NULL;


-- ============================================================================
-- 6. MAVEN_MEMORY - General event log (git session_log backup)
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_memory (
    id SERIAL PRIMARY KEY,

    -- Event data
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Context linking
    related_decision_id INTEGER REFERENCES maven_decisions(id) ON DELETE SET NULL,
    related_trade_id INTEGER REFERENCES maven_trades(id) ON DELETE SET NULL,

    -- Search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(description, ''))
    ) STORED,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for maven_memory
CREATE INDEX IF NOT EXISTS idx_maven_memory_type
    ON maven_memory(event_type);
CREATE INDEX IF NOT EXISTS idx_maven_memory_created
    ON maven_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_maven_memory_search
    ON maven_memory USING GIN(search_vector);


-- ============================================================================
-- TRIGGERS - Auto-update timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_maven_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER maven_decisions_updated_at
    BEFORE UPDATE ON maven_decisions
    FOR EACH ROW
    EXECUTE FUNCTION update_maven_updated_at();

CREATE TRIGGER maven_trades_updated_at
    BEFORE UPDATE ON maven_trades
    FOR EACH ROW
    EXECUTE FUNCTION update_maven_updated_at();

CREATE TRIGGER maven_insights_updated_at
    BEFORE UPDATE ON maven_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_maven_updated_at();


-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Get current portfolio value
CREATE OR REPLACE FUNCTION maven_get_current_portfolio()
RETURNS TABLE(
    total_value NUMERIC,
    available_balance NUMERIC,
    margin_used NUMERIC,
    unrealized_pnl NUMERIC,
    position_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        total_value_usd,
        available_balance_usd,
        margin_used_usd,
        unrealized_pnl_usd,
        position_count
    FROM maven_portfolio_snapshots
    ORDER BY snapshot_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;


-- Get win rate by asset
CREATE OR REPLACE FUNCTION maven_win_rate_by_asset()
RETURNS TABLE(
    asset TEXT,
    total_trades BIGINT,
    wins BIGINT,
    losses BIGINT,
    win_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.asset,
        COUNT(*) as total_trades,
        COUNT(*) FILTER (WHERE t.realized_pnl_usd > 0) as wins,
        COUNT(*) FILTER (WHERE t.realized_pnl_usd < 0) as losses,
        ROUND(
            (COUNT(*) FILTER (WHERE t.realized_pnl_usd > 0)::NUMERIC / COUNT(*)) * 100,
            2
        ) as win_rate
    FROM maven_trades t
    WHERE t.status = 'closed' AND t.realized_pnl_usd IS NOT NULL
    GROUP BY t.asset
    ORDER BY total_trades DESC;
END;
$$ LANGUAGE plpgsql;


-- Get recent decision performance
CREATE OR REPLACE FUNCTION maven_decision_performance(lookback_days INTEGER DEFAULT 7)
RETURNS TABLE(
    decision_id INTEGER,
    decided_at TIMESTAMPTZ,
    decision_type TEXT,
    asset TEXT,
    confidence NUMERIC,
    trades_executed INTEGER,
    total_pnl NUMERIC,
    outcome TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.decided_at,
        d.decision_type,
        d.asset,
        d.confidence,
        COUNT(t.id)::INTEGER as trades_executed,
        COALESCE(SUM(t.net_pnl_usd), 0) as total_pnl,
        CASE
            WHEN COALESCE(SUM(t.net_pnl_usd), 0) > 0 THEN 'profitable'
            WHEN COALESCE(SUM(t.net_pnl_usd), 0) < 0 THEN 'loss'
            ELSE 'breakeven'
        END as outcome
    FROM maven_decisions d
    LEFT JOIN maven_trades t ON t.decision_id = d.id AND t.status = 'closed'
    WHERE d.decided_at > NOW() - (lookback_days || ' days')::INTERVAL
    GROUP BY d.id, d.decided_at, d.decision_type, d.asset, d.confidence
    ORDER BY d.decided_at DESC;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE maven_decisions IS 'Maven CFO trading decisions - git files are source of truth, this is for queries';
COMMENT ON TABLE maven_trades IS 'Actual trade executions linked to Maven decisions';
COMMENT ON TABLE maven_portfolio_snapshots IS 'Point-in-time portfolio state for tracking growth';
COMMENT ON TABLE maven_performance_metrics IS 'Aggregated performance statistics by time period';
COMMENT ON TABLE maven_insights IS 'Maven market observations, predictions, and reflections';
COMMENT ON TABLE maven_memory IS 'General event log backing up git session_log for queryability';

COMMENT ON COLUMN maven_decisions.git_filename IS 'Source of truth filename in .moha/maven/decisions/';
COMMENT ON COLUMN maven_trades.trade_source IS 'Which bot/system executed this trade';
COMMENT ON COLUMN maven_portfolio_snapshots.snapshot_type IS 'Why this snapshot was taken';
COMMENT ON COLUMN maven_performance_metrics.period_type IS 'Time granularity of aggregation';
