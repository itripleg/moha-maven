"""
SQLite database layer for Motherhaven trading bot.

This module provides database initialization and management for:
- Standard Config Tables
- Autonomous Data Tables
- Position Data Tables
- Bot Status Data Tables
- Data Collection Categories
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional

# Global database path
_db_path: Optional[Path] = None


def set_database_path(mode: str = "paper") -> None:
    """Set the database file path based on trading mode."""
    global _db_path
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    _db_path = data_dir / f"motherhaven_{mode}.db"
    print(f"[DATABASE] Path set to: {_db_path}")


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    if _db_path is None:
        raise RuntimeError("Database path not set. Call set_database_path() first.")

    conn = sqlite3.connect(str(_db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize database schema."""
    if _db_path is None:
        raise RuntimeError("Database path not set. Call set_database_path() first.")

    conn = get_connection()
    cursor = conn.cursor()

    # ============================================================================
    # STANDARD CONFIG TABLES
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ============================================================================
    # POSITION DATA TABLES
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT NOT NULL,
            side TEXT,
            entry_price REAL,
            current_price REAL,
            size REAL,
            leverage REAL,
            pnl REAL,
            pnl_percent REAL,
            liquidation_price REAL,
            margin_used REAL,
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            status TEXT DEFAULT 'open',
            wallet_address TEXT,
            initiated_by TEXT DEFAULT 'bot'
        )
    """)

    # Migration: Add new columns to existing positions table
    try:
        cursor.execute("ALTER TABLE positions ADD COLUMN wallet_address TEXT")
        print("[DATABASE] Added wallet_address column to positions table")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE positions ADD COLUMN initiated_by TEXT DEFAULT 'bot'")
        print("[DATABASE] Added initiated_by column to positions table")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # ============================================================================
    # TA DATA TABLES
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL,
            UNIQUE(asset, timeframe, timestamp)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            indicator_type TEXT NOT NULL,
            value REAL,
            metadata TEXT,
            UNIQUE(asset, timeframe, timestamp, indicator_type)
        )
    """)

    # ============================================================================
    # AUTONOMOUS DATA TABLES
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            asset TEXT NOT NULL,
            decision TEXT NOT NULL,
            reasoning TEXT,
            confidence REAL,
            strategy_mode TEXT,
            cycle_number INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            asset TEXT NOT NULL,
            price REAL,
            volume_24h REAL,
            funding_rate REAL,
            open_interest REAL,
            data JSON
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            asset TEXT NOT NULL,
            vision_text TEXT,
            market_context TEXT,
            ta_summary TEXT
        )
    """)

    # ============================================================================
    # BOT STATUS DATA TABLES
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            state TEXT NOT NULL,
            cycle_count INTEGER,
            error_message TEXT,
            active_positions INTEGER,
            total_pnl REAL
        )
    """)

    # ============================================================================
    # PROMPT STORAGE TABLES
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts_cooperative (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prompt_text TEXT NOT NULL,
            active BOOLEAN DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts_hedging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prompt_text TEXT NOT NULL,
            active BOOLEAN DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts_entry_exit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prompt_text TEXT NOT NULL,
            active BOOLEAN DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts_date_collecting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prompt_text TEXT NOT NULL,
            active BOOLEAN DEFAULT 1
        )
    """)

    # ============================================================================
    # USER INPUT TABLE
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_input (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            message_type TEXT NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived_at TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    """)

    # ============================================================================
    # ACCOUNT STATE TABLE
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            balance REAL,
            equity REAL,
            margin_used REAL,
            available_margin REAL,
            unrealized_pnl REAL,
            realized_pnl REAL,
            total_pnl REAL,
            account_value REAL,
            data JSON
        )
    """)

    # ============================================================================
    # STRATEGY PRESETS TABLE
    # ============================================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            strategy_type TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    print(f"[DATABASE] Schema initialized at {_db_path}")


def save_strategy_preset(name: str, strategy_type: str, prompt_text: str, description: str = None) -> int:
    """Save a new strategy preset."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO strategy_presets (name, strategy_type, prompt_text, description)
        VALUES (?, ?, ?, ?)
    """, (name, strategy_type, prompt_text, description))
    preset_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return preset_id


def query_strategy_presets() -> list:
    """Query all strategy presets."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM strategy_presets
        ORDER BY name ASC
    """)
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_strategy_preset(name: str) -> Optional[dict]:
    """Get a specific strategy preset by name."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM strategy_presets
        WHERE name = ?
    """, (name,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None


# ============================================================================
# BOT CONFIG FUNCTIONS
# ============================================================================

def get_bot_config(key: str = None):
    """
    Get bot configuration from database.
    If key is None, returns all config as a dict.
    If key is provided, returns that specific value or None.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if key is None:
        # Return all config
        cursor.execute("SELECT key, value FROM bot_config")
        results = cursor.fetchall()
        conn.close()
        return {row['key']: row['value'] for row in results}
    else:
        # Return specific key
        cursor.execute("SELECT value FROM bot_config WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result['value'] if result else None


def set_bot_config(key: str, value: str) -> None:
    """Set a bot configuration value in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO bot_config (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (key, str(value)))
    conn.commit()
    conn.close()


def update_bot_config(config_dict: dict) -> None:
    """Update multiple bot config values at once."""
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in config_dict.items():
        cursor.execute("""
            INSERT OR REPLACE INTO bot_config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, str(value)))
    conn.commit()
    conn.close()


