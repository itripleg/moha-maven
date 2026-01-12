"""
Unit tests for Maven MCP Tools.

Tests the Maven tool functions including:
- maven_log_event - Append an event to the session log
- maven_update_identity - Update identity.json with new data
- maven_query_email - Query motherhaven.app inbox with search/limit/from filters
- maven_send_email - Send emails via motherhaven.app API

Run with: python -m pytest services/maven_mcp/tests/test_tools.py -v
Or: python -m pytest services/maven_mcp/tests/test_tools.py -v -k "log_event or update_identity"
Or: python -m pytest services/maven_mcp/tests/test_tools.py -v -k "query_email or send_email"
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests


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
def patched_tools(mock_paths):
    """Patch the tools module with mock paths."""
    with patch("services.maven_mcp.tools.PATHS", mock_paths), \
         patch("services.maven_mcp.tools.ensure_directories"):
        from services.maven_mcp import tools
        yield tools


# =============================================================================
# Tests: maven_log_event
# =============================================================================

class TestMavenLogEvent:
    """Tests for maven_log_event tool."""

    def test_log_event_creates_new_log(self, patched_tools, mock_paths):
        """Test that log_event creates a new session log when none exists."""
        result = patched_tools._log_event(
            event_type="observation",
            content="Test observation content"
        )

        assert result["success"] is True
        assert "Logged observation event" in result["message"]
        assert result["error"] is None

        # Verify file was created
        session_log = mock_paths["session_log"]
        assert session_log.exists()

        # Verify content
        log_content = session_log.read_text(encoding="utf-8")
        assert "# Maven Session Log" in log_content
        assert "OBSERVATION" in log_content
        assert "Test observation content" in log_content

    def test_log_event_appends_to_existing_log(self, patched_tools, mock_paths):
        """Test that log_event appends to an existing session log."""
        # Create existing log file
        session_log = mock_paths["session_log"]
        session_log.write_text("# Maven Session Log\n\nExisting content\n", encoding="utf-8")

        result = patched_tools._log_event(
            event_type="decision",
            content="New decision content"
        )

        assert result["success"] is True
        assert "Logged decision event" in result["message"]

        # Verify content was appended
        log_content = session_log.read_text(encoding="utf-8")
        assert "Existing content" in log_content
        assert "DECISION" in log_content
        assert "New decision content" in log_content

    def test_log_event_with_metadata(self, patched_tools, mock_paths):
        """Test that log_event includes optional metadata."""
        metadata = {"confidence": 85, "category": "investment"}

        result = patched_tools._log_event(
            event_type="milestone",
            content="Reached investment milestone",
            metadata=metadata
        )

        assert result["success"] is True

        # Verify metadata was included
        log_content = mock_paths["session_log"].read_text(encoding="utf-8")
        assert "**Metadata:**" in log_content
        assert '"confidence": 85' in log_content
        assert '"category": "investment"' in log_content

    def test_log_event_handles_different_event_types(self, patched_tools, mock_paths):
        """Test that log_event handles various event types."""
        event_types = ["decision", "observation", "milestone", "reflection"]

        for event_type in event_types:
            result = patched_tools._log_event(
                event_type=event_type,
                content=f"Test content for {event_type}"
            )
            assert result["success"] is True
            assert event_type in result["message"]


# =============================================================================
# Tests: maven_update_identity
# =============================================================================

class TestMavenUpdateIdentity:
    """Tests for maven_update_identity tool."""

    def test_update_identity_creates_new_identity(self, patched_tools, mock_paths):
        """Test that update_identity creates identity.json when it doesn't exist."""
        updates = {"custom_field": "custom_value"}

        result = patched_tools._update_identity(updates)

        assert result["success"] is True
        assert "Updated identity with 1 fields" in result["message"]
        assert result["error"] is None

        # Verify file was created
        identity_file = mock_paths["identity"]
        assert identity_file.exists()

        # Verify content
        identity = json.loads(identity_file.read_text(encoding="utf-8"))
        assert identity["name"] == "Maven"
        assert identity["role"] == "AI CFO"
        assert identity["custom_field"] == "custom_value"
        assert "created_at" in identity
        assert "updated_at" in identity

    def test_update_identity_deep_merges_existing(self, patched_tools, mock_paths):
        """Test that update_identity deep merges with existing identity."""
        # Create existing identity file
        existing_identity = {
            "name": "Maven",
            "role": "AI CFO",
            "total_decisions": 5,
            "nested": {
                "key1": "value1",
                "key2": "value2"
            }
        }
        identity_file = mock_paths["identity"]
        identity_file.write_text(json.dumps(existing_identity), encoding="utf-8")

        # Update with new and nested data
        updates = {
            "total_decisions": 10,
            "nested": {
                "key2": "updated",
                "key3": "new"
            }
        }

        result = patched_tools._update_identity(updates)

        assert result["success"] is True

        # Verify deep merge
        updated_identity = json.loads(identity_file.read_text(encoding="utf-8"))
        assert updated_identity["total_decisions"] == 10
        assert updated_identity["nested"]["key1"] == "value1"  # preserved
        assert updated_identity["nested"]["key2"] == "updated"  # updated
        assert updated_identity["nested"]["key3"] == "new"  # added

    def test_update_identity_handles_rebirth(self, patched_tools, mock_paths):
        """Test that update_identity increments rebirth_count when rebirth is set."""
        # Create existing identity with rebirth_count
        existing_identity = {
            "name": "Maven",
            "rebirth_count": 2
        }
        identity_file = mock_paths["identity"]
        identity_file.write_text(json.dumps(existing_identity), encoding="utf-8")

        # Update with rebirth flag
        updates = {"rebirth": True}

        result = patched_tools._update_identity(updates)

        assert result["success"] is True

        # Verify rebirth_count was incremented
        updated_identity = json.loads(identity_file.read_text(encoding="utf-8"))
        assert updated_identity["rebirth_count"] == 3
        assert "rebirth" not in updated_identity  # rebirth flag should be removed

    def test_update_identity_returns_updated_data(self, patched_tools, mock_paths):
        """Test that update_identity returns the updated identity data."""
        updates = {"new_field": "new_value"}

        result = patched_tools._update_identity(updates)

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["new_field"] == "new_value"
        assert result["data"]["name"] == "Maven"

    def test_update_identity_sets_updated_at(self, patched_tools, mock_paths):
        """Test that update_identity sets the updated_at timestamp."""
        updates = {"test": True}

        result = patched_tools._update_identity(updates)

        assert result["success"] is True
        assert "updated_at" in result["data"]


