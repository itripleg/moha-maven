"""
Hyperliquid API client wrapper.

This module provides a centralized wrapper for the Hyperliquid SDK
with connection management, error handling, and testnet/mainnet switching.
"""

import time
from typing import Optional
import eth_account
from eth_account.signers.local import LocalAccount

from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants


class HyperliquidClient:
    """
    Wrapper for Hyperliquid Info and Exchange APIs.

    Handles connection lifecycle, testnet/mainnet switching, and error handling.

    Example:
        ```python
        client = HyperliquidClient(private_key="0x123...", use_testnet=True)
        if client.test_connection():
            info = client.get_info()
            prices = info.all_mids()
        ```
    """

    def __init__(self, private_key: str, account_address: Optional[str] = None, use_testnet: bool = True):
        """
        Initialize Hyperliquid client with wallet credentials.

        Args:
            private_key: API wallet private key (hex string, with or without 0x prefix)
            account_address: Main account address (for API wallets). If None, uses wallet address.
            use_testnet: Use testnet if True, mainnet if False
        """
        # Normalize private key (ensure 0x prefix)
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key

        # Create account from private key
        self.account: LocalAccount = eth_account.Account.from_key(private_key)
        self.use_testnet = use_testnet

        # Use account_address if provided, otherwise derive from private key
        self.address = account_address or self.account.address

        # Determine base URL
        if use_testnet:
            self.base_url = constants.TESTNET_API_URL
        else:
            self.base_url = constants.MAINNET_API_URL

        # Lazy initialization
        self._info: Optional[Info] = None
        self._exchange: Optional[Exchange] = None

    def get_info(self) -> Info:
        """
        Get Info API instance (lazy initialization).

        Returns:
            Hyperliquid Info API instance
        """
        if self._info is None:
            self._info = Info(self.base_url, skip_ws=True)
        return self._info

    def get_exchange(self) -> Exchange:
        """
        Get Exchange API instance (lazy initialization).

        Returns:
            Hyperliquid Exchange API instance
        """
        if self._exchange is None:
            self._exchange = Exchange(
                self.account,
                self.base_url,
                account_address=self.address if self.address != self.account.address else None
            )
        return self._exchange

    def get_wallet_address(self) -> str:
        """
        Get API wallet address from private key.

        Returns:
            Ethereum address (0x...)
        """
        return self.account.address

    def get_account_address(self) -> str:
        """
        Get main account address (for querying balance/positions).

        Returns:
            Ethereum address (0x...)
        """
        return self.address

    def test_connection(self, max_retries: int = 3) -> bool:
        """
        Test API connectivity by fetching all_mids().

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            True if connection successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                info = self.get_info()
                # Test connection with a simple API call
                all_mids = info.all_mids()

                # Verify we got data
                if all_mids and len(all_mids) > 0:
                    return True
                else:
                    print(f"[WARNING] API returned empty data", flush=True)
                    return False

            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    print(f"[ERROR] Connection test failed after {max_retries} attempts: {e}", flush=True)
                    return False
                else:
                    # Retry with exponential backoff
                    delay = 2 ** attempt
                    print(f"[RETRY] Connection attempt {attempt + 1} failed: {e}. Retrying in {delay}s...", flush=True)
                    time.sleep(delay)

        return False

    def close(self):
        """
        Cleanup connections.

        Currently a no-op but can be extended for WebSocket cleanup if needed.
        """
        # Info and Exchange don't require explicit cleanup in skip_ws mode
        pass

    def __repr__(self) -> str:
        """String representation of client."""
        network = "Testnet" if self.use_testnet else "Mainnet"
        return f"HyperliquidClient(wallet={self.get_wallet_address()}, network={network})"
