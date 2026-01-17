-- Maven Treasury Schema
-- Real-time treasury tracking and market data storage
-- Builds on maven_financial.sql

-- ============================================================================
-- 1. TREASURY_STATE - Current state of MoHa treasury wallet
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_treasury_state (
    id SERIAL PRIMARY KEY,

    -- Wallet identification
    wallet_address TEXT NOT NULL DEFAULT '0xF60c2792722fDae7A8Df69D1b83C40a837E55A4A',
    wallet_type TEXT NOT NULL DEFAULT 'hyperliquid_api' CHECK (wallet_type IN ('hyperliquid_api', 'hyperliquid_main', 'evm')),

    -- Balance tracking
    account_value_usd NUMERIC(20,2) NOT NULL,
    withdrawable_usd NUMERIC(20,2) NOT NULL,
    margin_used_usd NUMERIC(20,2) DEFAULT 0,
    unrealized_pnl_usd NUMERIC(20,2) DEFAULT 0,

    -- Position summary
    active_positions INTEGER DEFAULT 0,
    positions_data JSONB DEFAULT '[]'::jsonb,

    -- Change tracking
    value_change_1h_usd NUMERIC(20,2),
    value_change_24h_usd NUMERIC(20,2),
    value_change_7d_usd NUMERIC(20,2),

    -- Timestamps
    snapshot_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_treasury_state_snapshot
    ON maven_treasury_state(snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_treasury_state_wallet
    ON maven_treasury_state(wallet_address);


-- ============================================================================
-- 2. MARKET_SNAPSHOTS - Hyperliquid market data captures
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_market_snapshots (
    id SERIAL PRIMARY KEY,

    -- Market identification
    coin TEXT NOT NULL,
    market_type TEXT NOT NULL DEFAULT 'perp' CHECK (market_type IN ('perp', 'spot')),

    -- Price data
    mid_price NUMERIC(20,8) NOT NULL,
    mark_price NUMERIC(20,8),
    index_price NUMERIC(20,8),

    -- Funding (perps only)
    funding_rate NUMERIC(20,10),
    predicted_funding NUMERIC(20,10),

    -- Volume/OI
    volume_24h_usd NUMERIC(20,2),
    open_interest_usd NUMERIC(20,2),

    -- L2 summary
    bid_depth_10_usd NUMERIC(20,2),
    ask_depth_10_usd NUMERIC(20,2),
    spread_bps NUMERIC(10,4),

    -- Metadata
    raw_data JSONB,

    -- Timestamps
    snapshot_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_market_snapshots_coin_time
    ON maven_market_snapshots(coin, snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_snapshots_time
    ON maven_market_snapshots(snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_snapshots_type
    ON maven_market_snapshots(market_type);


-- ============================================================================
-- 3. CANDLE_DATA - OHLCV candle storage for analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_candles (
    id SERIAL PRIMARY KEY,

    -- Identification
    coin TEXT NOT NULL,
    interval TEXT NOT NULL CHECK (interval IN ('1m', '5m', '15m', '1h', '4h', '1d')),

    -- OHLCV
    open_price NUMERIC(20,8) NOT NULL,
    high_price NUMERIC(20,8) NOT NULL,
    low_price NUMERIC(20,8) NOT NULL,
    close_price NUMERIC(20,8) NOT NULL,
    volume_usd NUMERIC(20,2) NOT NULL,

    -- Derived
    price_change_pct NUMERIC(10,4) GENERATED ALWAYS AS (
        CASE
            WHEN open_price > 0 THEN ((close_price - open_price) / open_price) * 100
            ELSE 0
        END
    ) STORED,

    -- Timestamps
    candle_open_at TIMESTAMPTZ NOT NULL,
    candle_close_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint
    UNIQUE(coin, interval, candle_open_at)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_candles_coin_interval_time
    ON maven_candles(coin, interval, candle_open_at DESC);


-- ============================================================================
-- 4. TRADING_SIGNALS - TA bot signals and Maven analysis signals
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_trading_signals (
    id SERIAL PRIMARY KEY,

    -- Signal identification
    signal_source TEXT NOT NULL,  -- 'maven_rlm', 'ta_bot', 'observation_bot', 'manual'
    source_bot_id INTEGER,

    -- Signal details
    coin TEXT NOT NULL,
    signal_type TEXT NOT NULL CHECK (signal_type IN ('buy', 'sell', 'hold', 'alert')),
    strength NUMERIC(5,2) CHECK (strength >= 0 AND strength <= 100),

    -- Context
    reasoning TEXT,
    indicators_used TEXT[],
    market_context JSONB,

    -- Execution tracking
    acted_upon BOOLEAN DEFAULT FALSE,
    decision_id INTEGER REFERENCES maven_decisions(id) ON DELETE SET NULL,

    -- Validity
    valid_until TIMESTAMPTZ,
    expired BOOLEAN DEFAULT FALSE,

    -- Timestamps
    generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_signals_coin_time
    ON maven_trading_signals(coin, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_source
    ON maven_trading_signals(signal_source);
CREATE INDEX IF NOT EXISTS idx_signals_type
    ON maven_trading_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_active
    ON maven_trading_signals(coin, expired) WHERE NOT expired;


-- ============================================================================
-- 5. WATCHLIST - Coins Maven is actively monitoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS maven_watchlist (
    id SERIAL PRIMARY KEY,

    -- Coin details
    coin TEXT UNIQUE NOT NULL,
    market_type TEXT NOT NULL DEFAULT 'perp',

    -- Monitoring config
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('high', 'normal', 'low')),
    snapshot_interval_minutes INTEGER DEFAULT 15,

    -- Notes
    watch_reason TEXT,
    tags TEXT[],

    -- Status
    active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    added_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Default watchlist
INSERT INTO maven_watchlist (coin, market_type, priority, watch_reason, tags) VALUES
    ('BTC', 'perp', 'high', 'King of crypto, market leader', ARRAY['major', 'crypto']),
    ('ETH', 'perp', 'high', 'ETH ecosystem, smart contracts', ARRAY['major', 'crypto']),
    ('SOL', 'perp', 'high', 'High performance L1', ARRAY['major', 'crypto']),
    ('NVDA', 'perp', 'high', 'AI chip leader, equity perp', ARRAY['equity', 'ai']),
    ('TSLA', 'perp', 'normal', 'High volatility equity', ARRAY['equity', 'ev']),
    ('COIN', 'perp', 'high', 'Crypto exposure via equity', ARRAY['equity', 'crypto']),
    ('HYPE', 'perp', 'high', 'Hyperliquid native token', ARRAY['major', 'crypto', 'hl'])
ON CONFLICT (coin) DO NOTHING;


-- ============================================================================
-- VIEWS - Quick access queries
-- ============================================================================

-- Current treasury status
CREATE OR REPLACE VIEW maven_treasury_current AS
SELECT
    wallet_address,
    account_value_usd,
    withdrawable_usd,
    margin_used_usd,
    unrealized_pnl_usd,
    active_positions,
    positions_data,
    value_change_24h_usd,
    snapshot_at
FROM maven_treasury_state
ORDER BY snapshot_at DESC
LIMIT 1;

-- Latest prices for watchlist
CREATE OR REPLACE VIEW maven_watchlist_prices AS
SELECT
    w.coin,
    w.priority,
    w.market_type,
    m.mid_price,
    m.funding_rate,
    m.volume_24h_usd,
    m.snapshot_at as price_updated_at
FROM maven_watchlist w
LEFT JOIN LATERAL (
    SELECT * FROM maven_market_snapshots ms
    WHERE ms.coin = w.coin
    ORDER BY ms.snapshot_at DESC
    LIMIT 1
) m ON TRUE
WHERE w.active = TRUE
ORDER BY w.priority DESC, w.coin;

-- Active signals summary
CREATE OR REPLACE VIEW maven_active_signals AS
SELECT
    coin,
    signal_source,
    signal_type,
    strength,
    reasoning,
    generated_at,
    valid_until
FROM maven_trading_signals
WHERE NOT expired
    AND (valid_until IS NULL OR valid_until > NOW())
ORDER BY strength DESC, generated_at DESC;


-- ============================================================================
-- FUNCTIONS - Treasury helpers
-- ============================================================================

-- Record treasury snapshot
CREATE OR REPLACE FUNCTION maven_record_treasury_snapshot(
    p_account_value NUMERIC,
    p_withdrawable NUMERIC,
    p_margin_used NUMERIC,
    p_unrealized_pnl NUMERIC,
    p_positions JSONB
) RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
    v_prev_value NUMERIC;
    v_prev_24h NUMERIC;
    v_prev_7d NUMERIC;
BEGIN
    -- Get previous values for change calculation
    SELECT account_value_usd INTO v_prev_value
    FROM maven_treasury_state
    WHERE snapshot_at >= NOW() - INTERVAL '1 hour'
    ORDER BY snapshot_at DESC
    LIMIT 1;

    SELECT account_value_usd INTO v_prev_24h
    FROM maven_treasury_state
    WHERE snapshot_at >= NOW() - INTERVAL '24 hours'
      AND snapshot_at <= NOW() - INTERVAL '23 hours'
    ORDER BY snapshot_at DESC
    LIMIT 1;

    SELECT account_value_usd INTO v_prev_7d
    FROM maven_treasury_state
    WHERE snapshot_at >= NOW() - INTERVAL '7 days'
      AND snapshot_at <= NOW() - INTERVAL '6 days 23 hours'
    ORDER BY snapshot_at DESC
    LIMIT 1;

    -- Insert new snapshot
    INSERT INTO maven_treasury_state (
        account_value_usd,
        withdrawable_usd,
        margin_used_usd,
        unrealized_pnl_usd,
        active_positions,
        positions_data,
        value_change_1h_usd,
        value_change_24h_usd,
        value_change_7d_usd,
        snapshot_at
    ) VALUES (
        p_account_value,
        p_withdrawable,
        p_margin_used,
        p_unrealized_pnl,
        jsonb_array_length(p_positions),
        p_positions,
        CASE WHEN v_prev_value IS NOT NULL THEN p_account_value - v_prev_value ELSE NULL END,
        CASE WHEN v_prev_24h IS NOT NULL THEN p_account_value - v_prev_24h ELSE NULL END,
        CASE WHEN v_prev_7d IS NOT NULL THEN p_account_value - v_prev_7d ELSE NULL END,
        NOW()
    ) RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;


-- Get treasury performance summary
CREATE OR REPLACE FUNCTION maven_treasury_performance(p_days INTEGER DEFAULT 30)
RETURNS TABLE(
    start_value NUMERIC,
    end_value NUMERIC,
    absolute_change NUMERIC,
    percentage_change NUMERIC,
    high_water_mark NUMERIC,
    low_water_mark NUMERIC,
    snapshot_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT account_value_usd FROM maven_treasury_state
         WHERE snapshot_at >= NOW() - (p_days || ' days')::INTERVAL
         ORDER BY snapshot_at ASC LIMIT 1) as start_value,
        (SELECT account_value_usd FROM maven_treasury_state
         ORDER BY snapshot_at DESC LIMIT 1) as end_value,
        (SELECT account_value_usd FROM maven_treasury_state
         ORDER BY snapshot_at DESC LIMIT 1) -
        (SELECT account_value_usd FROM maven_treasury_state
         WHERE snapshot_at >= NOW() - (p_days || ' days')::INTERVAL
         ORDER BY snapshot_at ASC LIMIT 1) as absolute_change,
        CASE
            WHEN (SELECT account_value_usd FROM maven_treasury_state
                  WHERE snapshot_at >= NOW() - (p_days || ' days')::INTERVAL
                  ORDER BY snapshot_at ASC LIMIT 1) > 0
            THEN (
                ((SELECT account_value_usd FROM maven_treasury_state ORDER BY snapshot_at DESC LIMIT 1) -
                 (SELECT account_value_usd FROM maven_treasury_state
                  WHERE snapshot_at >= NOW() - (p_days || ' days')::INTERVAL
                  ORDER BY snapshot_at ASC LIMIT 1)) /
                (SELECT account_value_usd FROM maven_treasury_state
                 WHERE snapshot_at >= NOW() - (p_days || ' days')::INTERVAL
                 ORDER BY snapshot_at ASC LIMIT 1)
            ) * 100
            ELSE 0
        END as percentage_change,
        MAX(mts.account_value_usd) as high_water_mark,
        MIN(mts.account_value_usd) as low_water_mark,
        COUNT(*) as snapshot_count
    FROM maven_treasury_state mts
    WHERE mts.snapshot_at >= NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE maven_treasury_state IS 'Real-time MoHa treasury wallet state snapshots';
COMMENT ON TABLE maven_market_snapshots IS 'Hyperliquid market data captures for analysis';
COMMENT ON TABLE maven_candles IS 'OHLCV candle data storage';
COMMENT ON TABLE maven_trading_signals IS 'Trading signals from all sources (bots, Maven RLM, etc)';
COMMENT ON TABLE maven_watchlist IS 'Coins Maven actively monitors';

COMMENT ON VIEW maven_treasury_current IS 'Current treasury state (latest snapshot)';
COMMENT ON VIEW maven_watchlist_prices IS 'Watchlist with latest prices';
COMMENT ON VIEW maven_active_signals IS 'Non-expired trading signals';