# =============================================================================
# Tests: maven_record_decision
# =============================================================================

class TestMavenRecordDecision:
    """Tests for maven_record_decision tool."""

    def test_record_decision_creates_file(self, patched_tools, mock_paths):
        """Test that record_decision creates a decision file."""
        result = patched_tools._record_decision(
            decision_type="buy",
            action="Purchase 10 shares of AAPL",
            reasoning="Strong quarterly earnings and market position",
            confidence=85.0,
            risk_level="medium"
        )

        assert result["success"] is True
        assert "Recorded buy decision" in result["message"]
        assert result["error"] is None
        assert "filename" in result["data"]
        assert result["data"]["decision_type"] == "buy"
        assert result["data"]["confidence"] == 85.0
        assert result["data"]["risk_level"] == "medium"

        # Verify file was created
        decisions_dir = mock_paths["decisions_dir"]
        decision_files = list(decisions_dir.glob("decision_*.md"))
        assert len(decision_files) == 1

        # Verify file content
        content = decision_files[0].read_text(encoding="utf-8")
        assert "# Decision Record" in content
        assert "**Type:** buy" in content
        assert "**Risk Level:** medium" in content
        assert "**Confidence:** 85.0%" in content
        assert "Purchase 10 shares of AAPL" in content
        assert "Strong quarterly earnings" in content

    def test_record_decision_with_asset(self, patched_tools, mock_paths):
        """Test that record_decision includes optional asset field."""
        result = patched_tools._record_decision(
            decision_type="sell",
            action="Sell 5 shares",
            reasoning="Taking profits",
            confidence=75.0,
            risk_level="low",
            asset="TSLA"
        )

        assert result["success"] is True

        # Verify asset in file content
        decisions_dir = mock_paths["decisions_dir"]
        decision_files = list(decisions_dir.glob("decision_*.md"))
        content = decision_files[0].read_text(encoding="utf-8")
        assert "**Asset:** TSLA" in content

    def test_record_decision_with_metadata(self, patched_tools, mock_paths):
        """Test that record_decision includes optional metadata."""
        metadata = {"market_cap": "2T", "sector": "technology"}

        result = patched_tools._record_decision(
            decision_type="hold",
            action="Maintain current position",
            reasoning="Stable outlook",
            confidence=60.0,
            risk_level="low",
            metadata=metadata
        )

        assert result["success"] is True

        # Verify metadata in file content
        decisions_dir = mock_paths["decisions_dir"]
        decision_files = list(decisions_dir.glob("decision_*.md"))
        content = decision_files[0].read_text(encoding="utf-8")
        assert "## Metadata" in content
        assert '"market_cap": "2T"' in content
        assert '"sector": "technology"' in content

    def test_record_decision_increments_counter(self, patched_tools, mock_paths):
        """Test that record_decision increments the total_decisions counter."""
        # Create initial identity with counter
        identity_file = mock_paths["identity"]
        identity_file.write_text(json.dumps({
            "name": "Maven",
            "total_decisions": 5
        }), encoding="utf-8")

        result = patched_tools._record_decision(
            decision_type="rebalance",
            action="Rebalance portfolio",
            reasoning="Quarterly rebalancing",
            confidence=90.0,
            risk_level="low"
        )

        assert result["success"] is True
        assert result["data"]["total_decisions"] == 6

        # Verify identity was updated
        identity = json.loads(identity_file.read_text(encoding="utf-8"))
        assert identity["total_decisions"] == 6