class RuntimeConfig:
    """
    Configuration loader that reads from database (primary) with fallback to .env.
    This enables remote configuration via web UI without needing shell access.
    """

    def __init__(self):
        from config import settings as env_settings
        self._env_settings = env_settings
        self._cache = {}
        self._cache_time = None
        self._cache_ttl = 5  # Cache for 5 seconds to avoid excessive DB reads

    def _load_from_db(self):
        """Load config from database with caching."""
        import time
        current_time = time.time()

        # Return cached config if still valid
        if self._cache and self._cache_time and (current_time - self._cache_time) < self._cache_ttl:
            return self._cache

        # Ensure database is initialized
        try:
            if not _db_path:
                set_database_path()
                init_database()
        except:
            pass  # Database will be initialized by Flask on first request

        # Load from database
        try:
            config_dict = get_bot_config()
            self._cache = config_dict
            self._cache_time = current_time
            return config_dict
        except RuntimeError:
            # Database not ready yet, return empty dict (will fall back to .env)
            return {}

    def _get(self, key: str, default=None, type_func=str):
        """Get a config value from DB (primary) or .env (fallback)."""
        config = self._load_from_db()
        value = config.get(key)

        if value is not None:
            # Found in database
            try:
                return type_func(value)
            except (ValueError, TypeError):
                print(f"[CONFIG WARNING] Invalid value for {key}: {value}, using default")
                return default

        # Fallback to .env
        env_value = getattr(self._env_settings, key, default)
        return env_value if env_value is not None else default

    @property
    def hyperliquid_wallet_private_key(self) -> str:
        return self._get('hyperliquid_wallet_private_key', '')

    @property
    def hyperliquid_account_address(self) -> str:
        return self._get('hyperliquid_account_address', '')

    @property
    def hyperliquid_testnet(self) -> bool:
        val = self._get('hyperliquid_testnet', 'true')
        return str(val).lower() == 'true'

    @property
    def anthropic_api_key(self) -> str:
        return self._get('anthropic_api_key', '')

    @property
    def trading_mode(self) -> str:
        return self._get('trading_mode', 'paper')

    @property
    def max_position_size_usd(self) -> float:
        return self._get('max_position_size_usd', 500.0, float)

    @property
    def max_leverage(self) -> int:
        return self._get('max_leverage', 5, int)

    @property
    def execution_interval_seconds(self) -> int:
        return self._get('execution_interval_seconds', 300, int)

    @property
    def trading_assets(self) -> str:
        return self._get('trading_assets', 'BTC,ETH,SOL')

    def get_trading_assets(self) -> list[str]:
        """Get trading assets as list."""
        return [asset.strip() for asset in self.trading_assets.split(",")]

    def is_live_trading(self) -> bool:
        """Check if live trading is enabled."""
        return self.trading_mode.lower() == "live"

    def reload(self):
        """Force reload config from database (clear cache)."""
        self._cache = {}
        self._cache_time = None


# Global runtime config instance
runtime_config = RuntimeConfig()


# ============================================================================
# SEEDING & DEFAULTS
# ============================================================================

