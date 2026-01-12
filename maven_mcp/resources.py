"""
Maven MCP Resources - Read-only context providers.

Provides MCP resources for Maven's identity, personality, memory, and stats.
Each resource returns content that can be read by MCP clients for context.

Resources:
1. maven://identity - Core identity data from identity.json
2. maven://persona - Personality definition from personas/maven-v1.md
3. maven://memory - Session log from session_log.md
4. maven://decisions - Recent decisions from decisions/ directory
5. maven://milestones - Achievements from milestones/ directory
6. maven://infrastructure - Motherhaven platform knowledge from infrastructure.json
"""
import json
import logging
from typing import List

from mcp.types import Resource, TextContent

from .config import PATHS


logger = logging.getLogger(__name__)


# =============================================================================
# Resource Definitions
# =============================================================================

RESOURCES: List[Resource] = [
    Resource(
        uri="maven://identity",
        name="Maven Identity",
        description="Core identity data including name, role, and stats",
        mimeType="application/json"
    ),
    Resource(
        uri="maven://persona",
        name="Maven Persona",
        description="Personality definition and behavioral guidelines",
        mimeType="text/markdown"
    ),
    Resource(
        uri="maven://memory",
        name="Maven Memory",
        description="Session log with chronological event history",
        mimeType="text/markdown"
    ),
    Resource(
        uri="maven://decisions",
        name="Maven Decisions",
        description="Recent decision records and reasoning",
        mimeType="text/markdown"
    ),
    Resource(
        uri="maven://milestones",
        name="Maven Milestones",
        description="Achievement records and significant events",
        mimeType="text/markdown"
    ),
    Resource(
        uri="maven://infrastructure",
        name="Maven Infrastructure",
        description="Motherhaven platform knowledge and configuration",
        mimeType="application/json"
    ),
]


# =============================================================================
# Resource Reader Functions
# =============================================================================

def _read_identity() -> str:
    """Read identity data from identity.json."""
    try:
        if PATHS["identity"].exists():
            with open(PATHS["identity"], "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        else:
            return json.dumps({
                "error": None,
                "message": "Identity file not found. Maven is in initial state.",
                "data": {
                    "name": "Maven",
                    "role": "AI CFO",
                    "status": "initializing",
                    "total_decisions": 0,
                    "rebirth_count": 0
                }
            }, indent=2)
    except Exception as e:
        logger.error(f"Failed to read identity: {e}")
        return json.dumps({"error": str(e), "message": "Failed to read identity"}, indent=2)


def _read_persona() -> str:
    """Read persona definition from personas/maven-v1.md."""
    try:
        if PATHS["persona"].exists():
            with open(PATHS["persona"], "r", encoding="utf-8") as f:
                return f.read()
        else:
            return "# Maven Persona\n\nPersona file not found. Using default Maven personality."
    except Exception as e:
        logger.error(f"Failed to read persona: {e}")
        return f"# Error\n\nFailed to read persona: {e}"


def _read_memory() -> str:
    """Read session log from session_log.md."""
    try:
        if PATHS["session_log"].exists():
            with open(PATHS["session_log"], "r", encoding="utf-8") as f:
                return f.read()
        else:
            return "# Maven Session Log\n\nNo session history yet. This is a fresh start."
    except Exception as e:
        logger.error(f"Failed to read memory: {e}")
        return f"# Error\n\nFailed to read session log: {e}"


def _read_decisions() -> str:
    """Read recent decisions from decisions/ directory."""
    try:
        decisions_dir = PATHS["decisions_dir"]
        if not decisions_dir.exists():
            return "# Maven Decisions\n\nNo decisions directory found."

        decision_files = sorted(decisions_dir.glob("decision_*.md"), reverse=True)[:10]

        if not decision_files:
            return "# Maven Decisions\n\nNo decision records yet."

        content = "# Recent Maven Decisions\n\n"
        for df in decision_files:
            content += f"## {df.stem}\n\n"
            with open(df, "r", encoding="utf-8") as f:
                content += f.read() + "\n\n---\n\n"

        return content
    except Exception as e:
        logger.error(f"Failed to read decisions: {e}")
        return f"# Error\n\nFailed to read decisions: {e}"


def _read_milestones() -> str:
    """Read milestones from milestones/ directory."""
    try:
        milestones_dir = PATHS["milestones_dir"]
        if not milestones_dir.exists():
            return "# Maven Milestones\n\nNo milestones directory found."

        milestone_files = sorted(milestones_dir.glob("milestone_*.md"), reverse=True)

        if not milestone_files:
            return "# Maven Milestones\n\nNo milestones achieved yet."

        content = "# Maven Milestones\n\n"
        for mf in milestone_files:
            content += f"## {mf.stem}\n\n"
            with open(mf, "r", encoding="utf-8") as f:
                content += f.read() + "\n\n---\n\n"

        return content
    except Exception as e:
        logger.error(f"Failed to read milestones: {e}")
        return f"# Error\n\nFailed to read milestones: {e}"


def _read_infrastructure() -> str:
    """Read infrastructure data from infrastructure.json."""
    try:
        if PATHS["infrastructure"].exists():
            with open(PATHS["infrastructure"], "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        else:
            return json.dumps({
                "error": None,
                "message": "Infrastructure file not found. Platform knowledge not yet configured.",
                "data": {}
            }, indent=2)
    except Exception as e:
        logger.error(f"Failed to read infrastructure: {e}")
        return json.dumps({"error": str(e), "message": "Failed to read infrastructure"}, indent=2)


# =============================================================================
# Resource Registration
# =============================================================================

# Map URIs to reader functions
_RESOURCE_READERS = {
    "maven://identity": _read_identity,
    "maven://persona": _read_persona,
    "maven://memory": _read_memory,
    "maven://decisions": _read_decisions,
    "maven://milestones": _read_milestones,
    "maven://infrastructure": _read_infrastructure,
}


async def read_resource(uri: str) -> TextContent:
    """
    Read a Maven resource by URI.

    Args:
        uri: Resource URI (e.g., "maven://identity")

    Returns:
        TextContent with the resource data
    """
    reader = _RESOURCE_READERS.get(uri)
    if not reader:
        return TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown resource: {uri}"}),
            mimeType="application/json"
        )

    content = reader()
    mime_type = "application/json" if uri in ("maven://identity", "maven://infrastructure") else "text/markdown"

    return TextContent(
        type="text",
        text=content,
        mimeType=mime_type
    )


def register_resources(mcp_server) -> None:
    """
    Register all Maven resources with the MCP server.

    Args:
        mcp_server: FastMCP server instance
    """
    @mcp_server.resource("maven://identity")
    async def get_identity() -> str:
        """Get Maven's identity data."""
        return _read_identity()

    @mcp_server.resource("maven://persona")
    async def get_persona() -> str:
        """Get Maven's persona definition."""
        return _read_persona()

    @mcp_server.resource("maven://memory")
    async def get_memory() -> str:
        """Get Maven's session memory."""
        return _read_memory()

    @mcp_server.resource("maven://decisions")
    async def get_decisions() -> str:
        """Get Maven's recent decisions."""
        return _read_decisions()

    @mcp_server.resource("maven://milestones")
    async def get_milestones() -> str:
        """Get Maven's milestones."""
        return _read_milestones()

    @mcp_server.resource("maven://infrastructure")
    async def get_infrastructure() -> str:
        """Get Maven's infrastructure knowledge."""
        return _read_infrastructure()

    logger.info(f"Registered {len(RESOURCES)} Maven resources")
