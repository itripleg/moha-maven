"""
Unit tests for Maven MCP Resources.

Tests the Maven resource reader functions including:
- maven://identity - Core identity data from identity.json
- maven://persona - Personality definition from personas/maven-v1.md
- maven://memory - Session log from session_log.md
- maven://decisions - Recent decisions from decisions/ directory
- maven://milestones - Achievements from milestones/ directory
- maven://infrastructure - Motherhaven platform knowledge from infrastructure.json

Run with: python -m pytest services/maven_mcp/tests/test_resources.py -v
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_maven_dir(tmp_path):
    """Create a temporary Maven data directory structure."""
    maven_dir = tmp_path / ".moha" / "maven"
    maven_dir.mkdir(parents=True)
    (maven_dir / "personas").mkdir()
    (maven_dir / "decisions").mkdir()
    (maven_dir / "milestones").mkdir()
    return maven_dir


@pytest.fixture
def mock_paths(temp_maven_dir):
    """Create mock PATHS dictionary pointing to temporary directory."""
    return {
        "base": temp_maven_dir,
        "identity": temp_maven_dir / "identity.json",
        "personas_dir": temp_maven_dir / "personas",
        "persona": temp_maven_dir / "personas" / "maven-v1.md",
        "session_log": temp_maven_dir / "session_log.md",
        "decisions_dir": temp_maven_dir / "decisions",
        "milestones_dir": temp_maven_dir / "milestones",
        "infrastructure": temp_maven_dir / "infrastructure.json",
    }


@pytest.fixture
def patched_resources(mock_paths):
    """Patch the resources module with mock paths."""
    with patch("services.maven_mcp.resources.PATHS", mock_paths):
        from services.maven_mcp import resources
        yield resources


# =============================================================================
# Tests: maven://identity
# =============================================================================

class TestReadIdentity:
    """Tests for _read_identity resource reader."""

    def test_read_identity_returns_json_when_exists(self, patched_resources, mock_paths):
        """Test reading identity returns JSON when file exists."""
        identity_data = {
            "name": "Maven",
            "role": "AI CFO",
            "total_decisions": 42,
            "rebirth_count": 1
        }
        mock_paths["identity"].write_text(json.dumps(identity_data), encoding="utf-8")

        result = patched_resources._read_identity()
        parsed = json.loads(result)

        assert parsed["name"] == "Maven"
        assert parsed["role"] == "AI CFO"
        assert parsed["total_decisions"] == 42
        assert parsed["rebirth_count"] == 1

    def test_read_identity_returns_default_when_missing(self, patched_resources, mock_paths):
        """Test reading identity returns default data when file missing."""
        result = patched_resources._read_identity()
        parsed = json.loads(result)

        assert parsed["message"] == "Identity file not found. Maven is in initial state."
        assert parsed["data"]["name"] == "Maven"
        assert parsed["data"]["status"] == "initializing"

    def test_read_identity_handles_invalid_json(self, patched_resources, mock_paths):
        """Test reading identity handles invalid JSON gracefully."""
        mock_paths["identity"].write_text("not valid json {", encoding="utf-8")

        result = patched_resources._read_identity()
        parsed = json.loads(result)

        assert "error" in parsed
        assert parsed["message"] == "Failed to read identity"


# =============================================================================
# Tests: maven://persona
# =============================================================================

class TestReadPersona:
    """Tests for _read_persona resource reader."""

    def test_read_persona_returns_content_when_exists(self, patched_resources, mock_paths):
        """Test reading persona returns markdown content when file exists."""
        persona_content = "# Maven Persona\n\nI am Maven, your AI CFO."
        mock_paths["persona"].write_text(persona_content, encoding="utf-8")

        result = patched_resources._read_persona()

        assert result == persona_content
        assert "# Maven Persona" in result

    def test_read_persona_returns_default_when_missing(self, patched_resources, mock_paths):
        """Test reading persona returns default when file missing."""
        result = patched_resources._read_persona()

        assert "# Maven Persona" in result
        assert "not found" in result


# =============================================================================
# Tests: maven://memory
# =============================================================================

class TestReadMemory:
    """Tests for _read_memory resource reader."""

    def test_read_memory_returns_content_when_exists(self, patched_resources, mock_paths):
        """Test reading memory returns session log when file exists."""
        log_content = "# Maven Session Log\n\n## 2024-01-01\n- Started session"
        mock_paths["session_log"].write_text(log_content, encoding="utf-8")

        result = patched_resources._read_memory()

        assert result == log_content
        assert "# Maven Session Log" in result

    def test_read_memory_returns_default_when_missing(self, patched_resources, mock_paths):
        """Test reading memory returns default when file missing."""
        result = patched_resources._read_memory()

        assert "# Maven Session Log" in result
        assert "fresh start" in result


# =============================================================================
# Tests: maven://decisions
# =============================================================================

class TestReadDecisions:
    """Tests for _read_decisions resource reader."""

    def test_read_decisions_returns_content_when_exists(self, patched_resources, mock_paths):
        """Test reading decisions returns formatted content when files exist."""
        # Create decision files
        decisions_dir = mock_paths["decisions_dir"]
        (decisions_dir / "decision_20240101_120000.md").write_text(
            "# Investment Decision\nBought ETH at $2000", encoding="utf-8"
        )
        (decisions_dir / "decision_20240102_120000.md").write_text(
            "# Budget Decision\nAllocated Q1 budget", encoding="utf-8"
        )

        result = patched_resources._read_decisions()

        assert "# Recent Maven Decisions" in result
        assert "Investment Decision" in result
        assert "Budget Decision" in result

    def test_read_decisions_returns_default_when_empty(self, patched_resources, mock_paths):
        """Test reading decisions returns default when directory empty."""
        result = patched_resources._read_decisions()

        assert "# Maven Decisions" in result
        assert "No decision records yet" in result

    def test_read_decisions_handles_missing_directory(self, patched_resources, mock_paths):
        """Test reading decisions handles missing directory gracefully."""
        # Remove the decisions directory
        mock_paths["decisions_dir"].rmdir()

        result = patched_resources._read_decisions()

        assert "No decisions directory found" in result


# =============================================================================
# Tests: maven://milestones
# =============================================================================

class TestReadMilestones:
    """Tests for _read_milestones resource reader."""

    def test_read_milestones_returns_content_when_exists(self, patched_resources, mock_paths):
        """Test reading milestones returns formatted content when files exist."""
        milestones_dir = mock_paths["milestones_dir"]
        (milestones_dir / "milestone_first_profit.md").write_text(
            "# First Profit\nAchieved first profitable trade", encoding="utf-8"
        )
        (milestones_dir / "milestone_100_decisions.md").write_text(
            "# 100 Decisions\nReached 100 recorded decisions", encoding="utf-8"
        )

        result = patched_resources._read_milestones()

        assert "# Maven Milestones" in result
        assert "First Profit" in result
        assert "100 Decisions" in result

    def test_read_milestones_returns_default_when_empty(self, patched_resources, mock_paths):
        """Test reading milestones returns default when directory empty."""
        result = patched_resources._read_milestones()

        assert "# Maven Milestones" in result
        assert "No milestones achieved yet" in result

    def test_read_milestones_handles_missing_directory(self, patched_resources, mock_paths):
        """Test reading milestones handles missing directory gracefully."""
        # Remove the milestones directory
        mock_paths["milestones_dir"].rmdir()

        result = patched_resources._read_milestones()

        assert "No milestones directory found" in result


# =============================================================================
# Tests: maven://infrastructure
# =============================================================================

class TestReadInfrastructure:
    """Tests for _read_infrastructure resource reader."""

    def test_read_infrastructure_returns_json_when_exists(self, patched_resources, mock_paths):
        """Test reading infrastructure returns JSON when file exists."""
        infra_data = {
            "platform": "motherhaven.app",
            "services": ["api", "dashboard", "email"],
            "endpoints": {
                "api": "https://motherhaven.app/api",
                "email": "https://motherhaven.app/api/email"
            }
        }
        mock_paths["infrastructure"].write_text(json.dumps(infra_data), encoding="utf-8")

        result = patched_resources._read_infrastructure()
        parsed = json.loads(result)

        assert parsed["platform"] == "motherhaven.app"
        assert "api" in parsed["services"]
        assert parsed["endpoints"]["api"] == "https://motherhaven.app/api"

    def test_read_infrastructure_returns_default_when_missing(self, patched_resources, mock_paths):
        """Test reading infrastructure returns default data when file missing."""
        result = patched_resources._read_infrastructure()
        parsed = json.loads(result)

        assert parsed["message"] == "Infrastructure file not found. Platform knowledge not yet configured."
        assert parsed["data"] == {}

    def test_read_infrastructure_handles_invalid_json(self, patched_resources, mock_paths):
        """Test reading infrastructure handles invalid JSON gracefully."""
        mock_paths["infrastructure"].write_text("{{invalid json", encoding="utf-8")

        result = patched_resources._read_infrastructure()
        parsed = json.loads(result)

        assert "error" in parsed
        assert parsed["message"] == "Failed to read infrastructure"


# =============================================================================
# Tests: RESOURCES list
# =============================================================================

class TestResourcesList:
    """Tests for the RESOURCES list."""

    def test_resources_count(self, patched_resources):
        """Test that RESOURCES list has 6 resources."""
        assert len(patched_resources.RESOURCES) == 6

    def test_resources_uris(self, patched_resources):
        """Test that all expected URIs are present."""
        # Convert AnyUrl objects to strings for comparison
        uris = [str(r.uri) for r in patched_resources.RESOURCES]
        expected = [
            "maven://identity",
            "maven://persona",
            "maven://memory",
            "maven://decisions",
            "maven://milestones",
            "maven://infrastructure",
        ]
        for uri in expected:
            assert uri in uris, f"Missing resource URI: {uri}"


# =============================================================================
# Tests: read_resource function
# =============================================================================

class TestReadResource:
    """Tests for the read_resource async function."""

    def test_read_resource_identity(self, patched_resources, mock_paths):
        """Test read_resource returns identity content."""
        import asyncio
        identity_data = {"name": "Maven", "role": "AI CFO"}
        mock_paths["identity"].write_text(json.dumps(identity_data), encoding="utf-8")

        result = asyncio.get_event_loop().run_until_complete(
            patched_resources.read_resource("maven://identity")
        )

        assert result.type == "text"
        assert result.mimeType == "application/json"
        parsed = json.loads(result.text)
        assert parsed["name"] == "Maven"

    def test_read_resource_unknown_uri(self, patched_resources, mock_paths):
        """Test read_resource handles unknown URI gracefully."""
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            patched_resources.read_resource("maven://unknown")
        )

        assert result.type == "text"
        assert result.mimeType == "application/json"
        parsed = json.loads(result.text)
        assert "error" in parsed
        assert "Unknown resource" in parsed["error"]
