"""
Hyperliquid Client wrapper for the MotherHaven API service.

Provides a unified interface for interacting with Hyperliquid's Info and Exchange APIs.
Implements lazy initialization for API clients to avoid unnecessary connections,
and uses skip_ws=True to avoid WebSocket connections per SDK best practices.
"""
import os
from typing import Optional, Dict, Any, List

try:
    import eth_account
    from eth_account.signers.local import LocalAccount
    from hyperliquid.info import Info
    from hyperliquid.exchange import Exchange
    HYPERLIQUID_AVAILABLE = True
except ImportError:
    HYPERLIQUID_AVAILABLE = False
    LocalAccount = None
    Info = None
    Exchange = None


# =============================================================================
# Configuration Constants
# =============================================================================

# Hyperliquid API URLs
TESTNET_API_URL = "https://api.hyperliquid-testnet.xyz"
MAINNET_API_URL = "https://api.hyperliquid.xyz"


# =============================================================================
# Error Categories and Patterns
# =============================================================================

class TradeErrorCategory:
    """Error categories for trade execution failures."""
    ORACLE = 'oracle'           # Price too far from oracle
    LIQUIDITY = 'liquidity'     # Insufficient liquidity
    MARGIN = 'margin'           # Insufficient margin
    SIZE = 'size'               # Invalid size (too small/large)
    RATE_LIMIT = 'rate_limit'   # Rate limiting
    NETWORK = 'network'         # Network/connectivity issues
    VALIDATION = 'validation'   # Input validation errors
    UNKNOWN = 'unknown'         # Uncategorized errors


# Error patterns for categorization
ORACLE_ERROR_PATTERNS = [
    'price too far from oracle',
    'oracle price',
    'stale oracle',
    'oracle deviation',
]

LIQUIDITY_ERROR_PATTERNS = [
    'insufficient liquidity',
    'no liquidity',
    'slippage',
    'not enough liquidity',
]

MARGIN_ERROR_PATTERNS = [
    'insufficient margin',
    'not enough margin',
    'margin requirement',
    'insufficient balance',
    'insufficient funds',
]

SIZE_ERROR_PATTERNS = [
    'size too small',
    'size too large',
    'minimum size',
    'maximum size',
    'invalid size',
    'below minimum',
]

RATE_LIMIT_ERROR_PATTERNS = [
    'rate limit',
    'too many requests',
    'throttled',
]


def categorize_trade_error(error_message: str) -> tuple[str, bool]:
    """
    Categorize a trade execution error based on the error message.

    Args:
        error_message: The error message from the exchange

    Returns:
        tuple: (error_category, is_retryable)
            - error_category: One of TradeErrorCategory values
            - is_retryable: Whether the error might be transient and retryable
    """
    if not error_message:
        return TradeErrorCategory.UNKNOWN, False

    error_lower = error_message.lower()

    # Check each category
    for pattern in ORACLE_ERROR_PATTERNS:
        if pattern in error_lower:
            return TradeErrorCategory.ORACLE, True  # Oracle errors are often transient

    for pattern in LIQUIDITY_ERROR_PATTERNS:
        if pattern in error_lower:
            return TradeErrorCategory.LIQUIDITY, True

    for pattern in MARGIN_ERROR_PATTERNS:
        if pattern in error_lower:
            return TradeErrorCategory.MARGIN, False  # Margin issues need user action

    for pattern in SIZE_ERROR_PATTERNS:
        if pattern in error_lower:
            return TradeErrorCategory.SIZE, False  # Size errors need input change

    for pattern in RATE_LIMIT_ERROR_PATTERNS:
        if pattern in error_lower:
            return TradeErrorCategory.RATE_LIMIT, True  # Rate limits are transient

    # Network-related keywords
    if any(kw in error_lower for kw in ['connection', 'timeout', 'network', 'unreachable']):
        return TradeErrorCategory.NETWORK, True

    return TradeErrorCategory.UNKNOWN, False


# =============================================================================
# Hyperliquid Client Wrapper
# =============================================================================