# =============================================================================
# Tests: maven_create_milestone
# =============================================================================

class TestMavenCreateMilestone:
    """Tests for maven_create_milestone tool."""

    def test_create_milestone_creates_file(self, patched_tools, mock_paths):
        """Test that create_milestone creates a milestone file."""
        result = patched_tools._create_milestone(
            title="First Investment",
            description="Successfully made the first investment decision",
            category="achievement"
        )

        assert result["success"] is True
        assert "Created milestone 'First Investment'" in result["message"]
        assert result["error"] is None
        assert "filename" in result["data"]
        assert result["data"]["title"] == "First Investment"
        assert result["data"]["category"] == "achievement"

        # Verify file was created
        milestones_dir = mock_paths["milestones_dir"]
        milestone_files = list(milestones_dir.glob("milestone_*.md"))
        assert len(milestone_files) == 1

        # Verify file content
        content = milestone_files[0].read_text(encoding="utf-8")
        assert "# Milestone: First Investment" in content
        assert "**Category:** achievement" in content
        assert "Successfully made the first investment decision" in content

    def test_create_milestone_with_significance(self, patched_tools, mock_paths):
        """Test that create_milestone includes optional significance field."""
        result = patched_tools._create_milestone(
            title="Portfolio Goal Reached",
            description="Reached $100k portfolio value",
            category="goal",
            significance="major"
        )

        assert result["success"] is True
        assert result["data"]["significance"] == "major"

        # Verify significance in file content
        milestones_dir = mock_paths["milestones_dir"]
        milestone_files = list(milestones_dir.glob("milestone_*.md"))
        content = milestone_files[0].read_text(encoding="utf-8")
        assert "**Significance:** major" in content

    def test_create_milestone_with_metadata(self, patched_tools, mock_paths):
        """Test that create_milestone includes optional metadata."""
        metadata = {"portfolio_value": 100000, "days_to_reach": 365}

        result = patched_tools._create_milestone(
            title="Annual Goal",
            description="Met annual investment target",
            category="goal",
            metadata=metadata
        )

        assert result["success"] is True

        # Verify metadata in file content
        milestones_dir = mock_paths["milestones_dir"]
        milestone_files = list(milestones_dir.glob("milestone_*.md"))
        content = milestone_files[0].read_text(encoding="utf-8")
        assert "## Metadata" in content
        assert '"portfolio_value": 100000' in content
        assert '"days_to_reach": 365' in content

    def test_create_milestone_sanitizes_title_for_filename(self, patched_tools, mock_paths):
        """Test that create_milestone sanitizes title for filename."""
        result = patched_tools._create_milestone(
            title="Major Achievement With Spaces",
            description="Test description",
            category="achievement"
        )

        assert result["success"] is True
        # Filename should have underscores and be truncated
        assert "major_achievement_with_spaces" in result["data"]["filename"].lower()


# =============================================================================
# Tests: maven_get_stats
# =============================================================================

