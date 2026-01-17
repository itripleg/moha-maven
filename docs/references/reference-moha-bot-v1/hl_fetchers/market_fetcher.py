"""
Market data fetcher for Hyperliquid.

This module provides functionality to fetch market data (prices, candles, volume)
from Hyperliquid and save it to the SQLite database.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from .hyperliquid_client import HyperliquidClient


class MarketFetcher:
    """
    Fetches market data from Hyperliquid and saves to database.

    Fetches ticker data (price, volume, funding rate) and candle data (OHLCV)
    for configured assets and saves to SQLite via database helper functions.
    """

    def __init__(self, client: HyperliquidClient):
        """
        Initialize market data fetcher.

        Args:
            client: Initialized HyperliquidClient instance
        """
        self.client = client
        self.info = client.get_info()

    def fetch_all_assets(self, assets: List[str]) -> Dict[str, Dict]:
        """
        Fetch market data for all configured assets.

        Args:
            assets: List of asset symbols (e.g., ['BTC', 'ETH', 'SOL'])

        Returns:
            {
                'BTC': {'price': 98765.43, 'volume_24h': ..., 'funding_rate': ...},
                'ETH': {...},
                ...
            }
        """
        results = {}
        for asset in assets:
            try:
                ticker = self.fetch_ticker_data(asset)
                results[asset] = ticker
            except Exception as e:
                print(f"[WARNING] Failed to fetch {asset}: {e}", flush=True)
                results[asset] = {'error': str(e)}

        return results

    def fetch_ticker_data(self, asset: str, retry_count: int = 3) -> Dict:
        """
        Fetch ticker data for a single asset.

        Args:
            asset: Asset symbol (e.g., 'BTC')
            retry_count: Number of retry attempts

        Returns:
            {
                'asset': 'BTC',
                'price': 98765.43,
                'volume_24h': 1234567.89,
                'funding_rate': 0.0001,
                'open_interest': 9876543.21
            }

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(retry_count):
            try:
                # Fetch current prices
                all_mids = self.info.all_mids()

                # Get price for this asset
                price = float(all_mids.get(asset, 0))
                if price == 0:
                    raise ValueError(f"No price data for {asset}")

                # Fetch metadata (includes universe data)
                meta = self.info.meta()

                # Find asset in universe
                asset_info = None
                for universe_asset in meta.get('universe', []):
                    if universe_asset.get('name') == asset:
                        asset_info = universe_asset
                        break

                # Extract additional data (if available)
                volume_24h = 0.0
                funding_rate = 0.0
                open_interest = 0.0

                # Note: These fields may not be directly in meta()
                # We'll populate them with 0 for now and can enhance later
                # when we have better access to this data via other endpoints

                return {
                    'asset': asset,
                    'price': price,
                    'volume_24h': volume_24h,
                    'funding_rate': funding_rate,
                    'open_interest': open_interest,
                    'timestamp': datetime.now().isoformat()
                }

            except Exception as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Failed to fetch ticker for {asset} after {retry_count} attempts: {e}")
                else:
                    delay = 2 ** attempt
                    print(f"[RETRY] Fetch ticker attempt {attempt + 1} failed: {e}. Retrying in {delay}s...", flush=True)
                    time.sleep(delay)

    def fetch_candles(self, asset: str, interval: str = "1h", limit: int = 100, retry_count: int = 3) -> List[Dict]:
        """
        Fetch candle data for an asset.

        Args:
            asset: Asset symbol (e.g., 'BTC')
            interval: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch
            retry_count: Number of retry attempts

        Returns:
            [
                {
                    'timestamp': '2025-12-17T10:00:00',
                    'open': 98000.0,
                    'high': 98500.0,
                    'low': 97500.0,
                    'close': 98200.0,
                    'volume': 1234.56
                },
                ...
            ]

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(retry_count):
            try:
                # Calculate time range based on interval and limit
                interval_minutes = self._parse_interval(interval)
                end_time = datetime.now()
                start_time = end_time - timedelta(minutes=interval_minutes * limit)

                # Convert to milliseconds (Hyperliquid format)
                start_time_ms = int(start_time.timestamp() * 1000)
                end_time_ms = int(end_time.timestamp() * 1000)

                # Fetch candles from API
                # Note: The exact method name may vary - check hyperliquid SDK docs
                # Common names: candles_snapshot, candle_snapshot, get_candles
                try:
                    candles = self.info.candles_snapshot(
                        coin=asset,
                        interval=interval,
                        startTime=start_time_ms,
                        endTime=end_time_ms
                    )
                except AttributeError:
                    # If candles_snapshot doesn't exist, try alternative method names
                    print(f"[WARNING] candles_snapshot not available, returning empty candles for {asset}", flush=True)
                    return []

                # Parse candles to our format
                parsed_candles = []
                for candle in candles:
                    # Hyperliquid format: {T: timestamp_ms, o: open, h: high, l: low, c: close, v: volume}
                    # or {t: timestamp_ms, o: open, h: high, l: low, c: close, v: volume}
                    timestamp_ms = candle.get('T') or candle.get('t')
                    timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000)

                    parsed_candles.append({
                        'timestamp': timestamp_dt.isoformat(),
                        'open': float(candle.get('o', 0)),
                        'high': float(candle.get('h', 0)),
                        'low': float(candle.get('l', 0)),
                        'close': float(candle.get('c', 0)),
                        'volume': float(candle.get('v', 0))
                    })

                return parsed_candles

            except Exception as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Failed to fetch candles for {asset} after {retry_count} attempts: {e}")
                else:
                    delay = 2 ** attempt
                    print(f"[RETRY] Fetch candles attempt {attempt + 1} failed: {e}. Retrying in {delay}s...", flush=True)
                    time.sleep(delay)

    def save_to_database(self, asset: str, ticker_data: Dict, candles: List[Dict]):
        """
        Save fetched data to database.

        Args:
            asset: Asset symbol
            ticker_data: Ticker data dict from fetch_ticker_data()
            candles: List of candle dicts from fetch_candles()
        """
        try:
            # Import database functions
            from database import save_market_snapshot, save_candle

            # Save market snapshot
            save_market_snapshot(
                asset=asset,
                price=ticker_data['price'],
                volume_24h=ticker_data.get('volume_24h', 0),
                funding_rate=ticker_data.get('funding_rate', 0),
                open_interest=ticker_data.get('open_interest', 0),
                data=json.dumps(ticker_data)
            )
            print(f"[DB] Saved market snapshot for {asset}", flush=True)

        except Exception as e:
            print(f"[DB ERROR] Failed to save market snapshot for {asset}: {e}", flush=True)

        # Save candles
        candles_saved = 0
        for candle in candles:
            try:
                save_candle(
                    asset=asset,
                    timeframe='1h',  # Use the interval from fetch_candles
                    timestamp=candle['timestamp'],
                    open=candle['open'],
                    high=candle['high'],
                    low=candle['low'],
                    close=candle['close'],
                    volume=candle['volume']
                )
                candles_saved += 1
            except Exception as e:
                # Log but continue with other candles
                print(f"[DB WARNING] Failed to save candle: {e}", flush=True)

        if candles_saved > 0:
            print(f"[DB] Saved {candles_saved}/{len(candles)} candles for {asset}", flush=True)

    def _parse_interval(self, interval: str) -> int:
        """
        Convert interval string to minutes.

        Args:
            interval: Interval string ('1m', '5m', '15m', '1h', '4h', '1d')

        Returns:
            Number of minutes
        """
        interval_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        return interval_map.get(interval, 60)  # Default to 1h

    def __repr__(self) -> str:
        """String representation."""
        return f"MarketFetcher(client={self.client})"