class HyperliquidClient:
    """
    Wrapper for Hyperliquid Info and Exchange APIs.

    Provides lazy initialization of API clients, testnet/mainnet switching,
    and proper handling of API wallet vs. main account addresses.

    Key Features:
        - Lazy initialization: API clients are created only when first accessed
        - skip_ws=True: Avoids WebSocket connections for Info client
        - Private key normalization: Handles keys with or without 0x prefix
        - Separate account address: Supports API wallets that trade on behalf
          of a main account

    Usage:
        # Basic initialization (uses wallet address as account)
        client = HyperliquidClient(private_key="your_private_key")

        # With separate account address (for API wallets)
        client = HyperliquidClient(
            private_key="api_wallet_key",
            account_address="main_account_address"
        )

        # Production (mainnet)
        client = HyperliquidClient(private_key="key", use_testnet=False)
    """

    def __init__(
        self,
        private_key: str,
        account_address: Optional[str] = None,
        use_testnet: bool = True
    ):
        """
        Initialize Hyperliquid client wrapper.

        Args:
            private_key: Ethereum private key for signing transactions.
                         Can be with or without '0x' prefix.
            account_address: Optional address of the main trading account.
                            If not provided, uses the wallet's address.
                            Use this when operating with an API wallet that
                            trades on behalf of a main account.
            use_testnet: Whether to connect to testnet (True) or mainnet (False).
                        Defaults to True for safety.

        Raises:
            ImportError: If hyperliquid-python-sdk is not installed
            ValueError: If private_key is invalid
        """
        if not HYPERLIQUID_AVAILABLE:
            raise ImportError(
                "Hyperliquid SDK not available. Install with: "
                "pip install hyperliquid-python-sdk eth-account"
            )

        # Normalize private key (ensure 0x prefix)
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key

        self._private_key = private_key
        self.use_testnet = use_testnet

        # Create account from private key
        try:
            self.account: LocalAccount = eth_account.Account.from_key(private_key)
        except Exception as e:
            raise ValueError(f"Invalid private key: {e}")

        # Use provided account address or default to wallet address
        self.address = account_address or self.account.address

        # Determine base URL based on network
        if use_testnet:
            self.base_url = TESTNET_API_URL
        else:
            self.base_url = MAINNET_API_URL

        # Lazy-initialized clients (use skip_ws=True to avoid WebSocket connections)
        self._info: Optional[Info] = None
        self._exchange: Optional[Exchange] = None

    @property
    def info(self) -> Info:
        """
        Get Info client for read-only API calls (lazy initialized).

        The Info client is used for fetching market data, user state,
        and other read-only operations. Uses skip_ws=True to avoid
        WebSocket connections per SDK best practices.

        Returns:
            Info: Hyperliquid Info client instance
        """
        if self._info is None:
            self._info = Info(self.base_url, skip_ws=True)
        return self._info

    @property
    def exchange(self) -> Exchange:
        """
        Get Exchange client for trading operations (lazy initialized).

        The Exchange client is used for placing orders, canceling orders,
        updating leverage, and other write operations that require signing.

        Note: Uses vault_address parameter when account_address differs from
        wallet address (API wallet scenario).

        Returns:
            Exchange: Hyperliquid Exchange client instance
        """
        if self._exchange is None:
            # If account address differs from wallet, use vault_address
            vault_address = None
            if self.address.lower() != self.account.address.lower():
                vault_address = self.address

            self._exchange = Exchange(
                self.account,
                self.base_url,
                vault_address=vault_address
            )
        return self._exchange

    @property
    def wallet_address(self) -> str:
        """
        Get the wallet (signing) address.

        Returns:
            str: Ethereum address of the signing wallet
        """
        return self.account.address

    @property
    def trading_address(self) -> str:
        """
        Get the trading account address.

        This is the address that positions and balances are associated with.
        For API wallets, this differs from the wallet_address.

        Returns:
            str: Ethereum address of the trading account
        """
        return self.address

    @property
    def is_testnet(self) -> bool:
        """
        Check if client is connected to testnet.

        Returns:
            bool: True if connected to testnet, False if mainnet
        """
        return self.use_testnet

    @property
    def network_name(self) -> str:
        """
        Get human-readable network name.

        Returns:
            str: 'testnet' or 'mainnet'
        """
        return 'testnet' if self.use_testnet else 'mainnet'

    def is_connected(self) -> bool:
        """
        Check if client can connect to Hyperliquid API.

        Attempts a simple API call to verify connectivity.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # Use a lightweight API call to test connectivity
            self.info.all_mids()
            return True
        except Exception:
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.

        Returns:
            dict: Connection information including network, addresses,
                  and connectivity status
        """
        return {
            'network': self.network_name,
            'base_url': self.base_url,
            'wallet_address': self.wallet_address,
            'trading_address': self.trading_address,
            'is_api_wallet': self.wallet_address.lower() != self.trading_address.lower(),
            'connected': self.is_connected()
        }

    def __repr__(self) -> str:
        """String representation of the client."""
        return (
            f"HyperliquidClient("
            f"network={self.network_name}, "
            f"wallet={self.wallet_address[:10]}..., "
            f"trading={self.trading_address[:10]}...)"
        )

    # =========================================================================
    # Market Data Methods
    # =========================================================================

    def get_market_info(self, coin: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market metadata and asset context information.

        Fetches perpetual market metadata including size decimals, mark price,
        funding rate, open interest, and daily volume.

        Args:
            coin: Optional specific coin to filter (e.g., 'BTC', 'ETH').
                  If None, returns info for all perpetual markets.

        Returns:
            dict: Market information with structure:
                - 'markets': List of market info dicts (or single market if coin specified)
                - 'success': Boolean indicating success
                - 'error': Error message if failed

                Each market dict contains:
                - 'name': Asset name (e.g., 'BTC')
                - 'sz_decimals': Size decimals for the asset
                - 'mark_px': Current mark price
                - 'funding': Current funding rate
                - 'open_interest': Open interest in USD
                - 'day_volume': 24h notional volume

        Example:
            # Get all markets
            info = client.get_market_info()

            # Get specific market
            btc_info = client.get_market_info('BTC')
        """
        try:
            # Get metadata with asset contexts (prices, funding, volumes)
            meta_and_ctx = self.info.meta_and_asset_ctxs()
            universe, contexts = meta_and_ctx

            markets = []
            for idx, ctx in enumerate(contexts):
                asset = universe["universe"][idx]
                market_data = {
                    'name': asset['name'],
                    'sz_decimals': asset.get('szDecimals', 0),
                    'mark_px': float(ctx.get('markPx', 0)),
                    'funding': float(ctx.get('funding', 0)),
                    'open_interest': float(ctx.get('openInterest', 0)),
                    'day_volume': float(ctx.get('dayNtlVlm', 0)),
                }
                markets.append(market_data)

            # Filter by coin if specified
            if coin:
                coin_upper = coin.upper()
                filtered = [m for m in markets if m['name'].upper() == coin_upper]
                if not filtered:
                    return {
                        'success': False,
                        'error': f"Market '{coin}' not found",
                        'markets': []
                    }
                return {
                    'success': True,
                    'markets': filtered[0]  # Return single market dict
                }

            return {
                'success': True,
                'markets': markets
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'markets': []
            }

    def get_prices(self, coins: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get current mid prices for assets.

        Retrieves real-time mid prices (average of best bid and ask) for
        all perpetual assets or a specific subset.

        Args:
            coins: Optional list of coin symbols to filter (e.g., ['BTC', 'ETH']).
                   If None, returns prices for all available assets.

        Returns:
            dict: Price information with structure:
                - 'prices': Dict mapping coin symbol to mid price
                - 'success': Boolean indicating success
                - 'error': Error message if failed

        Example:
            # Get all prices
            all_prices = client.get_prices()
            print(all_prices['prices']['BTC'])

            # Get specific prices
            prices = client.get_prices(['BTC', 'ETH'])
        """
        try:
            all_mids = self.info.all_mids()

            # Convert to float for consistency
            prices = {k: float(v) for k, v in all_mids.items()}

            # Filter by coins if specified
            if coins:
                coins_upper = [c.upper() for c in coins]
                filtered = {}
                not_found = []

                for coin in coins_upper:
                    if coin in prices:
                        filtered[coin] = prices[coin]
                    else:
                        not_found.append(coin)

                if not_found:
                    return {
                        'success': True,
                        'prices': filtered,
                        'warning': f"Coins not found: {', '.join(not_found)}"
                    }

                return {
                    'success': True,
                    'prices': filtered
                }

            return {
                'success': True,
                'prices': prices
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prices': {}
            }

    def get_orderbook(
        self,
        coin: str,
        depth: int = 5
    ) -> Dict[str, Any]:
        """
        Get L2 order book snapshot for a specific market.

        Retrieves the current order book with bid and ask levels, including
        price and size at each level.

        Args:
            coin: Asset symbol (e.g., 'BTC', 'ETH'). Required.
            depth: Number of price levels to return on each side.
                   Defaults to 5. Max available depends on exchange.

        Returns:
            dict: Order book data with structure:
                - 'coin': Asset symbol
                - 'bids': List of bid levels [{'px': price, 'sz': size}, ...]
                - 'asks': List of ask levels [{'px': price, 'sz': size}, ...]
                - 'best_bid': Best (highest) bid price
                - 'best_ask': Best (lowest) ask price
                - 'spread': Spread between best ask and best bid
                - 'spread_pct': Spread as percentage of mid price
                - 'success': Boolean indicating success
                - 'error': Error message if failed

        Example:
            orderbook = client.get_orderbook('ETH', depth=10)
            print(f"Best bid: {orderbook['best_bid']}")
            print(f"Best ask: {orderbook['best_ask']}")
            print(f"Spread: {orderbook['spread_pct']:.4f}%")
        """
        if not coin:
            return {
                'success': False,
                'error': "coin parameter is required",
                'coin': None,
                'bids': [],
                'asks': []
            }

        try:
            coin_upper = coin.upper()
            l2_snapshot = self.info.l2_snapshot(coin_upper)

            # Extract levels from snapshot
            levels = l2_snapshot.get('levels', [[], []])
            bids_raw = levels[0] if len(levels) > 0 else []
            asks_raw = levels[1] if len(levels) > 1 else []

            # Process and limit depth
            bids = [
                {'px': float(b['px']), 'sz': float(b['sz'])}
                for b in bids_raw[:depth]
            ]
            asks = [
                {'px': float(a['px']), 'sz': float(a['sz'])}
                for a in asks_raw[:depth]
            ]

            # Calculate spread metrics
            best_bid = bids[0]['px'] if bids else 0.0
            best_ask = asks[0]['px'] if asks else 0.0
            spread = best_ask - best_bid if (best_bid and best_ask) else 0.0

            # Calculate spread percentage (relative to mid price)
            mid_price = (best_bid + best_ask) / 2 if (best_bid and best_ask) else 0.0
            spread_pct = (spread / mid_price * 100) if mid_price > 0 else 0.0

            return {
                'success': True,
                'coin': l2_snapshot.get('coin', coin_upper),
                'bids': bids,
                'asks': asks,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid_price': mid_price,
                'spread': spread,
                'spread_pct': spread_pct
            }

        except Exception as e:
            error_msg = str(e)
            # Check for common error patterns
            if 'not found' in error_msg.lower() or 'unknown' in error_msg.lower():
                error_msg = f"Market '{coin}' not found"

            return {
                'success': False,
                'error': error_msg,
                'coin': coin.upper(),
                'bids': [],
                'asks': []
            }

    # =========================================================================
    # Account State Methods
    # =========================================================================

    def get_account_state(self) -> Dict[str, Any]:
        """
        Get comprehensive account state including positions, margin, and account value.

        Fetches the full user state for the trading address, including all
        open positions, margin summary, and withdrawable balance.

        Returns:
            dict: Account state with structure:
                - 'account_value': Total account value in USD
                - 'total_margin_used': Total margin used across positions
                - 'total_position_value': Sum of all position notional values
                - 'withdrawable': Available balance for withdrawal
                - 'positions': List of position summaries
                - 'margin_summary': Full margin details
                - 'cross_margin_summary': Cross margin details (if available)
                - 'success': Boolean indicating success
                - 'error': Error message if failed

        Example:
            state = client.get_account_state()
            if state['success']:
                print(f"Account Value: ${state['account_value']:,.2f}")
                print(f"Withdrawable: ${state['withdrawable']:,.2f}")
                print(f"Open Positions: {len(state['positions'])}")
        """
        try:
            user_state = self.info.user_state(self.address)

            # Extract margin summary
            margin_summary = user_state.get('marginSummary', {})
            account_value = float(margin_summary.get('accountValue', 0))
            total_margin_used = float(margin_summary.get('totalMarginUsed', 0))
            total_position_value = float(margin_summary.get('totalNtlPos', 0))

            # Extract withdrawable balance
            withdrawable = float(user_state.get('withdrawable', 0))

            # Extract and summarize positions
            asset_positions = user_state.get('assetPositions', [])
            positions = []
            for asset_pos in asset_positions:
                pos = asset_pos.get('position', {})
                # Only include positions with non-zero size
                size = float(pos.get('szi', 0))
                if size != 0:
                    positions.append({
                        'coin': pos.get('coin', 'UNKNOWN'),
                        'size': size,
                        'entry_px': float(pos.get('entryPx', 0)),
                        'position_value': float(pos.get('positionValue', 0)),
                        'unrealized_pnl': float(pos.get('unrealizedPnl', 0)),
                        'leverage': pos.get('leverage', {}),
                        'liquidation_px': pos.get('liquidationPx'),
                        'margin_used': float(pos.get('marginUsed', 0)),
                        'max_leverage': pos.get('maxLeverage'),
                    })

            # Extract cross margin summary if available
            cross_margin = user_state.get('crossMarginSummary', {})

            return {
                'success': True,
                'account_value': account_value,
                'total_margin_used': total_margin_used,
                'total_position_value': total_position_value,
                'withdrawable': withdrawable,
                'positions': positions,
                'margin_summary': margin_summary,
                'cross_margin_summary': cross_margin,
                'raw_state': user_state  # Include raw for debugging/advanced use
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'account_value': 0.0,
                'total_margin_used': 0.0,
                'total_position_value': 0.0,
                'withdrawable': 0.0,
                'positions': [],
                'margin_summary': {},
                'cross_margin_summary': {}
            }

    def get_positions(self, coin: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current open positions.

        Retrieves detailed information about all open perpetual positions,
        optionally filtered by a specific coin.

        Args:
            coin: Optional coin symbol to filter (e.g., 'BTC', 'ETH').
                  If None, returns all open positions.

        Returns:
            dict: Position data with structure:
                - 'positions': List of position dicts, each containing:
                    - 'coin': Asset symbol
                    - 'size': Position size (negative for short)
                    - 'side': 'long' or 'short'
                    - 'entry_px': Average entry price
                    - 'mark_px': Current mark price
                    - 'unrealized_pnl': Unrealized profit/loss
                    - 'realized_pnl': Realized profit/loss
                    - 'leverage': Current leverage settings
                    - 'liquidation_px': Liquidation price
                    - 'margin_used': Margin used for position
                    - 'return_on_equity': ROE percentage
                - 'total_unrealized_pnl': Sum of all unrealized PnL
                - 'position_count': Number of open positions
                - 'success': Boolean indicating success
                - 'error': Error message if failed

        Example:
            # Get all positions
            positions = client.get_positions()
            for pos in positions['positions']:
                print(f"{pos['coin']}: {pos['side']} {abs(pos['size'])} @ {pos['entry_px']}")

            # Get specific position
            eth_pos = client.get_positions('ETH')
        """
        try:
            user_state = self.info.user_state(self.address)
            asset_positions = user_state.get('assetPositions', [])

            positions = []
            total_unrealized_pnl = 0.0

            for asset_pos in asset_positions:
                pos = asset_pos.get('position', {})
                size = float(pos.get('szi', 0))

                # Skip positions with zero size
                if size == 0:
                    continue

                # Determine side based on size sign
                side = 'long' if size > 0 else 'short'

                # Calculate return on equity if margin used
                margin_used = float(pos.get('marginUsed', 0))
                unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                roe = (unrealized_pnl / margin_used * 100) if margin_used > 0 else 0.0

                position_data = {
                    'coin': pos.get('coin', 'UNKNOWN'),
                    'size': size,
                    'side': side,
                    'entry_px': float(pos.get('entryPx', 0)),
                    'mark_px': float(pos.get('markPx', 0)) if pos.get('markPx') else None,
                    'unrealized_pnl': unrealized_pnl,
                    'realized_pnl': float(pos.get('cumFunding', {}).get('sinceOpen', 0)),
                    'leverage': pos.get('leverage', {}),
                    'liquidation_px': pos.get('liquidationPx'),
                    'margin_used': margin_used,
                    'return_on_equity': roe,
                    'max_leverage': pos.get('maxLeverage'),
                    'position_value': float(pos.get('positionValue', 0)),
                }
                positions.append(position_data)
                total_unrealized_pnl += unrealized_pnl

            # Filter by coin if specified
            if coin:
                coin_upper = coin.upper()
                positions = [p for p in positions if p['coin'].upper() == coin_upper]

            return {
                'success': True,
                'positions': positions,
                'total_unrealized_pnl': total_unrealized_pnl,
                'position_count': len(positions)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'positions': [],
                'total_unrealized_pnl': 0.0,
                'position_count': 0
            }

    def get_open_orders(
        self,
        coin: Optional[str] = None,
        include_frontend_details: bool = False
    ) -> Dict[str, Any]:
        """
        Get current open orders.

        Retrieves all open orders for the trading account, optionally
        filtered by coin. Can include additional frontend details like
        TP/SL and trigger information.

        Args:
            coin: Optional coin symbol to filter (e.g., 'BTC', 'ETH').
                  If None, returns all open orders.
            include_frontend_details: If True, fetch additional details
                                     including trigger conditions and TP/SL.

        Returns:
            dict: Order data with structure:
                - 'orders': List of order dicts, each containing:
                    - 'oid': Order ID
                    - 'coin': Asset symbol
                    - 'side': 'buy' or 'sell'
                    - 'size': Order size
                    - 'size_filled': Filled size (if available)
                    - 'limit_px': Limit price
                    - 'order_type': Order type (limit, stop, etc.)
                    - 'reduce_only': Whether reduce-only
                    - 'timestamp': Order timestamp
                    - 'cloid': Client order ID (if set)
                    # If include_frontend_details=True:
                    - 'is_trigger': Whether it's a trigger order
                    - 'trigger_px': Trigger price (for stop orders)
                    - 'trigger_condition': 'above' or 'below'
                    - 'tpsl': Take profit / stop loss info
                - 'order_count': Number of open orders
                - 'success': Boolean indicating success
                - 'error': Error message if failed

        Example:
            # Get all open orders
            orders = client.get_open_orders()
            for order in orders['orders']:
                print(f"{order['coin']}: {order['side']} {order['size']} @ {order['limit_px']}")

            # Get orders with trigger details
            orders = client.get_open_orders(include_frontend_details=True)
        """
        try:
            if include_frontend_details:
                raw_orders = self.info.frontend_open_orders(self.address)
            else:
                raw_orders = self.info.open_orders(self.address)

            orders = []
            for order in raw_orders:
                # Basic order info (common to both endpoints)
                order_data = {
                    'oid': order.get('oid'),
                    'coin': order.get('coin', 'UNKNOWN'),
                    'side': order.get('side', 'unknown').lower(),
                    'size': float(order.get('sz', 0)),
                    'limit_px': float(order.get('limitPx', 0)),
                    'timestamp': order.get('timestamp'),
                    'cloid': order.get('cloid'),
                }

                # Add fields that may differ between basic and frontend endpoints
                if include_frontend_details:
                    order_data.update({
                        'order_type': order.get('orderType', 'limit'),
                        'reduce_only': order.get('reduceOnly', False),
                        'is_trigger': order.get('isTrigger', False),
                        'trigger_px': float(order.get('triggerPx', 0)) if order.get('triggerPx') else None,
                        'trigger_condition': order.get('triggerCondition'),
                        'tpsl': order.get('tpsl'),
                        'children': order.get('children', []),
                    })
                else:
                    order_data.update({
                        'order_type': order.get('orderType', 'limit'),
                        'reduce_only': order.get('reduceOnly', False),
                        'orig_sz': float(order.get('origSz', 0)) if order.get('origSz') else None,
                    })

                orders.append(order_data)

            # Filter by coin if specified
            if coin:
                coin_upper = coin.upper()
                orders = [o for o in orders if o['coin'].upper() == coin_upper]

            return {
                'success': True,
                'orders': orders,
                'order_count': len(orders)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'orders': [],
                'order_count': 0
            }

    # =========================================================================
    # Trade Execution Methods
    # =========================================================================

    def market_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        slippage: float = 0.01,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a market order for a perpetual asset.

        Places an immediate market order that fills at the current market price
        with a specified slippage tolerance. Uses the exchange.market_open()
        method from the Hyperliquid SDK.

        Args:
            coin: Asset symbol (e.g., 'BTC', 'ETH'). Required.
            is_buy: True for a buy/long order, False for a sell/short order.
            size: Order size in base asset units (e.g., 0.1 ETH).
            slippage: Maximum acceptable slippage as a decimal (default 0.01 = 1%).
                      The order will fail if slippage exceeds this threshold.
            reduce_only: If True, the order can only reduce an existing position,
                        not open a new one. Useful for closing positions partially.

        Returns:
            dict: Order result with structure:
                - 'success': Boolean indicating if order was placed
                - 'order_id': Order ID if filled (oid)
                - 'filled_size': Total size filled
                - 'avg_price': Average fill price
                - 'statuses': List of status responses from exchange
                - 'error': Error message if failed
                - 'raw_response': Full response from exchange

        Example:
            # Market buy 0.1 ETH with 1% slippage
            result = client.market_order('ETH', is_buy=True, size=0.1)
            if result['success']:
                print(f"Filled {result['filled_size']} @ {result['avg_price']}")

            # Market sell (short) 0.05 BTC
            result = client.market_order('BTC', is_buy=False, size=0.05)

            # Reduce-only order to partially close
            result = client.market_order('ETH', is_buy=False, size=0.05, reduce_only=True)

        Raises:
            Does not raise - errors are returned in the response dict.
        """
        if not coin:
            return {
                'success': False,
                'error': "coin parameter is required",
                'order_id': None,
                'filled_size': 0.0,
                'avg_price': 0.0,
                'statuses': []
            }

        if size <= 0:
            return {
                'success': False,
                'error': "size must be greater than 0",
                'order_id': None,
                'filled_size': 0.0,
                'avg_price': 0.0,
                'statuses': []
            }

        if slippage < 0 or slippage > 1:
            return {
                'success': False,
                'error': "slippage must be between 0 and 1 (0% to 100%)",
                'order_id': None,
                'filled_size': 0.0,
                'avg_price': 0.0,
                'statuses': []
            }

        try:
            coin_upper = coin.upper()

            # Use exchange.market_open for market orders
            # px=None uses current market price, slippage controls tolerance
            order_result = self.exchange.market_open(
                coin_upper,
                is_buy,
                size,
                None,  # px - None for market price
                slippage
            )

            # Parse the response
            if order_result.get("status") == "ok":
                response_data = order_result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])

                # Collect fill information
                total_filled = 0.0
                avg_price = 0.0
                order_id = None
                errors = []

                for status in statuses:
                    if "filled" in status:
                        filled = status["filled"]
                        order_id = filled.get("oid")
                        total_filled = float(filled.get("totalSz", 0))
                        avg_price = float(filled.get("avgPx", 0))
                    elif "resting" in status:
                        # Order is resting (partially filled or limit-like)
                        resting = status["resting"]
                        order_id = resting.get("oid")
                    elif "error" in status:
                        errors.append(status["error"])

                if errors:
                    error_msg = "; ".join(errors)
                    error_category, is_retryable = categorize_trade_error(error_msg)
                    return {
                        'success': False,
                        'error': error_msg,
                        'error_category': error_category,
                        'is_retryable': is_retryable,
                        'order_id': order_id,
                        'filled_size': total_filled,
                        'avg_price': avg_price,
                        'statuses': statuses,
                        'raw_response': order_result
                    }

                return {
                    'success': True,
                    'order_id': order_id,
                    'coin': coin_upper,
                    'side': 'buy' if is_buy else 'sell',
                    'filled_size': total_filled,
                    'avg_price': avg_price,
                    'statuses': statuses,
                    'raw_response': order_result
                }
            else:
                # Status is not "ok"
                error_msg = order_result.get("response", {}).get("error", "Unknown error")
                if not error_msg:
                    error_msg = order_result.get("error", "Order failed")

                error_category, is_retryable = categorize_trade_error(str(error_msg))
                return {
                    'success': False,
                    'error': str(error_msg),
                    'error_category': error_category,
                    'is_retryable': is_retryable,
                    'order_id': None,
                    'filled_size': 0.0,
                    'avg_price': 0.0,
                    'statuses': [],
                    'raw_response': order_result
                }

        except Exception as e:
            error_msg = str(e)
            error_category, is_retryable = categorize_trade_error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_category': error_category,
                'is_retryable': is_retryable,
                'order_id': None,
                'filled_size': 0.0,
                'avg_price': 0.0,
                'statuses': []
            }

    def cancel_order(
        self,
        coin: str,
        order_id: int
    ) -> Dict[str, Any]:
        """
        Cancel an open order by its order ID.

        Cancels a resting (unfilled or partially filled) order on the exchange.
        Uses the exchange.cancel() method from the Hyperliquid SDK.

        Args:
            coin: Asset symbol the order was placed on (e.g., 'BTC', 'ETH').
            order_id: The order ID (oid) returned when the order was placed.

        Returns:
            dict: Cancellation result with structure:
                - 'success': Boolean indicating if cancellation was successful
                - 'order_id': The order ID that was cancelled
                - 'coin': Asset symbol
                - 'message': Success or error message
                - 'raw_response': Full response from exchange

        Example:
            # Cancel an order
            result = client.cancel_order('ETH', oid=12345)
            if result['success']:
                print(f"Order {result['order_id']} cancelled")

        Notes:
            - Only resting (unfilled) orders can be cancelled
            - Fully filled orders cannot be cancelled
            - Use get_open_orders() to find order IDs to cancel
        """
        if not coin:
            return {
                'success': False,
                'error': "coin parameter is required",
                'order_id': None,
                'coin': None,
                'message': None
            }

        if order_id is None:
            return {
                'success': False,
                'error': "order_id parameter is required",
                'order_id': None,
                'coin': coin,
                'message': None
            }

        try:
            coin_upper = coin.upper()

            # Call exchange.cancel(coin, oid)
            cancel_result = self.exchange.cancel(coin_upper, order_id)

            # Parse the response
            if cancel_result.get("status") == "ok":
                response_data = cancel_result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])

                # Check for errors in statuses
                for status in statuses:
                    if "error" in status:
                        return {
                            'success': False,
                            'error': status["error"],
                            'order_id': order_id,
                            'coin': coin_upper,
                            'message': status["error"],
                            'raw_response': cancel_result
                        }

                return {
                    'success': True,
                    'order_id': order_id,
                    'coin': coin_upper,
                    'message': f"Order {order_id} cancelled successfully",
                    'statuses': statuses,
                    'raw_response': cancel_result
                }
            else:
                error_msg = cancel_result.get("response", {}).get("error", "Unknown error")
                if not error_msg:
                    error_msg = cancel_result.get("error", "Cancel failed")

                return {
                    'success': False,
                    'error': str(error_msg),
                    'order_id': order_id,
                    'coin': coin_upper,
                    'message': str(error_msg),
                    'raw_response': cancel_result
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id,
                'coin': coin.upper() if coin else None,
                'message': str(e)
            }

    def close_position(
        self,
        coin: str,
        slippage: float = 0.01
    ) -> Dict[str, Any]:
        """
        Close an entire open position for a given asset.

        Places a market order to close the full position size in the opposite
        direction. Uses the exchange.market_close() method from the Hyperliquid SDK.

        Args:
            coin: Asset symbol to close position for (e.g., 'BTC', 'ETH').
            slippage: Maximum acceptable slippage as a decimal (default 0.01 = 1%).
                      Note: market_close may not use slippage parameter directly;
                      included for consistency and future compatibility.

        Returns:
            dict: Close result with structure:
                - 'success': Boolean indicating if position was closed
                - 'coin': Asset symbol
                - 'closed_size': Size of position that was closed
                - 'avg_price': Average close price
                - 'pnl': Realized PnL from closing (if available)
                - 'message': Success or error message
                - 'raw_response': Full response from exchange

        Example:
            # Close entire ETH position
            result = client.close_position('ETH')
            if result['success']:
                print(f"Closed {result['closed_size']} @ {result['avg_price']}")

        Notes:
            - This closes the ENTIRE position, not a partial amount
            - For partial closes, use market_order() with reduce_only=True
            - If no position exists, the call may succeed with 0 size closed
              or return an error depending on exchange behavior
        """
        if not coin:
            return {
                'success': False,
                'error': "coin parameter is required",
                'coin': None,
                'closed_size': 0.0,
                'avg_price': 0.0,
                'message': None
            }

        try:
            coin_upper = coin.upper()

            # First, check if there's actually a position to close
            positions_result = self.get_positions(coin_upper)
            if not positions_result.get('success'):
                return {
                    'success': False,
                    'error': f"Failed to check positions: {positions_result.get('error')}",
                    'coin': coin_upper,
                    'closed_size': 0.0,
                    'avg_price': 0.0,
                    'message': None
                }

            positions = positions_result.get('positions', [])
            if not positions:
                return {
                    'success': False,
                    'error': f"No open position found for {coin_upper}",
                    'coin': coin_upper,
                    'closed_size': 0.0,
                    'avg_price': 0.0,
                    'message': f"No position to close for {coin_upper}"
                }

            # Get position details for response
            position = positions[0]
            position_size = abs(position.get('size', 0))
            position_side = position.get('side', 'unknown')

            # Call exchange.market_close(coin) to close the position
            # Note: market_close closes the entire position
            close_result = self.exchange.market_close(coin_upper)

            # Parse the response
            if close_result.get("status") == "ok":
                response_data = close_result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])

                # Collect fill information
                closed_size = 0.0
                avg_price = 0.0
                errors = []

                for status in statuses:
                    if "filled" in status:
                        filled = status["filled"]
                        closed_size = float(filled.get("totalSz", 0))
                        avg_price = float(filled.get("avgPx", 0))
                    elif "error" in status:
                        errors.append(status["error"])

                if errors:
                    error_msg = "; ".join(errors)
                    error_category, is_retryable = categorize_trade_error(error_msg)
                    return {
                        'success': False,
                        'error': error_msg,
                        'error_category': error_category,
                        'is_retryable': is_retryable,
                        'coin': coin_upper,
                        'closed_size': closed_size,
                        'avg_price': avg_price,
                        'previous_side': position_side,
                        'previous_size': position_size,
                        'message': error_msg,
                        'statuses': statuses,
                        'raw_response': close_result
                    }

                return {
                    'success': True,
                    'coin': coin_upper,
                    'closed_size': closed_size,
                    'avg_price': avg_price,
                    'previous_side': position_side,
                    'previous_size': position_size,
                    'message': f"Position closed: {closed_size} {coin_upper} @ {avg_price}",
                    'statuses': statuses,
                    'raw_response': close_result
                }
            else:
                error_msg = close_result.get("response", {}).get("error", "Unknown error")
                if not error_msg:
                    error_msg = close_result.get("error", "Close failed")

                error_category, is_retryable = categorize_trade_error(str(error_msg))
                return {
                    'success': False,
                    'error': str(error_msg),
                    'error_category': error_category,
                    'is_retryable': is_retryable,
                    'coin': coin_upper,
                    'closed_size': 0.0,
                    'avg_price': 0.0,
                    'previous_side': position_side,
                    'previous_size': position_size,
                    'message': str(error_msg),
                    'raw_response': close_result
                }

        except Exception as e:
            error_msg = str(e)
            error_category, is_retryable = categorize_trade_error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_category': error_category,
                'is_retryable': is_retryable,
                'coin': coin.upper() if coin else None,
                'closed_size': 0.0,
                'avg_price': 0.0,
                'message': error_msg
            }