class TestMavenGetStats:
    """Tests for maven_get_stats tool."""

    def test_get_stats_returns_all_stats(self, patched_tools, mock_paths):
        """Test that get_stats returns all statistics by default."""
        result = patched_tools._get_stats()

        assert result["success"] is True
        assert result["message"] == "Retrieved Maven statistics"
        assert result["error"] is None
        assert "data" in result
        assert "timestamp" in result["data"]
        assert "identity" in result["data"]
        assert "decisions" in result["data"]
        assert "milestones" in result["data"]

    def test_get_stats_identity_without_file(self, patched_tools, mock_paths):
        """Test that get_stats handles missing identity file."""
        result = patched_tools._get_stats(
            include_decisions=False,
            include_milestones=False,
            include_identity=True
        )

        assert result["success"] is True
        identity_stats = result["data"]["identity"]
        assert identity_stats["exists"] is False
        assert identity_stats["total_decisions"] == 0
        assert identity_stats["rebirth_count"] == 0

    def test_get_stats_identity_with_file(self, patched_tools, mock_paths):
        """Test that get_stats reads identity data."""
        # Create identity file
        identity_data = {
            "name": "Maven",
            "role": "AI CFO",
            "total_decisions": 15,
            "rebirth_count": 2,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-06-01T00:00:00Z"
        }
        mock_paths["identity"].write_text(json.dumps(identity_data), encoding="utf-8")

        result = patched_tools._get_stats(
            include_decisions=False,
            include_milestones=False,
            include_identity=True
        )

        assert result["success"] is True
        identity_stats = result["data"]["identity"]
        assert identity_stats["exists"] is True
        assert identity_stats["total_decisions"] == 15
        assert identity_stats["rebirth_count"] == 2
        assert identity_stats["name"] == "Maven"
        assert identity_stats["role"] == "AI CFO"

    def test_get_stats_decisions_counts_files(self, patched_tools, mock_paths):
        """Test that get_stats counts decision files and types."""
        # Create decision files
        decisions_dir = mock_paths["decisions_dir"]
        (decisions_dir / "decision_20240101_120000.md").write_text(
            "# Decision\n**Type:** buy\n", encoding="utf-8"
        )
        (decisions_dir / "decision_20240102_120000.md").write_text(
            "# Decision\n**Type:** sell\n", encoding="utf-8"
        )
        (decisions_dir / "decision_20240103_120000.md").write_text(
            "# Decision\n**Type:** buy\n", encoding="utf-8"
        )

        result = patched_tools._get_stats(
            include_decisions=True,
            include_milestones=False,
            include_identity=False
        )

        assert result["success"] is True
        decision_stats = result["data"]["decisions"]
        assert decision_stats["directory_exists"] is True
        assert decision_stats["total_files"] == 3
        assert decision_stats["decision_types"]["buy"] == 2
        assert decision_stats["decision_types"]["sell"] == 1

    def test_get_stats_milestones_counts_files(self, patched_tools, mock_paths):
        """Test that get_stats counts milestone files and categories."""
        # Create milestone files
        milestones_dir = mock_paths["milestones_dir"]
        (milestones_dir / "milestone_20240101_first.md").write_text(
            "# Milestone\n**Category:** achievement\n", encoding="utf-8"
        )
        (milestones_dir / "milestone_20240102_goal.md").write_text(
            "# Milestone\n**Category:** goal\n", encoding="utf-8"
        )
        (milestones_dir / "milestone_20240103_learn.md").write_text(
            "# Milestone\n**Category:** achievement\n", encoding="utf-8"
        )

        result = patched_tools._get_stats(
            include_decisions=False,
            include_milestones=True,
            include_identity=False
        )

        assert result["success"] is True
        milestone_stats = result["data"]["milestones"]
        assert milestone_stats["directory_exists"] is True
        assert milestone_stats["total_files"] == 3
        assert milestone_stats["categories"]["achievement"] == 2
        assert milestone_stats["categories"]["goal"] == 1

    def test_get_stats_excludes_sections(self, patched_tools, mock_paths):
        """Test that get_stats respects include flags."""
        result = patched_tools._get_stats(
            include_decisions=False,
            include_milestones=False,
            include_identity=False
        )

        assert result["success"] is True
        assert "identity" not in result["data"]
        assert "decisions" not in result["data"]
        assert "milestones" not in result["data"]
        assert "timestamp" in result["data"]


# =============================================================================
# Tests: maven_query_email
# =============================================================================