DEFAULT_CONFIG = {
    # Runtime trading config (can be changed on the fly)
    'execution_interval_seconds': 300,  # 5 minutes
    'max_open_positions': 3,
    'min_margin_usd': 20.0,
    'max_margin_usd': 200.0,
    'min_balance_threshold': 10.0,
    'trading_mode': 'paper',
    'max_position_size_usd': 500.0,
    'max_leverage': 5,
    'trading_assets': 'BTC,ETH,SOL',
    'hyperliquid_testnet': 'true',
}

DEFAULT_PROMPTS = {
    'cooperative': """You are a Cooperative Trading Bot engaged in a collaborative trading session.
Your goal is to analyze the market data and make trading decisions that balance risk and reward.
You should look for high-probability setups confirmed by multiple indicators.
Prioritize capital preservation but be willing to take calculated risks when conditions significantly favor a directional move.
Explain your reasoning clearly, citing specific indicators and price levels.""",

    'hedging': """You are a Hedging Bot responsible for protecting capital.
Your primary goal is to minimize downside risk.
Look for opportunities to hedge existing exposure or take low-risk, mean-reverting trades.
Avoid aggressive directional bets.
Prioritize short-duration trades to capture small inefficiencies while remaining market-neutral where possible.""",

    'entry_exit': """You are an Entry/Exit Specialist.
Your sole focus is identifying optimal entry and exit points with precision.
Ignore broad macroeconomic trends unless they immediately impact the current setup.
Focus heavily on technical levels: Support/Resistance, Fibonacci retracements, and Order blocks.
Be strict with Stop Loss and Take Profit levels.""",

    'date_collecting': """You are a Data Collector.
DO NOT TRADE.
Your role is to observe the market, log significant events, and potential setups for future reference.
Analyze the price action and indicators as if you were going to trade, but output a 'HOLD' decision with your analysis.
Focus on identifying determining factors for potential future volatility."""
}

def seed_defaults() -> None:
    """Populate database with default values if tables are empty."""
    from config import settings as env_settings

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Seed Bot Config
        # Use .env values if provided, otherwise use defaults
        # This logic ensures new config keys are added even if table exists
        print("[DATABASE] Checking bot config...")

        # Merge env settings with defaults
        config_to_seed = DEFAULT_CONFIG.copy()

        # Override with .env values if provided
        config_to_seed['execution_interval_seconds'] = env_settings.execution_interval_seconds
        config_to_seed['trading_mode'] = env_settings.trading_mode
        config_to_seed['max_position_size_usd'] = env_settings.max_position_size_usd
        config_to_seed['max_leverage'] = env_settings.max_leverage
        config_to_seed['trading_assets'] = env_settings.trading_assets
        config_to_seed['hyperliquid_testnet'] = str(env_settings.hyperliquid_testnet).lower()

        # Add API keys if provided in .env (can also be set via web UI later)
        if env_settings.hyperliquid_wallet_private_key:
            config_to_seed['hyperliquid_wallet_private_key'] = env_settings.hyperliquid_wallet_private_key
        if env_settings.anthropic_api_key:
            config_to_seed['anthropic_api_key'] = env_settings.anthropic_api_key

        # Insert or update each config key (INSERT OR IGNORE to avoid overwriting existing values)
        for key, value in config_to_seed.items():
            cursor.execute("SELECT COUNT(*) FROM bot_config WHERE key = ?", (key,))
            if cursor.fetchone()[0] == 0:
                print(f"[DATABASE] Seeding config: {key}")
                cursor.execute("""
                    INSERT INTO bot_config (key, value)
                    VALUES (?, ?)
                """, (key, str(value)))
        
        # 2. Seed Prompts
        # Map preset types to table names (must match app.py logic)
        table_map = {
            'cooperative': 'prompts_cooperative',
            'hedging': 'prompts_hedging',
            'entry_exit': 'prompts_entry_exit',
            'date_collecting': 'prompts_date_collecting'
        }
        
        for preset_type, prompt_text in DEFAULT_PROMPTS.items():
            table_name = table_map.get(preset_type)
            if table_name:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                if cursor.fetchone()[0] == 0:
                    print(f"[DATABASE] Seeding default prompt for {preset_type}...")
                    cursor.execute(f"""
                        INSERT INTO {table_name} (prompt_text, active)
                        VALUES (?, 1)
                    """, (prompt_text,))

        # 3. Seed Standard Strategy Presets (so they appear in custom list/manager if needed)
        # Note: We don't strictly need to put standard presets in strategy_presets table 
        # because the API merges them from code constants, but adding them here 
        # allows users to "edit" the standard ones (which creates a custom override usually)
        # For now, we leave strategy_presets empty so we can distinguish "Standard" vs "Custom" clearly.

        conn.commit()
    except Exception as e:
        print(f"[DATABASE ERROR] Failed to seed defaults: {e}")
    finally:
        conn.close()