# =============================================================================
# Public Hyperliquid Client (No Authentication Required)
# =============================================================================

class PublicHyperliquidClient:
    """
    Public read-only client for Hyperliquid Info API.

    Provides access to market data without requiring authentication.
    No private key is needed - only public read-only endpoints are available.

    Key Features:
        - No private key required: Access public market data without authentication
        - Lazy initialization: Info client is created only when first accessed
        - skip_ws=True: Avoids WebSocket connections for REST-only access
        - Testnet/mainnet switching: Connect to either network

    Usage:
        # Basic initialization (testnet by default)
        client = PublicHyperliquidClient()

        # Production (mainnet)
        client = PublicHyperliquidClient(use_testnet=False)

        # Access Info API
        prices = client.info.all_mids()
    """

    def __init__(self, use_testnet: bool = True):
        """
        Initialize public Hyperliquid client.

        Args:
            use_testnet: Whether to connect to testnet (True) or mainnet (False).
                        Defaults to True for safety.

        Raises:
            ImportError: If hyperliquid-python-sdk is not installed
        """
        if not HYPERLIQUID_AVAILABLE:
            raise ImportError(
                "Hyperliquid SDK not available. Install with: "
                "pip install hyperliquid-python-sdk"
            )

        self.use_testnet = use_testnet

        # Determine base URL based on network
        if use_testnet:
            self.base_url = TESTNET_API_URL
        else:
            self.base_url = MAINNET_API_URL

        # Lazy-initialized Info client (use skip_ws=True to avoid WebSocket connections)
        self._info: Optional[Info] = None

    @property
    def info(self) -> Info:
        """
        Get Info client for read-only API calls (lazy initialized).

        The Info client is used for fetching market data, orderbook,
        candles, and other read-only operations. Uses skip_ws=True to avoid
        WebSocket connections per SDK best practices.

        Returns:
            Info: Hyperliquid Info client instance
        """
        if self._info is None:
            self._info = Info(self.base_url, skip_ws=True)
        return self._info

    @property
    def is_testnet(self) -> bool:
        """
        Check if client is connected to testnet.

        Returns:
            bool: True if connected to testnet, False if mainnet
        """
        return self.use_testnet

    @property
    def network_name(self) -> str:
        """
        Get human-readable network name.

        Returns:
            str: 'testnet' or 'mainnet'
        """
        return 'testnet' if self.use_testnet else 'mainnet'

    def is_connected(self) -> bool:
        """
        Check if client can connect to Hyperliquid API.

        Attempts a simple API call to verify connectivity.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # Use a lightweight API call to test connectivity
            self.info.all_mids()
            return True
        except Exception:
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.

        Returns:
            dict: Connection information including network and connectivity status
        """
        return {
            'network': self.network_name,
            'base_url': self.base_url,
            'authenticated': False,
            'connected': self.is_connected()
        }

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"PublicHyperliquidClient(network={self.network_name})"

    # =========================================================================
    # Market Data Methods
    # =========================================================================

    def get_candles(
        self,
        coin: str,
        interval: str = '1h',
        limit: int = 200
    ) -> Dict[str, Any]:
        """
        Get historical OHLCV candle data for a specific asset.

        Fetches candlestick data using the public Info API without authentication.
        Uses `info.candles_snapshot()` to retrieve historical price data.

        Args:
            coin: Asset symbol (e.g., 'BTC', 'ETH'). Required.
            interval: Candle interval/timeframe. Valid values include:
                      '1m', '5m', '15m', '30m', '1h', '4h', '1d'.
                      Defaults to '1h'.
            limit: Maximum number of candles to return. Defaults to 200.

        Returns:
            dict: Candle data with structure:
                - 'success': Boolean indicating success
                - 'coin': Asset symbol
                - 'interval': Candle interval used
                - 'candles': List of candle dicts, each containing:
                    - 'timestamp': ISO format timestamp
                    - 'timestamp_ms': Unix timestamp in milliseconds
                    - 'open': Open price
                    - 'high': High price
                    - 'low': Low price
                    - 'close': Close price
                    - 'volume': Trading volume
                - 'count': Number of candles returned
                - 'error': Error message if failed

        Example:
            # Get 100 hourly candles for BTC
            result = client.get_candles('BTC', interval='1h', limit=100)
            if result['success']:
                for candle in result['candles']:
                    print(f"{candle['timestamp']}: O={candle['open']}, C={candle['close']}")

            # Get 15-minute candles for ETH
            result = client.get_candles('ETH', interval='15m', limit=50)
        """
        if not coin:
            return {
                'success': False,
                'error': "coin parameter is required",
                'coin': None,
                'interval': interval,
                'candles': [],
                'count': 0
            }

        if limit <= 0:
            return {
                'success': False,
                'error': "limit must be greater than 0",
                'coin': coin.upper(),
                'interval': interval,
                'candles': [],
                'count': 0
            }

        try:
            import time
            from datetime import datetime

            coin_upper = coin.upper()

            # Calculate time range based on interval and limit
            # Approximate interval durations in seconds
            interval_seconds = {
                '1m': 60,
                '5m': 300,
                '15m': 900,
                '30m': 1800,
                '1h': 3600,
                '4h': 14400,
                '1d': 86400,
                '1w': 604800,
            }

            # Get interval duration (default to 1h if unknown)
            interval_duration = interval_seconds.get(interval, 3600)

            # End time is now
            end_time_ms = int(time.time() * 1000)

            # Start time is calculated from limit * interval_duration
            # Add buffer for potential gaps
            buffer_factor = 1.1
            start_time_ms = end_time_ms - int(limit * interval_duration * 1000 * buffer_factor)

            # Fetch candles using Info API
            # SDK signature: candles_snapshot(name, interval, startTime, endTime)
            raw_candles = self.info.candles_snapshot(
                coin_upper,
                interval,
                start_time_ms,
                end_time_ms
            )

            # Handle empty response
            if not raw_candles:
                return {
                    'success': True,
                    'coin': coin_upper,
                    'interval': interval,
                    'candles': [],
                    'count': 0,
                    'warning': f"No candle data available for {coin_upper}"
                }

            # Parse candle data
            # Hyperliquid candle format: {T: timestamp_ms, o: open, h: high, l: low, c: close, v: volume}
            parsed_candles = []
            for candle in raw_candles:
                try:
                    timestamp_ms = candle.get('T') or candle.get('t', 0)
                    parsed_candles.append({
                        'timestamp': datetime.fromtimestamp(timestamp_ms / 1000).isoformat(),
                        'timestamp_ms': timestamp_ms,
                        'open': float(candle.get('o', 0)),
                        'high': float(candle.get('h', 0)),
                        'low': float(candle.get('l', 0)),
                        'close': float(candle.get('c', 0)),
                        'volume': float(candle.get('v', 0))
                    })
                except (ValueError, TypeError) as e:
                    # Skip malformed candles but continue processing
                    continue

            # Limit the number of candles returned
            if len(parsed_candles) > limit:
                parsed_candles = parsed_candles[-limit:]

            return {
                'success': True,
                'coin': coin_upper,
                'interval': interval,
                'candles': parsed_candles,
                'count': len(parsed_candles)
            }

        except Exception as e:
            error_msg = str(e)
            # Check for common error patterns
            if 'not found' in error_msg.lower() or 'unknown' in error_msg.lower():
                error_msg = f"Market '{coin}' not found"

            return {
                'success': False,
                'error': error_msg,
                'coin': coin.upper() if coin else None,
                'interval': interval,
                'candles': [],
                'count': 0
            }

    def get_market_info(self, coin: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market metadata and asset context information.

        Fetches perpetual market metadata including size decimals, mark price,
        funding rate, open interest, and daily volume. No authentication required.

        Args:
            coin: Optional specific coin to filter (e.g., 'BTC', 'ETH').
                  If None, returns info for all perpetual markets.

        Returns:
            dict: Market information with structure:
                - 'markets': List of market info dicts (or single market if coin specified)
                - 'success': Boolean indicating success
                - 'error': Error message if failed

                Each market dict contains:
                - 'name': Asset name (e.g., 'BTC')
                - 'sz_decimals': Size decimals for the asset
                - 'mark_px': Current mark price
                - 'funding': Current funding rate
                - 'open_interest': Open interest in USD
                - 'day_volume': 24h notional volume

        Example:
            # Get all markets
            info = client.get_market_info()

            # Get specific market
            btc_info = client.get_market_info('BTC')
        """
        try:
            # Get metadata with asset contexts (prices, funding, volumes)
            meta_and_ctx = self.info.meta_and_asset_ctxs()
            universe, contexts = meta_and_ctx

            markets = []
            for idx, ctx in enumerate(contexts):
                asset = universe["universe"][idx]
                market_data = {
                    'name': asset['name'],
                    'sz_decimals': asset.get('szDecimals', 0),
                    'mark_px': float(ctx.get('markPx', 0)),
                    'funding': float(ctx.get('funding', 0)),
                    'open_interest': float(ctx.get('openInterest', 0)),
                    'day_volume': float(ctx.get('dayNtlVlm', 0)),
                }
                markets.append(market_data)

            # Filter by coin if specified
            if coin:
                coin_upper = coin.upper()
                filtered = [m for m in markets if m['name'].upper() == coin_upper]
                if not filtered:
                    return {
                        'success': False,
                        'error': f"Market '{coin}' not found",
                        'markets': []
                    }
                return {
                    'success': True,
                    'markets': filtered[0]  # Return single market dict
                }

            return {
                'success': True,
                'markets': markets
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'markets': []
            }

    def get_orderbook(
        self,
        coin: str,
        depth: int = 5
    ) -> Dict[str, Any]:
        """
        Get L2 order book snapshot for a specific market.

        Retrieves the current order book with bid and ask levels, including
        price and size at each level. No authentication required.

        Args:
            coin: Asset symbol (e.g., 'BTC', 'ETH'). Required.
            depth: Number of price levels to return on each side.
                   Defaults to 5. Max available depends on exchange.

        Returns:
            dict: Order book data with structure:
                - 'coin': Asset symbol
                - 'bids': List of bid levels [{'px': price, 'sz': size}, ...]
                - 'asks': List of ask levels [{'px': price, 'sz': size}, ...]
                - 'best_bid': Best (highest) bid price
                - 'best_ask': Best (lowest) ask price
                - 'spread': Spread between best ask and best bid
                - 'spread_pct': Spread as percentage of mid price
                - 'mid_price': Mid price between best bid and ask
                - 'success': Boolean indicating success
                - 'error': Error message if failed

        Example:
            orderbook = client.get_orderbook('ETH', depth=10)
            print(f"Best bid: {orderbook['best_bid']}")
            print(f"Best ask: {orderbook['best_ask']}")
            print(f"Spread: {orderbook['spread_pct']:.4f}%")
        """
        if not coin:
            return {
                'success': False,
                'error': "coin parameter is required",
                'coin': None,
                'bids': [],
                'asks': []
            }

        try:
            coin_upper = coin.upper()
            l2_snapshot = self.info.l2_snapshot(coin_upper)

            # Extract levels from snapshot
            levels = l2_snapshot.get('levels', [[], []])
            bids_raw = levels[0] if len(levels) > 0 else []
            asks_raw = levels[1] if len(levels) > 1 else []

            # Process and limit depth
            bids = [
                {'px': float(b['px']), 'sz': float(b['sz'])}
                for b in bids_raw[:depth]
            ]
            asks = [
                {'px': float(a['px']), 'sz': float(a['sz'])}
                for a in asks_raw[:depth]
            ]

            # Calculate spread metrics
            best_bid = bids[0]['px'] if bids else 0.0
            best_ask = asks[0]['px'] if asks else 0.0
            spread = best_ask - best_bid if (best_bid and best_ask) else 0.0

            # Calculate spread percentage (relative to mid price)
            mid_price = (best_bid + best_ask) / 2 if (best_bid and best_ask) else 0.0
            spread_pct = (spread / mid_price * 100) if mid_price > 0 else 0.0

            return {
                'success': True,
                'coin': l2_snapshot.get('coin', coin_upper),
                'bids': bids,
                'asks': asks,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid_price': mid_price,
                'spread': spread,
                'spread_pct': spread_pct
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'coin': coin.upper() if coin else None,
                'bids': [],
                'asks': []
            }

    def get_prices(self, coins: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get current mid prices for assets.

        Retrieves real-time mid prices (average of best bid and ask) for
        all perpetual assets or a specific subset. No authentication required.

        Args:
            coins: Optional list of coin symbols to filter (e.g., ['BTC', 'ETH']).
                   If None, returns prices for all available assets.

        Returns:
            dict: Price information with structure:
                - 'prices': Dict mapping coin symbol to mid price
                - 'success': Boolean indicating success
                - 'error': Error message if failed
                - 'warning': Warning message if some coins not found

        Example:
            # Get all prices
            all_prices = client.get_prices()
            print(all_prices['prices']['BTC'])

            # Get specific prices
            prices = client.get_prices(['BTC', 'ETH'])
        """
        try:
            all_mids = self.info.all_mids()

            # Convert to float for consistency
            prices = {k: float(v) for k, v in all_mids.items()}

            # Filter by coins if specified
            if coins:
                coins_upper = [c.upper() for c in coins]
                filtered = {}
                not_found = []

                for coin in coins_upper:
                    if coin in prices:
                        filtered[coin] = prices[coin]
                    else:
                        not_found.append(coin)

                if not_found:
                    return {
                        'success': True,
                        'prices': filtered,
                        'warning': f"Coins not found: {', '.join(not_found)}"
                    }

                return {
                    'success': True,
                    'prices': filtered
                }

            return {
                'success': True,
                'prices': prices
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prices': {}
            }


# =============================================================================
# Module-Level Convenience Functions and Singleton
# =============================================================================

# Global client instances (initialized lazily)
_client: Optional[HyperliquidClient] = None
_public_client: Optional[PublicHyperliquidClient] = None


def get_hl_client(
    private_key: Optional[str] = None,
    account_address: Optional[str] = None,
    use_testnet: Optional[bool] = None,
    force_new: bool = False
) -> Optional[HyperliquidClient]:
    """
    Get the global Hyperliquid client instance (singleton pattern).

    Creates a new client on first call or when force_new=True.
    Configuration is resolved in this order:
        1. Explicit parameters passed to this function
        2. Database settings (via get_hyperliquid_config from settings.py)
        3. Environment variables as final fallback

    Environment variables (fallback):
        - HYPERLIQUID_WALLET_PRIVATE_KEY: API wallet private key
        - HYPERLIQUID_ACCOUNT_ADDRESS: Main account address (optional)
        - HYPERLIQUID_TESTNET: Use testnet ('true'/'false', default: 'true')

    Args:
        private_key: Override private key (uses db/env if not provided)
        account_address: Override account address (uses db/env if not provided)
        use_testnet: Override testnet setting (uses db/env if not provided)
        force_new: Force creation of a new client instance

    Returns:
        HyperliquidClient: Configured client instance, or None if SDK not available
                          or no private key configured

    Example:
        # First call initializes from database or environment
        client = get_hl_client()

        # Subsequent calls return same instance
        client = get_hl_client()

        # Force new instance with different config
        client = get_hl_client(use_testnet=False, force_new=True)
    """
    global _client

    if not HYPERLIQUID_AVAILABLE:
        return None

    if _client is not None and not force_new:
        return _client

    # Try to get configuration from database first, then fall back to environment
    db_config = None
    try:
        from settings import get_hyperliquid_config
        db_config = get_hyperliquid_config()
    except ImportError:
        # settings module not available (e.g., in standalone use)
        db_config = None
    except Exception:
        # Database unavailable - fall back to environment
        db_config = None

    # Resolve private key: explicit param > database > environment
    if private_key is None:
        if db_config and db_config.get('private_key'):
            private_key = db_config['private_key']
        else:
            private_key = os.environ.get('HYPERLIQUID_WALLET_PRIVATE_KEY')

    if private_key is None:
        # No private key configured - return None
        return None

    # Resolve account address: explicit param > database > environment
    if account_address is None:
        if db_config and db_config.get('account_address'):
            account_address = db_config['account_address']
        else:
            account_address = os.environ.get('HYPERLIQUID_ACCOUNT_ADDRESS')

    # Resolve testnet setting: explicit param > database > environment
    if use_testnet is None:
        if db_config and 'testnet' in db_config:
            use_testnet = db_config['testnet']
        else:
            testnet_env = os.environ.get('HYPERLIQUID_TESTNET', 'true').lower()
            use_testnet = testnet_env in ('true', '1', 'yes')

    try:
        _client = HyperliquidClient(
            private_key=private_key,
            account_address=account_address,
            use_testnet=use_testnet
        )
        return _client
    except (ImportError, ValueError) as e:
        # Log error but don't crash - return None
        import logging
        logging.getLogger(__name__).warning(f"Failed to initialize Hyperliquid client: {e}")
        return None


def reset_hl_client() -> None:
    """
    Reset the global Hyperliquid client instance.

    Call this to force re-initialization on the next get_hl_client() call.
    The next call will reload configuration from the database settings
    (via get_hyperliquid_config), picking up any wallet key changes made
    via the API or CLI.

    Useful when:
        - Wallet private key is updated via API/CLI/frontend
        - Network is switched between testnet and mainnet
        - Account address is changed
        - Environment variables change
        - For testing purposes
    """
    global _client
    _client = None


def is_hl_available() -> bool:
    """
    Check if Hyperliquid SDK is available.

    Returns:
        bool: True if hyperliquid-python-sdk is installed, False otherwise
    """
    return HYPERLIQUID_AVAILABLE


def get_public_client(
    use_testnet: Optional[bool] = None,
    force_new: bool = False
) -> Optional[PublicHyperliquidClient]:
    """
    Get the global public Hyperliquid client instance (singleton pattern).

    Creates a new client on first call or when force_new=True.
    No authentication is required - this client provides read-only access
    to public market data endpoints.

    Configuration is resolved in this order:
        1. Explicit use_testnet parameter
        2. Environment variable HYPERLIQUID_TESTNET
        3. Default to testnet (True) for safety

    Args:
        use_testnet: Whether to use testnet (True) or mainnet (False).
                    If not provided, checks HYPERLIQUID_TESTNET env var,
                    then defaults to True.
        force_new: Force creation of a new client instance

    Returns:
        PublicHyperliquidClient: Configured public client instance,
                                 or None if SDK not available

    Example:
        # Get public client for market data
        client = get_public_client()

        # Access market prices
        prices = client.info.all_mids()

        # Force mainnet client
        client = get_public_client(use_testnet=False, force_new=True)
    """
    global _public_client

    if not HYPERLIQUID_AVAILABLE:
        return None

    if _public_client is not None and not force_new:
        return _public_client

    # Resolve testnet setting: explicit param > environment > default (True)
    if use_testnet is None:
        testnet_env = os.environ.get('HYPERLIQUID_TESTNET', 'true').lower()
        use_testnet = testnet_env in ('true', '1', 'yes')

    try:
        _public_client = PublicHyperliquidClient(use_testnet=use_testnet)
        return _public_client
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to initialize public Hyperliquid client: {e}")
        return None


def reset_public_client() -> None:
    """
    Reset the global public Hyperliquid client instance.

    Call this to force re-initialization on the next get_public_client() call.
    Useful when:
        - Network is switched between testnet and mainnet
        - Environment variables change
        - For testing purposes
    """
    global _public_client
    _public_client = None


def check_hl_health() -> Dict[str, Any]:
    """
    Check Hyperliquid service health and connectivity.

    Returns:
        dict: Health check results including:
            - sdk_available: Whether SDK is installed
            - configured: Whether credentials are configured
            - connected: Whether API is reachable
            - network: Current network (testnet/mainnet)
            - wallet_address: Wallet address (if configured)
            - trading_address: Trading address (if configured)
    """
    result = {
        'sdk_available': HYPERLIQUID_AVAILABLE,
        'configured': False,
        'connected': False,
        'network': None,
        'wallet_address': None,
        'trading_address': None
    }

    if not HYPERLIQUID_AVAILABLE:
        return result

    client = get_hl_client()
    if client is None:
        return result

    result['configured'] = True
    result['network'] = client.network_name
    result['wallet_address'] = client.wallet_address
    result['trading_address'] = client.trading_address

    try:
        result['connected'] = client.is_connected()
    except Exception:
        result['connected'] = False

    return result
