"""
Configuration for Maven MCP Server.

Provides path configuration for Maven's data files and server settings.
Uses environment variables for customization with sensible defaults.
"""
import os
from pathlib import Path


# =============================================================================
# Base Directory Configuration
# =============================================================================

# Base directory for Maven data - defaults to project root's .moha/maven/
# From maven_mcp/config.py: parent=maven_mcp, parent.parent=/app (project root)
_base_dir = os.getenv('MAVEN_BASE_DIR', str(Path(__file__).parent.parent))
MAVEN_DATA_DIR = Path(_base_dir) / ".moha" / "maven"


# =============================================================================
# Path Configuration
# =============================================================================

PATHS = {
    "base": MAVEN_DATA_DIR,
    "identity": MAVEN_DATA_DIR / "identity.json",
    "personas_dir": MAVEN_DATA_DIR / "personas",
    "persona": MAVEN_DATA_DIR / "personas" / "maven-v1.md",
    "session_log": MAVEN_DATA_DIR / "session_log.md",
    "decisions_dir": MAVEN_DATA_DIR / "decisions",
    "milestones_dir": MAVEN_DATA_DIR / "milestones",
    "infrastructure": MAVEN_DATA_DIR / "infrastructure.json",
}


# =============================================================================
# Server Configuration
# =============================================================================

SERVER_CONFIG = {
    "name": "maven-mcp",
    "host": os.getenv("MAVEN_MCP_HOST", "localhost"),
    "port": int(os.getenv("MAVEN_MCP_PORT", "3100")),
    "transport": "stdio",
}


# =============================================================================
# Git Remote Configuration (for syncing memory from anywhere)
# =============================================================================

GIT_REMOTE_CONFIG = {
    "repo": "itripleg/moha-maven",
    "branch": "master",
    "raw_base": "https://raw.githubusercontent.com/itripleg/moha-maven/master/.moha/maven",
    "files_to_sync": [
        ("identity.json", "identity"),
        ("session_log.md", "session_log"),
        ("infrastructure.json", "infrastructure"),
    ],
}


# =============================================================================
# Utility Functions
# =============================================================================

def get_iso_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def ensure_directories():
    """Ensure all required directories exist."""
    PATHS["base"].mkdir(parents=True, exist_ok=True)
    PATHS["personas_dir"].mkdir(parents=True, exist_ok=True)
    PATHS["decisions_dir"].mkdir(parents=True, exist_ok=True)
    PATHS["milestones_dir"].mkdir(parents=True, exist_ok=True)


def deep_merge(base: dict, update: dict) -> dict:
    """Deep merge two dictionaries, with update values taking precedence."""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
