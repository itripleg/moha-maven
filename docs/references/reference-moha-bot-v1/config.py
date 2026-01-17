"""
Configuration management for motherhaven v2.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Hyperliquid
    hyperliquid_wallet_private_key: str = Field(default="")
    hyperliquid_account_address: str = Field(
        default="",
        description="Hyperliquid main account address (for API wallets, use main account address)"
    )
    hyperliquid_testnet: bool = Field(default=True)

    # LLM
    anthropic_api_key: str = Field(default="")

    # Trading
    trading_mode: str = Field(default="paper")  # paper or live
    max_position_size_usd: float = Field(default=500.0)
    max_leverage: int = Field(default=5)
    execution_interval_seconds: int = Field(default=180)

    # Assets
    trading_assets: str = Field(default="BTC")

    # Flask
    port: int = Field(default=5000)
    flask_env: str = Field(default="development")
    flask_debug: bool = Field(default=True)

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_enabled: bool = Field(default=True)
    redis_db: int = Field(default=0)
    redis_password: str = Field(default="")
    redis_key_prefix: str = Field(default="moha")

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_trading_assets(self) -> list[str]:
        """Get trading assets as list."""
        return [asset.strip() for asset in self.trading_assets.split(",")]

    def is_live_trading(self) -> bool:
        """Check if live trading is enabled."""
        return self.trading_mode.lower() == "live"

    def is_redis_enabled(self) -> bool:
        """Check if Redis is enabled and configured."""
        return self.redis_enabled and bool(self.redis_host)


# Global settings instance
settings = Settings()
