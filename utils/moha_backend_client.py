"""
Client for communicating with moha-bot backend API.

When Maven is deployed alongside moha-bot, she can query the backend
for additional context about trading operations, bot status, etc.
"""
import os
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# moha-bot backend URL (when deployed together)
MOHA_BACKEND_URL = os.getenv('MOHA_BACKEND_URL', 'http://moha_backend:5001')

def get_bot_status() -> Optional[Dict[str, Any]]:
    """
    Get current status of moha-bot trading system.

    Returns:
        dict: Bot status or None if unavailable
    """
    try:
        response = requests.get(f"{MOHA_BACKEND_URL}/api/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.debug(f"Could not reach moha-bot backend: {e}")
        return None

def get_active_positions() -> Optional[Dict[str, Any]]:
    """
    Get currently active trading positions.

    Returns:
        dict: Position data or None if unavailable
    """
    try:
        response = requests.get(f"{MOHA_BACKEND_URL}/api/positions", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.debug(f"Could not fetch positions from moha-bot: {e}")
        return None

def get_recent_trades(limit: int = 10) -> Optional[list]:
    """
    Get recent trade history.

    Args:
        limit: Number of recent trades to fetch

    Returns:
        list: Trade history or None if unavailable
    """
    try:
        response = requests.get(
            f"{MOHA_BACKEND_URL}/api/trades",
            params={'limit': limit},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.debug(f"Could not fetch trades from moha-bot: {e}")
        return None

def get_account_balance() -> Optional[Dict[str, Any]]:
    """
    Get current account balance and equity.

    Returns:
        dict: Account data or None if unavailable
    """
    try:
        response = requests.get(f"{MOHA_BACKEND_URL}/api/account", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.debug(f"Could not fetch account data from moha-bot: {e}")
        return None

def is_moha_backend_available() -> bool:
    """
    Check if moha-bot backend is accessible.

    Returns:
        bool: True if backend is reachable
    """
    try:
        response = requests.get(f"{MOHA_BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_full_context() -> Dict[str, Any]:
    """
    Get comprehensive context from moha-bot backend.

    Returns:
        dict: All available backend context
    """
    context = {
        'backend_available': is_moha_backend_available(),
        'bot_status': None,
        'positions': None,
        'recent_trades': None,
        'account': None
    }

    if context['backend_available']:
        context['bot_status'] = get_bot_status()
        context['positions'] = get_active_positions()
        context['recent_trades'] = get_recent_trades(limit=5)
        context['account'] = get_account_balance()

    return context
