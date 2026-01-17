"""
Maven Hyperliquid MCP Server - Market Data & Trading Intelligence.

Provides real-time Hyperliquid data access for Maven's trading analysis.
Includes all standard HL info endpoints plus Maven-specific aggregations.

Port: 3101 (inside Maven docker network)
"""
import json
import os
import logging
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import iso8601
from hyperliquid.info import Info
from hyperliquid.utils import constants
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize Hyperliquid Info client (mainnet)
info = Info(constants.MAINNET_API_URL, skip_ws=True)

# Create MCP server
mcp = FastMCP(
    name="Maven Hyperliquid",
    dependencies=["hyperliquid-python-sdk", "python-iso8601"]
)

# =============================================================================
# MARKET DATA TOOLS
# =============================================================================

@mcp.tool()
async def get_all_mids(ctx: Context = None) -> str:
    """Get mid prices for ALL trading pairs on Hyperliquid (239+ perps, 48 spot)."""
    try:
        all_mids = info.all_mids()
        return json.dumps(all_mids)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch all mids: {str(e)}"})


@mcp.tool()
async def get_perp_metadata(include_asset_ctxs: bool = False, ctx: Context = None) -> str:
    """
    Get metadata for ALL perpetual markets including equity perps.

    Returns universe of tradeable perps with leverage limits, tick sizes, etc.
    Equity perps include: NVDA, TSLA, AAPL, MSFT, PLTR, HOOD, META, AMZN, GOOGL, AMD, COIN, NFLX
    """
    try:
        data = info.meta_and_asset_ctxs() if include_asset_ctxs else info.meta()
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch perpetual metadata: {str(e)}"})


@mcp.tool()
async def get_spot_metadata(include_asset_ctxs: bool = False, ctx: Context = None) -> str:
    """Get metadata for all spot markets on Hyperliquid."""
    try:
        data = info.spot_meta_and_asset_ctxs() if include_asset_ctxs else info.spot_meta()
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch spot metadata: {str(e)}"})


@mcp.tool()
async def get_l2_snapshot(coin: str, ctx: Context = None) -> str:
    """
    Get Level 2 order book snapshot for a specific coin.

    Args:
        coin: Trading symbol (e.g., 'BTC', 'ETH', 'NVDA')
    """
    try:
        data = info.l2_snapshot(coin)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch L2 snapshot for {coin}: {str(e)}"})


@mcp.tool()
async def get_candles(
    coin: str,
    interval: str = "1h",
    lookback_hours: int = 24,
    ctx: Context = None
) -> str:
    """
    Get candlestick data for a coin.

    Args:
        coin: Trading symbol (e.g., 'BTC', 'ETH', 'NVDA')
        interval: Candle interval ('1m', '5m', '15m', '1h', '4h', '1d')
        lookback_hours: Hours of history to fetch (default 24)
    """
    try:
        end_ms = int(datetime.now().timestamp() * 1000)
        start_ms = int((datetime.now() - timedelta(hours=lookback_hours)).timestamp() * 1000)
        data = info.candles_snapshot(coin, interval, start_ms, end_ms)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch candles for {coin}: {str(e)}"})


@mcp.tool()
async def get_funding_rates(coin: str, lookback_hours: int = 168, ctx: Context = None) -> str:
    """
    Get funding rate history for a coin.

    Args:
        coin: Trading symbol
        lookback_hours: Hours of history (default 168 = 1 week)
    """
    try:
        end_ms = int(datetime.now().timestamp() * 1000)
        start_ms = int((datetime.now() - timedelta(hours=lookback_hours)).timestamp() * 1000)
        data = info.funding_history(coin, start_ms, end_ms)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch funding for {coin}: {str(e)}"})


# =============================================================================
# USER/ACCOUNT TOOLS
# =============================================================================