def query_latest_positions(limit: int = 10) -> list:
    """Query latest positions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM positions
        ORDER BY opened_at DESC
        LIMIT ?
    """, (limit,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def save_trading_decision(asset: str, decision: str, reasoning: str = "", confidence: float = 0.0, strategy_mode: str = None, cycle_number: int = None) -> None:
    """Save a trading decision to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trading_decisions (asset, decision, reasoning, confidence, strategy_mode, cycle_number)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (asset, decision, reasoning, confidence, strategy_mode, cycle_number))
    conn.commit()
    conn.close()


# ============================================================================
# CANDLE DATA FUNCTIONS
# ============================================================================

def save_candle(asset: str, timeframe: str, timestamp: str, open: float, high: float, low: float, close: float, volume: float = None) -> None:
    """Save a candle to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO candles (asset, timeframe, timestamp, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (asset, timeframe, timestamp, open, high, low, close, volume))
    conn.commit()
    conn.close()


def query_candles(asset: str, timeframe: str, limit: int = 100) -> list:
    """Query recent candles for an asset and timeframe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM candles
        WHERE asset = ? AND timeframe = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (asset, timeframe, limit))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================================================
# INDICATOR FUNCTIONS
# ============================================================================

def save_indicator(asset: str, timeframe: str, indicator_type: str, value: float, metadata: str = None) -> None:
    """Save an indicator value to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO indicators (asset, timeframe, indicator_type, value, metadata)
        VALUES (?, ?, ?, ?, ?)
    """, (asset, timeframe, indicator_type, value, metadata))
    conn.commit()
    conn.close()


def query_indicators(asset: str, timeframe: str, indicator_type: str = None, limit: int = 100) -> list:
    """Query indicators for an asset."""
    conn = get_connection()
    cursor = conn.cursor()

    if indicator_type:
        cursor.execute("""
            SELECT * FROM indicators
            WHERE asset = ? AND timeframe = ? AND indicator_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (asset, timeframe, indicator_type, limit))
    else:
        cursor.execute("""
            SELECT * FROM indicators
            WHERE asset = ? AND timeframe = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (asset, timeframe, limit))

    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================================================
# MARKET SNAPSHOT FUNCTIONS
# ============================================================================

def save_market_snapshot(asset: str, price: float, volume_24h: float = None, funding_rate: float = None, open_interest: float = None, data: str = None) -> None:
    """Save a market snapshot."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO market_snapshots (asset, price, volume_24h, funding_rate, open_interest, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (asset, price, volume_24h, funding_rate, open_interest, data))
    conn.commit()
    conn.close()


def query_market_snapshots(asset: str, limit: int = 100) -> list:
    """Query recent market snapshots."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM market_snapshots
        WHERE asset = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (asset, limit))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================================================
# VISION FUNCTIONS
# ============================================================================

def save_vision(asset: str, vision_text: str, market_context: str = None, ta_summary: str = None) -> None:
    """Save a trading vision."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO visions (asset, vision_text, market_context, ta_summary)
        VALUES (?, ?, ?, ?)
    """, (asset, vision_text, market_context, ta_summary))
    conn.commit()
    conn.close()


def query_visions(asset: str, limit: int = 10) -> list:
    """Query recent visions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM visions
        WHERE asset = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (asset, limit))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================================================
# PROMPT MANAGEMENT FUNCTIONS
# ============================================================================

def save_prompt(prompt_type: str, prompt_text: str) -> int:
    """Save a prompt to the appropriate table."""
    table_map = {
        'cooperative': 'prompts_cooperative',
        'hedging': 'prompts_hedging',
        'entry_exit': 'prompts_entry_exit',
        'date_collecting': 'prompts_date_collecting'
    }

    if prompt_type not in table_map:
        raise ValueError(f"Invalid prompt_type: {prompt_type}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO {table_map[prompt_type]} (prompt_text)
        VALUES (?)
    """, (prompt_text,))
    prompt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prompt_id


def query_active_prompts(prompt_type: str) -> list:
    """Query active prompts of a specific type."""
    table_map = {
        'cooperative': 'prompts_cooperative',
        'hedging': 'prompts_hedging',
        'entry_exit': 'prompts_entry_exit',
        'date_collecting': 'prompts_date_collecting'
    }

    if prompt_type not in table_map:
        raise ValueError(f"Invalid prompt_type: {prompt_type}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT * FROM {table_map[prompt_type]}
        WHERE active = 1
        ORDER BY created_at DESC
    """)
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================================================
# USER INPUT FUNCTIONS
# ============================================================================