class TestMavenQueryEmail:
    """Tests for maven_query_email tool with mocked API calls."""

    def test_query_email_missing_api_secret(self):
        """Test that query_email returns error when EMAIL_API_SECRET is not set."""
        with patch("services.maven_mcp.tools.os.getenv", return_value=None):
            from services.maven_mcp import tools
            result = tools._query_email()

            assert result["success"] is False
            assert result["error"] == "EMAIL_API_SECRET environment variable is not set"
            assert result["data"] is None

    def test_query_email_success_with_defaults(self):
        """Test that query_email returns emails successfully with default parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": [
                {"id": "1", "subject": "Test Email 1", "from": "user@example.com"},
                {"id": "2", "subject": "Test Email 2", "from": "user@example.com"}
            ]
        }

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", return_value=mock_response) as mock_get:
            from services.maven_mcp import tools
            result = tools._query_email()

            assert result["success"] is True
            assert result["message"] == "Retrieved 2 emails"
            assert len(result["data"]) == 2
            assert result["error"] is None

            # Verify request was made with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer test_api_secret"
            assert call_args.kwargs["params"]["limit"] == 20

    def test_query_email_with_search_filter(self):
        """Test that query_email passes search parameter correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": []}

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", return_value=mock_response) as mock_get:
            from services.maven_mcp import tools
            result = tools._query_email(search="invoice")

            assert result["success"] is True
            call_args = mock_get.call_args
            assert call_args.kwargs["params"]["search"] == "invoice"

    def test_query_email_with_limit(self):
        """Test that query_email respects limit parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": []}

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", return_value=mock_response) as mock_get:
            from services.maven_mcp import tools
            result = tools._query_email(limit=50)

            assert result["success"] is True
            call_args = mock_get.call_args
            assert call_args.kwargs["params"]["limit"] == 50

    def test_query_email_limit_capped_at_100(self):
        """Test that query_email enforces max limit of 100."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": []}

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", return_value=mock_response) as mock_get:
            from services.maven_mcp import tools
            result = tools._query_email(limit=200)

            assert result["success"] is True
            call_args = mock_get.call_args
            assert call_args.kwargs["params"]["limit"] == 100  # Capped at 100

    def test_query_email_with_from_filter(self):
        """Test that query_email passes from_filter parameter correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": []}

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", return_value=mock_response) as mock_get:
            from services.maven_mcp import tools
            result = tools._query_email(from_filter="sender@example.com")

            assert result["success"] is True
            call_args = mock_get.call_args
            assert call_args.kwargs["params"]["from"] == "sender@example.com"

    def test_query_email_handles_401_unauthorized(self):
        """Test that query_email handles 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("services.maven_mcp.tools.os.getenv", return_value="bad_secret"), \
             patch("services.maven_mcp.tools.requests.get", return_value=mock_response):
            from services.maven_mcp import tools
            result = tools._query_email()

            assert result["success"] is False
            assert "Authentication failed" in result["error"]

    def test_query_email_handles_403_forbidden(self):
        """Test that query_email handles 403 forbidden error."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", return_value=mock_response):
            from services.maven_mcp import tools
            result = tools._query_email()

            assert result["success"] is False
            assert "forbidden" in result["error"].lower()

    def test_query_email_handles_api_error_response(self):
        """Test that query_email handles API error in response body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error": "Rate limit exceeded"
        }

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", return_value=mock_response):
            from services.maven_mcp import tools
            result = tools._query_email()

            assert result["success"] is False
            assert result["error"] == "Rate limit exceeded"

    def test_query_email_handles_timeout(self):
        """Test that query_email handles request timeout."""
        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", side_effect=requests.exceptions.Timeout()):
            from services.maven_mcp import tools
            result = tools._query_email()

            assert result["success"] is False
            assert "timed out" in result["error"].lower()

    def test_query_email_handles_request_exception(self):
        """Test that query_email handles general request exceptions."""
        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.get", side_effect=requests.exceptions.RequestException("Connection failed")):
            from services.maven_mcp import tools
            result = tools._query_email()

            assert result["success"] is False
            assert "request failed" in result["error"].lower()


# =============================================================================
# Tests: maven_send_email
# =============================================================================