@mcp.tool()
async def get_user_state(address: str, check_spot: bool = False, ctx: Context = None) -> str:
    """
    Get user's trading state including positions, margin, and withdrawable balance.

    Args:
        address: Hyperliquid wallet address
        check_spot: If True, query spot state instead of perps
    """
    try:
        data = info.spot_user_state(address) if check_spot else info.user_state(address)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch user state: {str(e)}"})


@mcp.tool()
async def get_user_positions(address: str, ctx: Context = None) -> str:
    """
    Get user's open positions with PnL details.

    Args:
        address: Hyperliquid wallet address
    """
    try:
        state = info.user_state(address)
        positions = state.get("assetPositions", [])
        # Filter to only positions with non-zero size
        active = [p for p in positions if float(p.get("position", {}).get("szi", 0)) != 0]
        return json.dumps({
            "address": address,
            "active_positions": len(active),
            "positions": active
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch positions: {str(e)}"})


@mcp.tool()
async def get_user_open_orders(address: str, ctx: Context = None) -> str:
    """Get all open orders for a user."""
    try:
        data = info.open_orders(address)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch open orders: {str(e)}"})


@mcp.tool()
async def get_user_fills(address: str, lookback_hours: int = 24, ctx: Context = None) -> str:
    """
    Get user's recent trade fills.

    Args:
        address: Hyperliquid wallet address
        lookback_hours: Hours of history (default 24)
    """
    try:
        data = info.user_fills(address)
        # Filter by time if needed
        cutoff = int((datetime.now() - timedelta(hours=lookback_hours)).timestamp() * 1000)
        recent = [f for f in data if f.get("time", 0) >= cutoff]
        return json.dumps(recent)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch fills: {str(e)}"})


@mcp.tool()
async def get_user_funding_payments(
    address: str,
    lookback_hours: int = 168,
    ctx: Context = None
) -> str:
    """
    Get user's funding payment history.

    Args:
        address: Hyperliquid wallet address
        lookback_hours: Hours of history (default 168 = 1 week)
    """
    try:
        end_ms = int(datetime.now().timestamp() * 1000)
        start_ms = int((datetime.now() - timedelta(hours=lookback_hours)).timestamp() * 1000)
        data = info.user_funding_history(address, start_ms, end_ms)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch funding payments: {str(e)}"})


@mcp.tool()
async def get_user_fees(address: str, ctx: Context = None) -> str:
    """Get user's fee structure (maker/taker rates)."""
    try:
        data = info.user_fees(address)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch fees: {str(e)}"})


# =============================================================================
# MAVEN-SPECIFIC AGGREGATIONS
# =============================================================================

@mcp.tool()
async def get_market_overview(ctx: Context = None) -> str:
    """
    Get comprehensive market overview for Maven's analysis.

    Returns top movers, funding extremes, and market summary.
    """
    try:
        mids = info.all_mids()
        meta = info.meta_and_asset_ctxs()

        # Extract asset contexts for additional data
        asset_ctxs = meta[1] if len(meta) > 1 else []
        universe = meta[0].get("universe", []) if meta else []

        # Build summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_perps": len(universe),
            "total_mids": len(mids),
            "sample_prices": {k: v for k, v in list(mids.items())[:20]},
            "equity_perps": [u["name"] for u in universe if u.get("name", "").upper() in
                           ["NVDA", "TSLA", "AAPL", "MSFT", "PLTR", "HOOD", "META", "AMZN", "GOOGL", "AMD", "COIN", "NFLX"]]
        }

        return json.dumps(summary)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch market overview: {str(e)}"})


@mcp.tool()
async def get_moha_treasury_state(ctx: Context = None) -> str:
    """
    Get MoHa treasury account state (execution wallet).

    Monitors: 0xF60c2792722fDae7A8Df69D1b83C40a837E55A4A
    """
    try:
        MOHA_WALLET = "0xF60c2792722fDae7A8Df69D1b83C40a837E55A4A"

        state = info.user_state(MOHA_WALLET)
        positions = state.get("assetPositions", [])
        margin = state.get("marginSummary", {})

        active_positions = [p for p in positions if float(p.get("position", {}).get("szi", 0)) != 0]

        return json.dumps({
            "wallet": MOHA_WALLET,
            "timestamp": datetime.now().isoformat(),
            "account_value": margin.get("accountValue", "0"),
            "withdrawable": state.get("withdrawable", "0"),
            "margin_used": margin.get("totalMarginUsed", "0"),
            "active_positions": len(active_positions),
            "positions": active_positions
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch treasury state: {str(e)}"})


@mcp.tool()
async def get_boss_positions(ctx: Context = None) -> str:
    """
    Get Boss's main dev wallet positions (for copy trading reference).

    Monitors: 0xd85327505Ab915AB0C1aa5bC6768bF4002732258
    """
    try:
        BOSS_WALLET = "0xd85327505Ab915AB0C1aa5bC6768bF4002732258"

        state = info.user_state(BOSS_WALLET)
        positions = state.get("assetPositions", [])
        margin = state.get("marginSummary", {})

        active_positions = [p for p in positions if float(p.get("position", {}).get("szi", 0)) != 0]

        return json.dumps({
            "wallet": BOSS_WALLET,
            "timestamp": datetime.now().isoformat(),
            "account_value": margin.get("accountValue", "0"),
            "active_positions": len(active_positions),
            "positions": active_positions
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch boss positions: {str(e)}"})


@mcp.tool()
async def analyze_coin(coin: str, ctx: Context = None) -> str:
    """
    Comprehensive analysis of a single coin for trading decisions.

    Includes: price, L2 depth, recent candles, funding rate.

    Args:
        coin: Trading symbol (e.g., 'BTC', 'ETH', 'NVDA')
    """
    try:
        # Gather all data
        mids = info.all_mids()
        l2 = info.l2_snapshot(coin)

        # Get 4h candles for last 24h
        end_ms = int(datetime.now().timestamp() * 1000)
        start_ms = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
        candles = info.candles_snapshot(coin, "4h", start_ms, end_ms)

        # Get funding for last 24h
        funding = info.funding_history(coin, start_ms, end_ms)

        # Calculate simple metrics
        current_price = float(mids.get(coin, 0))

        # L2 analysis
        bids = l2.get("levels", [[]])[0]
        asks = l2.get("levels", [[], []])[1]
        bid_depth = sum(float(b.get("sz", 0)) for b in bids[:10]) if bids else 0
        ask_depth = sum(float(a.get("sz", 0)) for a in asks[:10]) if asks else 0

        # Funding analysis
        avg_funding = sum(float(f.get("fundingRate", 0)) for f in funding) / len(funding) if funding else 0

        analysis = {
            "coin": coin,
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price,
            "l2_analysis": {
                "bid_depth_10": bid_depth,
                "ask_depth_10": ask_depth,
                "depth_ratio": bid_depth / ask_depth if ask_depth > 0 else 0,
                "bias": "bullish" if bid_depth > ask_depth * 1.1 else "bearish" if ask_depth > bid_depth * 1.1 else "neutral"
            },
            "funding": {
                "data_points": len(funding),
                "avg_rate": avg_funding,
                "bias": "shorts_paying" if avg_funding > 0 else "longs_paying" if avg_funding < 0 else "neutral"
            },
            "candles_24h": len(candles)
        }

        return json.dumps(analysis)
    except Exception as e:
        return json.dumps({"error": f"Failed to analyze {coin}: {str(e)}"})


# =============================================================================
# SERVER ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", 3101))
    logger.info(f"Starting Maven Hyperliquid MCP Server on port {port}")
    logger.info("Available tools: get_all_mids, get_perp_metadata, get_spot_metadata, get_l2_snapshot, get_candles, get_funding_rates, get_user_state, get_user_positions, get_user_open_orders, get_user_fills, get_user_funding_payments, get_user_fees, get_market_overview, get_moha_treasury_state, get_boss_positions, analyze_coin")
    mcp.run(transport="stdio")
