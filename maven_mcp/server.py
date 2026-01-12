"""
Maven MCP Server - Main Entry Point.

Bootstraps the MCP server for Maven, the AI CFO assistant. Registers all
resources and tools, then runs the server using stdio transport for
integration with Claude Desktop and other MCP clients.

Example usage:
    # Run as module
    python -m services.maven_mcp.server

    # Import and run programmatically
    from services.maven_mcp.server import main
    main()

Claude Desktop configuration (add to claude_desktop_config.json):
    {
        "mcpServers": {
            "maven": {
                "command": "python",
                "args": ["-m", "services.maven_mcp.server"],
                "cwd": "/path/to/project"
            }
        }
    }
"""
import logging
import sys

from mcp.server.fastmcp import FastMCP

from .config import SERVER_CONFIG, ensure_directories
from .resources import RESOURCES, register_resources
from .tools import TOOLS, register_tools


# =============================================================================
# Logging Configuration
# =============================================================================

# Configure logging to stderr to avoid interfering with stdio transport
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# =============================================================================
# FastMCP Server Instance
# =============================================================================

# Create the FastMCP server instance for Maven operations
mcp = FastMCP(SERVER_CONFIG["name"])


# =============================================================================
# Server Initialization
# =============================================================================

def _initialize_server() -> None:
    """
    Initialize the MCP server with resources and tools.

    Registers all Maven resources and tools with the FastMCP server instance.
    Also ensures required directories exist for data storage.
    """
    # Ensure data directories exist
    ensure_directories()
    logger.info("Ensured Maven data directories exist")

    # Register resources
    register_resources(mcp)
    logger.info(f"Registered {len(RESOURCES)} Maven resources")

    # Register tools
    register_tools(mcp)
    logger.info(f"Registered {len(TOOLS)} Maven tools")


# =============================================================================
# Entry Points
# =============================================================================

def run() -> None:
    """
    Run the Maven MCP server.

    Initializes all resources and tools, then starts the server
    using stdio transport for MCP client communication.
    """
    logger.info("Starting Maven MCP Server...")
    _initialize_server()

    logger.info(f"Maven MCP Server running: {SERVER_CONFIG['name']}")
    logger.info(f"Resources: {len(RESOURCES)}, Tools: {len(TOOLS)}")

    # Run with stdio transport
    mcp.run(transport="stdio")


def main() -> None:
    """
    Main entry point for the Maven MCP server.

    This function is called when running the module directly:
        python -m services.maven_mcp.server
    """
    try:
        run()
    except KeyboardInterrupt:
        logger.info("Maven MCP Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Maven MCP Server error: {e}")
        sys.exit(1)


# =============================================================================
# Module Execution
# =============================================================================

if __name__ == "__main__":
    main()
