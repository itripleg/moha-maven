"""
Account state fetcher for Hyperliquid.

This module provides functionality to fetch account state (balance, positions, PnL)
from Hyperliquid and save it to the SQLite database.
"""

import time
from datetime import datetime
from typing import Dict, List
import json

from .hyperliquid_client import HyperliquidClient


class AccountFetcher:
    """
    Fetches account state from Hyperliquid and saves to database.

    Fetches account balance, equity, margin, unrealized PnL, and open positions
    from Hyperliquid and saves to SQLite via database helper functions.
    """

    def __init__(self, client: HyperliquidClient):
        """
        Initialize account state fetcher.

        Args:
            client: Initialized HyperliquidClient instance
        """
        self.client = client
        self.info = client.get_info()
        self.wallet_address = client.get_account_address()  # Use main account address, not API wallet

    def fetch_account_state(self, retry_count: int = 3) -> Dict:
        """
        Fetch complete account state.

        Args:
            retry_count: Number of retry attempts

        Returns:
            {
                'balance': 1000.0,
                'equity': 1050.25,
                'margin_used': 200.0,
                'available_margin': 850.25,
                'unrealized_pnl': 50.25,
                'realized_pnl': 0.0,
                'total_pnl': 50.25,
                'account_value': 1050.25,
                'timestamp': '2025-12-17T...'
            }

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(retry_count):
            try:
                # Fetch user state from Hyperliquid
                user_state = self.info.user_state(self.wallet_address)

                # Extract margin summary
                margin_summary = user_state.get('marginSummary', {})

                # Parse account values
                account_value = float(margin_summary.get('accountValue', 0))
                total_margin_used = float(margin_summary.get('totalMarginUsed', 0))
                total_ntl_pos = float(margin_summary.get('totalNtlPos', 0))  # Net position value
                total_raw_usd = float(margin_summary.get('totalRawUsd', 0))  # Unrealized PnL

                # Calculate derived fields
                # Equity = account value (which already includes unrealized PnL)
                equity = account_value
                # Balance = equity - unrealized PnL
                balance = equity - total_raw_usd
                # Available margin = equity - margin used
                available_margin = equity - total_margin_used

                return {
                    'balance': balance,
                    'equity': equity,
                    'margin_used': total_margin_used,
                    'available_margin': available_margin,
                    'unrealized_pnl': total_raw_usd,
                    'realized_pnl': 0.0,  # Not directly available in marginSummary
                    'total_pnl': total_raw_usd,  # Simplified (only unrealized)
                    'account_value': account_value,
                    'timestamp': datetime.now().isoformat()
                }

            except Exception as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Failed to fetch account state after {retry_count} attempts: {e}")
                else:
                    delay = 2 ** attempt
                    print(f"[RETRY] Fetch account state attempt {attempt + 1} failed: {e}. Retrying in {delay}s...", flush=True)
                    time.sleep(delay)

    def fetch_positions(self, retry_count: int = 3) -> List[Dict]:
        """
        Fetch open positions.

        Args:
            retry_count: Number of retry attempts

        Returns:
            [
                {
                    'asset': 'BTC',
                    'side': 'long',
                    'entry_price': 98000.0,
                    'current_price': 98500.0,
                    'size': 0.01,
                    'leverage': 5.0,
                    'pnl': 5.0,
                    'pnl_percent': 0.51,
                    'liquidation_price': 80000.0,
                    'margin_used': 196.0
                },
                ...
            ]

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(retry_count):
            try:
                # Fetch user state from Hyperliquid
                user_state = self.info.user_state(self.wallet_address)

                # Extract asset positions
                asset_positions = user_state.get('assetPositions', [])

                positions = []
                for asset_pos in asset_positions:
                    position_data = asset_pos.get('position', {})

                    # Extract position fields
                    coin = position_data.get('coin', '')
                    szi = float(position_data.get('szi', 0))  # Signed size
                    entry_px = float(position_data.get('entryPx', 0))
                    position_value = float(position_data.get('positionValue', 0))
                    unrealized_pnl = float(position_data.get('unrealizedPnl', 0))

                    # Get leverage info
                    leverage_info = position_data.get('leverage', {})
                    leverage = float(leverage_info.get('value', 1)) if isinstance(leverage_info, dict) else float(leverage_info)

                    # Determine side (long if positive, short if negative)
                    if szi == 0:
                        continue  # Skip if no position
                    side = 'long' if szi > 0 else 'short'
                    size = abs(szi)

                    # Calculate current price from position value
                    # position_value = size * current_price
                    current_price = position_value / size if size > 0 else entry_px

                    # Calculate PnL percentage
                    if entry_px > 0:
                        pnl_percent = (unrealized_pnl / (entry_px * size)) * 100
                    else:
                        pnl_percent = 0

                    # Liquidation price (may not be directly available)
                    liquidation_price = position_data.get('liquidationPx', 0)
                    if liquidation_price == 0:
                        # Estimate liquidation price if not provided
                        # This is a simplified calculation
                        if side == 'long':
                            liquidation_price = entry_px * (1 - 1/leverage) if leverage > 0 else 0
                        else:
                            liquidation_price = entry_px * (1 + 1/leverage) if leverage > 0 else 0

                    # Calculate margin used
                    margin_used = position_value / leverage if leverage > 0 else position_value

                    positions.append({
                        'asset': coin,
                        'side': side,
                        'entry_price': entry_px,
                        'current_price': current_price,
                        'size': size,
                        'leverage': leverage,
                        'pnl': unrealized_pnl,
                        'pnl_percent': pnl_percent,
                        'liquidation_price': liquidation_price,
                        'margin_used': margin_used
                    })

                return positions

            except Exception as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Failed to fetch positions after {retry_count} attempts: {e}")
                else:
                    delay = 2 ** attempt
                    print(f"[RETRY] Fetch positions attempt {attempt + 1} failed: {e}. Retrying in {delay}s...", flush=True)
                    time.sleep(delay)

    def save_to_database(self, account_state: Dict, positions: List[Dict]):
        """
        Save account state and positions to database.

        Args:
            account_state: Account state dict from fetch_account_state()
            positions: List of position dicts from fetch_positions()
        """
        # Save account state
        try:
            from database import save_account_state

            save_account_state(
                balance=account_state['balance'],
                equity=account_state['equity'],
                margin_used=account_state['margin_used'],
                available_margin=account_state['available_margin'],
                unrealized_pnl=account_state['unrealized_pnl'],
                realized_pnl=account_state.get('realized_pnl', 0),
                total_pnl=account_state['total_pnl'],
                account_value=account_state['account_value'],
                data=json.dumps(account_state)
            )
            print(f"[DB] Saved account state", flush=True)

        except Exception as e:
            print(f"[DB ERROR] Failed to save account state: {e}", flush=True)

        # Save or update positions
        for pos in positions:
            try:
                from database import get_open_positions, create_position, update_position

                # Check if position already exists
                existing_positions = get_open_positions()
                existing_pos = None
                for existing in existing_positions:
                    if existing.get('asset') == pos['asset'] and existing.get('side') == pos['side']:
                        existing_pos = existing
                        break

                if existing_pos:
                    # Update existing position
                    update_position(
                        position_id=existing_pos['id'],
                        current_price=pos['current_price'],
                        pnl=pos['pnl'],
                        pnl_percent=pos['pnl_percent']
                    )
                    print(f"[DB] Updated position {pos['asset']} {pos['side']}", flush=True)
                else:
                    # Create new position
                    create_position(
                        asset=pos['asset'],
                        side=pos['side'],
                        entry_price=pos['entry_price'],
                        current_price=pos['current_price'],
                        quantity_usd=pos['size'],  # Note: may need adjustment
                        leverage=pos['leverage'],
                        wallet_address=self.wallet_address,
                        initiated_by='bot'
                    )
                    print(f"[DB] Created position {pos['asset']} {pos['side']}", flush=True)

            except Exception as e:
                print(f"[DB WARNING] Failed to save position {pos['asset']}: {e}", flush=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"AccountFetcher(wallet={self.wallet_address})"