def get_active_user_input() -> Optional[dict]:
    """Get the active user input if one exists."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM user_input
        WHERE active = 1 AND archived_at IS NULL
        ORDER BY created_at DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None


def save_user_input(message: str, message_type: str, image_path: str = None) -> int:
    """Save a new user input to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_input (message, message_type, image_path)
        VALUES (?, ?, ?)
    """, (message, message_type, image_path))
    input_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return input_id


def archive_user_input(input_id: int) -> None:
    """Archive a user input by ID."""
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_input
        SET active = 0, archived_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), input_id))
    conn.commit()
    conn.close()


# ============================================================================
# POSITION QUERY FUNCTIONS
# ============================================================================

def get_open_positions() -> list:
    """Get all currently open positions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM positions
        WHERE status = 'open'
        ORDER BY opened_at DESC
    """)
    results = cursor.fetchall()
    conn.close()

    # Convert to list of dicts with legacy field names for compatibility
    positions = []
    for row in results:
        pos = dict(row)
        # Add legacy field mappings for bot_runner.py compatibility
        pos['coin'] = pos.get('asset')
        pos['quantity_usd'] = pos.get('size')
        pos['entry_time'] = pos.get('opened_at')
        positions.append(pos)

    return positions


def create_position(asset: str, side: str, entry_price: float, size: float,
                   leverage: float = 1.0, wallet_address: str = None,
                   initiated_by: str = 'bot') -> int:
    """Create a new position in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO positions (asset, side, entry_price, current_price, size, leverage,
                              wallet_address, initiated_by, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')
    """, (asset, side, entry_price, entry_price, size, leverage, wallet_address, initiated_by))
    position_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return position_id


def update_position(position_id: int, current_price: float = None, pnl: float = None,
                   pnl_percent: float = None, status: str = None) -> None:
    """Update an existing position."""
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if current_price is not None:
        updates.append("current_price = ?")
        params.append(current_price)

    if pnl is not None:
        updates.append("pnl = ?")
        params.append(pnl)

    if pnl_percent is not None:
        updates.append("pnl_percent = ?")
        params.append(pnl_percent)

    if status is not None:
        updates.append("status = ?")
        params.append(status)
        if status == 'closed':
            updates.append("closed_at = ?")
            params.append(datetime.now().isoformat())

    if not updates:
        conn.close()
        return

    params.append(position_id)
    query = f"UPDATE positions SET {', '.join(updates)} WHERE id = ?"

    cursor.execute(query, params)
    conn.commit()
    conn.close()


# ============================================================================
# TRADING DECISION QUERY FUNCTIONS
# ============================================================================

def query_trading_decisions(asset: str = None, limit: int = 100) -> list:
    """Query trading decisions with optional asset filter."""
    conn = get_connection()
    cursor = conn.cursor()

    if asset:
        cursor.execute("""
            SELECT * FROM trading_decisions
            WHERE asset = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (asset, limit))
    else:
        cursor.execute("""
            SELECT * FROM trading_decisions
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================================================
# ACCOUNT STATE FUNCTIONS
# ============================================================================

def save_account_state(balance: float = None, equity: float = None, margin_used: float = None,
                       available_margin: float = None, unrealized_pnl: float = None,
                       realized_pnl: float = None, total_pnl: float = None,
                       account_value: float = None, data: str = None) -> None:
    """Save an account state snapshot."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO account_states (balance, equity, margin_used, available_margin,
                                    unrealized_pnl, realized_pnl, total_pnl, account_value, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (balance, equity, margin_used, available_margin, unrealized_pnl,
          realized_pnl, total_pnl, account_value, data))
    conn.commit()
    conn.close()


def query_account_states(limit: int = 100) -> list:
    """Query recent account state snapshots."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM account_states
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_db_path() -> str:
    """Get the database file path."""
    if _db_path is None:
        raise RuntimeError("Database path not set. Call set_database_path() first.")
    return str(_db_path)