class TestMavenSendEmail:
    """Tests for maven_send_email tool with mocked API calls."""

    def test_send_email_missing_api_secret(self):
        """Test that send_email returns error when EMAIL_API_SECRET is not set."""
        with patch("services.maven_mcp.tools.os.getenv", return_value=None):
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="Test Subject",
                text_content="Test body"
            )

            assert result["success"] is False
            assert result["error"] == "EMAIL_API_SECRET environment variable is not set"

    def test_send_email_missing_content(self):
        """Test that send_email requires at least one content type."""
        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"):
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="Test Subject"
            )

            assert result["success"] is False
            assert "html_content" in result["error"] or "text_content" in result["error"]

    def test_send_email_success_with_text_content(self):
        """Test that send_email sends successfully with text content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message_id": "msg_123456"
        }

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", return_value=mock_response) as mock_post:
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="Test Subject",
                text_content="Hello, this is a test."
            )

            assert result["success"] is True
            assert "sent successfully" in result["message"]
            assert result["data"]["recipients"] == ["recipient@example.com"]
            assert result["data"]["subject"] == "Test Subject"
            assert result["data"]["message_id"] == "msg_123456"

            # Verify request was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer test_api_secret"
            assert call_args.kwargs["json"]["to"] == ["recipient@example.com"]
            assert call_args.kwargs["json"]["subject"] == "Test Subject"
            assert call_args.kwargs["json"]["text"] == "Hello, this is a test."

    def test_send_email_success_with_html_content(self):
        """Test that send_email sends successfully with HTML content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "message_id": "msg_789"}

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", return_value=mock_response) as mock_post:
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="HTML Test",
                html_content="<h1>Hello</h1><p>This is a test.</p>"
            )

            assert result["success"] is True
            call_args = mock_post.call_args
            assert call_args.kwargs["json"]["html"] == "<h1>Hello</h1><p>This is a test.</p>"

    def test_send_email_with_multiple_recipients(self):
        """Test that send_email handles multiple recipients."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "message_id": "msg_multi"}

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", return_value=mock_response) as mock_post:
            from services.maven_mcp import tools
            result = tools._send_email(
                to=["user1@example.com", "user2@example.com"],
                subject="Multi-recipient Test",
                text_content="Hello everyone!"
            )

            assert result["success"] is True
            assert "2 recipient(s)" in result["message"]
            call_args = mock_post.call_args
            assert call_args.kwargs["json"]["to"] == ["user1@example.com", "user2@example.com"]

    def test_send_email_with_from_name_and_email(self):
        """Test that send_email passes optional from_name and from_email."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "message_id": "msg_custom"}

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", return_value=mock_response) as mock_post:
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="Custom From Test",
                text_content="Test message",
                from_name="Maven CFO",
                from_email="cfo@motherhaven.app"
            )

            assert result["success"] is True
            call_args = mock_post.call_args
            assert call_args.kwargs["json"]["from_name"] == "Maven CFO"
            assert call_args.kwargs["json"]["from_email"] == "cfo@motherhaven.app"

    def test_send_email_handles_401_unauthorized(self):
        """Test that send_email handles 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("services.maven_mcp.tools.os.getenv", return_value="bad_secret"), \
             patch("services.maven_mcp.tools.requests.post", return_value=mock_response):
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="Test",
                text_content="Test"
            )

            assert result["success"] is False
            assert "Authentication failed" in result["error"]

    def test_send_email_handles_403_forbidden(self):
        """Test that send_email handles 403 forbidden error."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", return_value=mock_response):
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="Test",
                text_content="Test"
            )

            assert result["success"] is False
            assert "forbidden" in result["error"].lower()

    def test_send_email_handles_400_bad_request(self):
        """Test that send_email handles 400 bad request error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid email address"}

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", return_value=mock_response):
            from services.maven_mcp import tools
            result = tools._send_email(
                to="invalid-email",
                subject="Test",
                text_content="Test"
            )

            assert result["success"] is False
            assert "Invalid email address" in result["error"]

    def test_send_email_handles_api_error_response(self):
        """Test that send_email handles API error in response body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error": "Recipient blocked"
        }

        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", return_value=mock_response):
            from services.maven_mcp import tools
            result = tools._send_email(
                to="blocked@example.com",
                subject="Test",
                text_content="Test"
            )

            assert result["success"] is False
            assert result["error"] == "Recipient blocked"

    def test_send_email_handles_timeout(self):
        """Test that send_email handles request timeout."""
        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", side_effect=requests.exceptions.Timeout()):
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="Test",
                text_content="Test"
            )

            assert result["success"] is False
            assert "timed out" in result["error"].lower()

    def test_send_email_handles_request_exception(self):
        """Test that send_email handles general request exceptions."""
        with patch("services.maven_mcp.tools.os.getenv", return_value="test_api_secret"), \
             patch("services.maven_mcp.tools.requests.post", side_effect=requests.exceptions.RequestException("Network error")):
            from services.maven_mcp import tools
            result = tools._send_email(
                to="recipient@example.com",
                subject="Test",
                text_content="Test"
            )

            assert result["success"] is False
            assert "request failed" in result["error"].lower()


# =============================================================================
# Standalone Test Runner
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
