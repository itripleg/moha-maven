"""
Trading bot main cycle logic.
"""

import time
import threading
from datetime import datetime
from enum import Enum
from typing import Optional
from config import settings  # Infrastructure settings (Flask port, etc.)
from database import runtime_config as config  # Trading config from database


class BotState(Enum):
    """Bot state machine."""
    STOPPED = "stopped"
    IDLE = "idle"          # Bot running but not trading (monitoring mode)
    TRADING = "trading"    # Bot running and actively trading
    PAUSED = "paused"
    ERROR = "error"


class TradingBot:
    """Main trading bot with cycle control."""

    def __init__(self):
        self.state = BotState.STOPPED
        self.thread: Optional[threading.Thread] = None
        self.last_cycle_time: Optional[datetime] = None
        self.cycle_interval: int = 0  # Store the interval used for current cycle
        self.cycle_count = 0
        self.error_message: Optional[str] = None

        # Initialize components (will add later)
        # self.executor = None
        # self.database = None

    def start(self):
        """Start the bot in a background thread."""
        if self.state == BotState.TRADING or self.state == BotState.IDLE:
            raise ValueError("Bot is already running")

        if self.state == BotState.PAUSED:
            # Resume from paused state
            self.state = BotState.IDLE
            return

        # Start new bot thread in IDLE mode
        self.state = BotState.IDLE
        self.thread = threading.Thread(target=self._run_cycle, daemon=True)
        self.thread.start()
        print(f"[BOT] Started in IDLE mode at {datetime.now()}", flush=True)

    def pause(self):
        """Pause the bot (keeps thread alive)."""
        if self.state != BotState.TRADING:
            raise ValueError("Bot is not trading")

        self.state = BotState.PAUSED
        print(f"[BOT] Paused at {datetime.now()}", flush=True)

    def resume(self):
        """Resume from paused state."""
        if self.state != BotState.PAUSED:
            raise ValueError("Bot is not paused")

        self.state = BotState.TRADING
        print(f"[BOT] Resumed at {datetime.now()}", flush=True)

    def stop(self):
        """Stop the bot completely."""
        self.state = BotState.STOPPED
        if self.thread:
            self.thread.join(timeout=5)
        print(f"[BOT] Stopped at {datetime.now()}", flush=True)

    def get_status(self) -> dict:
        """Get current bot status."""
        return {
            "state": self.state.value,
            "last_cycle_time": self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            "cycle_count": self.cycle_count,
            "error_message": self.error_message,
            "execution_interval_seconds": config.execution_interval_seconds,
            "next_cycle_in_seconds": self._get_seconds_until_next_cycle() if self.state in (BotState.TRADING, BotState.IDLE) else None
        }

    def _get_seconds_until_next_cycle(self) -> Optional[int]:
        """Calculate seconds until next cycle."""
        if not self.last_cycle_time or not self.cycle_interval:
            return 0

        elapsed = (datetime.now() - self.last_cycle_time).total_seconds()
        remaining = self.cycle_interval - elapsed
        return max(0, int(remaining))

    def _run_cycle(self):
        """Main bot cycle (runs in background thread)."""
        print(f"[BOT] Initializing bot...", flush=True)

        try:
            self._initialize()
            print(f"[BOT] Initialization complete", flush=True)
        except Exception as e:
            self.state = BotState.ERROR
            self.error_message = f"Initialization failed: {str(e)}"
            print(f"[BOT ERROR] {self.error_message}", flush=True)
            return

        # Main cycle loop
        while self.state != BotState.STOPPED:
            # Check if paused or idle
            if self.state == BotState.PAUSED:
                print(f"[BOT] Idling (paused)...", flush=True)
                time.sleep(5)  # Check every 5 seconds if resumed
                continue

            if self.state == BotState.IDLE:
                # Execute monitoring cycle (data observation mode - no trading)
                print(f"\n[BOT] ===== Monitoring Cycle {self.cycle_count + 1} =====", flush=True)
                print(f"[BOT] Bot in IDLE mode (data observation only, no trading)", flush=True)

                # Fetch market data
                print(f"[BOT] Fetching market data...", flush=True)
                try:
                    assets = config.get_trading_assets()
                    market_data = {}

                    for asset in assets:
                        try:
                            # Fetch ticker data
                            ticker = self.market_fetcher.fetch_ticker_data(asset)
                            print(f"[BOT]   {asset}: ${ticker['price']:.2f}", flush=True)

                            # Fetch candles (1h timeframe, last 100 candles)
                            candles = self.market_fetcher.fetch_candles(asset, interval="1h", limit=100)
                            print(f"[BOT]   {asset}: Fetched {len(candles)} candles", flush=True)

                            # Save to database
                            self.market_fetcher.save_to_database(asset, ticker, candles)

                            market_data[asset] = {
                                'ticker': ticker,
                                'candles': candles
                            }

                        except Exception as e:
                            print(f"[BOT WARNING] Failed to fetch {asset} data: {e}", flush=True)

                    if not market_data:
                        print(f"[BOT WARNING] Failed to fetch any market data", flush=True)

                except Exception as e:
                    print(f"[BOT ERROR] Market data fetch failed: {e}", flush=True)

                # Fetch account state
                try:
                    print(f"[BOT] Getting account state...", flush=True)
                    account_state = self.account_fetcher.fetch_account_state()
                    positions = self.account_fetcher.fetch_positions()

                    print(f"[BOT]   Account Value: ${account_state['account_value']:.2f}", flush=True)
                    print(f"[BOT]   Balance: ${account_state['balance']:.2f}", flush=True)
                    print(f"[BOT]   Unrealized PnL: ${account_state['unrealized_pnl']:.2f}", flush=True)
                    print(f"[BOT]   Open Positions: {len(positions)}", flush=True)

                    for pos in positions:
                        print(f"[BOT]     {pos['asset']} {pos['side']}: {pos['size']} @ ${pos['current_price']:.2f} (PnL: ${pos['pnl']:.2f})", flush=True)

                    # Save to database
                    self.account_fetcher.save_to_database(account_state, positions)

                except Exception as e:
                    print(f"[BOT WARNING] Account state fetch failed: {e}", flush=True)

                # Store interval and time together for consistent countdown calculation
                wait_time = config.execution_interval_seconds
                self.cycle_interval = wait_time
                self.last_cycle_time = datetime.now()
                self.cycle_count += 1

                # Wait for next cycle with countdown
                print(f"[BOT] Data observation complete. Waiting {wait_time}s until next cycle...", flush=True)

                # Print countdown every 30 seconds during wait
                elapsed = 0
                countdown_interval = 30
                while elapsed < wait_time and self.state == BotState.IDLE:
                    sleep_time = min(countdown_interval, wait_time - elapsed)
                    time.sleep(sleep_time)
                    elapsed += sleep_time

                    if elapsed < wait_time and self.state == BotState.IDLE:
                        remaining = wait_time - elapsed
                        print(f"[BOT] IDLE: {remaining}s until next monitoring cycle...", flush=True)
                continue

            try:
                # Execute one trading cycle
                print(f"\n[BOT] ===== Trading Cycle {self.cycle_count + 1} =====", flush=True)
                self._execute_cycle()

                # Store interval and time together for consistent countdown calculation
                wait_time = config.execution_interval_seconds
                self.cycle_interval = wait_time
                self.last_cycle_time = datetime.now()
                self.cycle_count += 1

                # Wait for next cycle with countdown
                print(f"[BOT] Cycle complete. Waiting {wait_time}s until next cycle...", flush=True)

                # Print countdown every 30 seconds during wait
                elapsed = 0
                countdown_interval = 30
                while elapsed < wait_time and (self.state == BotState.TRADING or self.state == BotState.IDLE):
                    sleep_time = min(countdown_interval, wait_time - elapsed)
                    time.sleep(sleep_time)
                    elapsed += sleep_time

                    if elapsed < wait_time and self.state == BotState.TRADING:
                        remaining = wait_time - elapsed
                        print(f"[BOT] TRADING: {remaining}s until next cycle...", flush=True)

            except Exception as e:
                self.state = BotState.ERROR
                self.error_message = f"Cycle error: {str(e)}"
                print(f"[BOT ERROR] {self.error_message}", flush=True)
                break

        print(f"[BOT] Exiting bot cycle", flush=True)

    def _initialize(self):
        """Initialize bot components."""
        print(f"[BOT] Configuration:", flush=True)
        print(f"  - Trading Mode: {config.trading_mode}", flush=True)
        print(f"  - Testnet: {config.hyperliquid_testnet}", flush=True)
        print(f"  - Max Position Size: ${config.max_position_size_usd}", flush=True)
        print(f"  - Max Leverage: {config.max_leverage}x", flush=True)
        print(f"  - Execution Interval: {config.execution_interval_seconds}s", flush=True)
        print(f"  - Trading Assets: {config.get_trading_assets()}", flush=True)

        # Initialize Hyperliquid client
        try:
            if not config.hyperliquid_wallet_private_key:
                raise ValueError("Hyperliquid wallet private key not configured")

            from hl_fetchers.hyperliquid_client import HyperliquidClient
            from hl_fetchers.market_fetcher import MarketFetcher
            from hl_fetchers.account_fetcher import AccountFetcher

            self.hl_client = HyperliquidClient(
                private_key=config.hyperliquid_wallet_private_key,
                account_address=config.hyperliquid_account_address or None,
                use_testnet=config.hyperliquid_testnet
            )

            # Test connection
            print(f"[BOT] Testing Hyperliquid connection...", flush=True)
            if not self.hl_client.test_connection():
                raise ConnectionError("Failed to connect to Hyperliquid API")

            network = "Testnet" if config.hyperliquid_testnet else "Mainnet"
            print(f"[BOT] Connected to Hyperliquid ({network})", flush=True)
            print(f"[BOT] Account: {self.hl_client.get_account_address()}", flush=True)
            if self.hl_client.get_account_address() != self.hl_client.get_wallet_address():
                print(f"[BOT] API Wallet: {self.hl_client.get_wallet_address()}", flush=True)

            # Initialize fetchers
            self.market_fetcher = MarketFetcher(self.hl_client)
            self.account_fetcher = AccountFetcher(self.hl_client)

        except Exception as e:
            print(f"[BOT ERROR] Failed to initialize Hyperliquid: {e}", flush=True)
            raise

        print(f"[BOT] Has Hyperliquid key: {bool(config.hyperliquid_wallet_private_key)}", flush=True)
        print(f"[BOT] Has Anthropic key: {bool(config.anthropic_api_key)}", flush=True)

    def _execute_cycle(self):
        """Execute one trading cycle."""
        # Check for active user input (cycle type)
        user_guidance = self._check_user_input()

        print(f"[BOT] Fetching market data...", flush=True)
        try:
            assets = config.get_trading_assets()  # ['BTC', 'ETH', 'SOL']
            market_data = {}

            for asset in assets:
                try:
                    # Fetch ticker data
                    ticker = self.market_fetcher.fetch_ticker_data(asset)
                    print(f"[BOT]   {asset}: ${ticker['price']:.2f}", flush=True)

                    # Fetch candles (1h timeframe, last 100 candles)
                    candles = self.market_fetcher.fetch_candles(asset, interval="1h", limit=100)
                    print(f"[BOT]   {asset}: Fetched {len(candles)} candles", flush=True)

                    # Save to database
                    self.market_fetcher.save_to_database(asset, ticker, candles)

                    market_data[asset] = {
                        'ticker': ticker,
                        'candles': candles
                    }

                except Exception as e:
                    print(f"[BOT WARNING] Failed to fetch {asset} data: {e}", flush=True)
                    # Continue with other assets

            if not market_data:
                raise RuntimeError("Failed to fetch any market data")

        except Exception as e:
            print(f"[BOT ERROR] Market data fetch failed: {e}", flush=True)
            # Skip cycle or use cached data

        print(f"[BOT] Calculating indicators...", flush=True)
        # TODO: Calculate technical indicators

        print(f"[BOT] Getting account state...", flush=True)
        try:
            account_state = self.account_fetcher.fetch_account_state()
            positions = self.account_fetcher.fetch_positions()

            print(f"[BOT]   Account Value: ${account_state['account_value']:.2f}", flush=True)
            print(f"[BOT]   Unrealized PnL: ${account_state['unrealized_pnl']:.2f}", flush=True)
            print(f"[BOT]   Open Positions: {len(positions)}", flush=True)

            for pos in positions:
                print(f"[BOT]     {pos['asset']} {pos['side']}: {pos['size']} @ ${pos['current_price']:.2f} (PnL: ${pos['pnl']:.2f})", flush=True)

            # Save to database
            self.account_fetcher.save_to_database(account_state, positions)

        except Exception as e:
            print(f"[BOT ERROR] Account state fetch failed: {e}", flush=True)
            # Continue cycle (may use last known state)

        print(f"[BOT] Querying Claude for trading decision...", flush=True)
        if user_guidance:
            print(f"[BOT] Including user guidance: {user_guidance[:50]}...", flush=True)
        # TODO: Send data to Claude API

        print(f"[BOT] Executing trades...", flush=True)
        # TODO: Execute approved trades

        print(f"[BOT] Saving to database...", flush=True)
        # TODO: Save decision and results to SQLite

    def _check_user_input(self) -> Optional[str]:
        """Check for active user input (cycle type only)."""
        try:
            from database import get_active_user_input, archive_user_input

            active_input = get_active_user_input()

            if active_input and active_input.get('message_type') == 'cycle':
                message = active_input.get('message')
                input_id = active_input.get('id')

                print(f"[BOT] Found user input: {message[:50]}...", flush=True)

                # Archive it after use
                archive_user_input(input_id)

                return message

        except Exception as e:
            print(f"[BOT WARNING] Failed to check user input: {e}", flush=True)

        return None


# Global bot instance
bot = TradingBot()
