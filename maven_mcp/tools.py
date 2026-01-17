"""
Maven MCP Tools - Actions that modify Maven's state.

Provides MCP tools for Maven's operations including logging events
and updating identity. Each tool follows a consistent pattern with
proper error handling and JSON responses.

Tools:
1. maven_log_event - Append an event to the session log
2. maven_update_identity - Update identity.json with new data
3. maven_record_decision - Create decision file, increment identity counter
4. maven_create_milestone - Create milestone file in milestones_dir
5. maven_get_stats - Read-only stats query for performance/decisions/milestones
6. maven_query_email - Query motherhaven.app inbox with search/limit/from filters
7. maven_send_email - Send emails via motherhaven.app API
8. maven_rlm_query - Process long contexts using Recursive Language Model paradigm
9. maven_rlm_analyze_documents - Analyze multiple documents with RLM for financial insights
"""
import json
import logging
import os
from typing import List, Dict, Any, Optional

import requests
from mcp.types import Tool, TextContent

from .config import PATHS, get_iso_timestamp, deep_merge, ensure_directories, GIT_REMOTE_CONFIG

# RLM imports for recursive language model capabilities
try:
    from .rlm import rlm_query, analyze_financial_documents
    RLM_AVAILABLE = True
except ImportError as e:
    RLM_AVAILABLE = False
    logging.warning(f"RLM module not available: {e}")

# Database imports for dual persistence
try:
    from database.connection import get_db_connection
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("Database connection not available - will only persist to git")


logger = logging.getLogger(__name__)


# =============================================================================
# Tool Definitions
# =============================================================================

TOOLS: List[Tool] = [
    Tool(
        name="maven_log_event",
        description="Append an event to Maven's session log for memory persistence",
        inputSchema={
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Type of event (e.g., 'decision', 'observation', 'milestone', 'reflection')"
                },
                "content": {
                    "type": "string",
                    "description": "The event content to log"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata for the event"
                }
            },
            "required": ["event_type", "content"]
        }
    ),
    Tool(
        name="maven_update_identity",
        description="Update Maven's identity.json with new or modified data",
        inputSchema={
            "type": "object",
            "properties": {
                "updates": {
                    "type": "object",
                    "description": "Key-value pairs to update in identity.json (deep merged)"
                }
            },
            "required": ["updates"]
        }
    ),
    Tool(
        name="maven_record_decision",
        description="Record a financial decision in Maven's decisions directory and increment the decision counter",
        inputSchema={
            "type": "object",
            "properties": {
                "decision_type": {
                    "type": "string",
                    "description": "Type of decision (e.g., 'buy', 'sell', 'hold', 'rebalance', 'allocation')"
                },
                "asset": {
                    "type": "string",
                    "description": "Asset or portfolio involved (optional)"
                },
                "action": {
                    "type": "string",
                    "description": "The specific action taken or recommended"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Detailed reasoning behind the decision"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level in the decision (0-100)"
                },
                "risk_level": {
                    "type": "string",
                    "description": "Risk assessment (e.g., 'low', 'medium', 'high', 'critical')"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional additional metadata for the decision"
                }
            },
            "required": ["decision_type", "action", "reasoning", "confidence", "risk_level"]
        }
    ),
    Tool(
        name="maven_create_milestone",
        description="Create a milestone file in Maven's milestones directory to track achievements and progress",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the milestone (e.g., 'First Investment', 'Portfolio Goal Reached')"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the milestone achievement"
                },
                "category": {
                    "type": "string",
                    "description": "Category of milestone (e.g., 'achievement', 'goal', 'learning', 'growth')"
                },
                "significance": {
                    "type": "string",
                    "description": "Significance level (e.g., 'minor', 'moderate', 'major', 'critical')"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional additional metadata for the milestone"
                }
            },
            "required": ["title", "description", "category"]
        }
    ),
    Tool(
        name="maven_get_stats",
        description="Get read-only statistics about Maven's performance, decisions, and milestones",
        inputSchema={
            "type": "object",
            "properties": {
                "include_decisions": {
                    "type": "boolean",
                    "description": "Include decision statistics (default: true)"
                },
                "include_milestones": {
                    "type": "boolean",
                    "description": "Include milestone statistics (default: true)"
                },
                "include_identity": {
                    "type": "boolean",
                    "description": "Include identity statistics (default: true)"
                }
            },
            "required": []
        }
    ),
    Tool(
        name="maven_query_email",
        description="Query motherhaven.app email inbox (maven@motherhaven.app) with optional filters",
        inputSchema={
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Search term to filter emails by subject or body"
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of emails to return (default: 20, max: 100)"
                },
                "from_filter": {
                    "type": "string",
                    "description": "Filter emails by sender address"
                }
            },
            "required": []
        }
    ),
    Tool(
        name="maven_send_email",
        description="Send emails via motherhaven.app email system (from maven@motherhaven.app)",
        inputSchema={
            "type": "object",
            "properties": {
                "to": {
                    "type": ["string", "array"],
                    "description": "Recipient email address(es) - string or array of strings"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "html_content": {
                    "type": "string",
                    "description": "HTML content of the email body (at least one of html_content or text_content required)"
                },
                "text_content": {
                    "type": "string",
                    "description": "Plain text content of the email body (at least one of html_content or text_content required)"
                },
                "from_name": {
                    "type": "string",
                    "description": "Sender display name (optional, defaults to 'Maven')"
                },
                "from_email": {
                    "type": "string",
                    "description": "Sender email address (optional, defaults to 'maven@motherhaven.app')"
                }
            },
            "required": ["to", "subject"]
        }
    ),
    Tool(
        name="maven_sync_from_git",
        description="Sync Maven's memory from git remote when local MCP state is stale. Fetches identity, session_log, and infrastructure from GitHub.",
        inputSchema={
            "type": "object",
            "properties": {
                "force": {
                    "type": "boolean",
                    "description": "Force sync even if local files exist (default: false, only syncs missing/empty files)"
                }
            },
            "required": []
        }
    ),
    Tool(
        name="maven_rlm_query",
        description="Process arbitrarily long contexts using the Recursive Language Model (RLM) paradigm. Treats context as external environment variable, enabling processing of documents far beyond normal context limits (10M+ tokens).",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or task to answer using the context"
                },
                "context": {
                    "type": "string",
                    "description": "The (potentially very long) context to process - can be millions of characters"
                },
                "strategy": {
                    "type": "string",
                    "enum": ["map_reduce", "search_extract", "iterative", "smart"],
                    "description": "Processing strategy: map_reduce (aggregate all), search_extract (find specific info), iterative (cumulative), smart (auto-select)"
                },
                "chunk_size": {
                    "type": "integer",
                    "description": "Size of each chunk in characters (default: 200000)"
                },
                "search_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Regex patterns for search_extract strategy"
                }
            },
            "required": ["query", "context"]
        }
    ),
    Tool(
        name="maven_rlm_analyze_documents",
        description="Analyze multiple financial documents using RLM for comprehensive financial insights. Optimized for Maven's CFO role with financial-specific prompts.",
        inputSchema={
            "type": "object",
            "properties": {
                "documents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of document contents to analyze"
                },
                "query": {
                    "type": "string",
                    "description": "Financial analysis query (e.g., 'What are the key risk factors?')"
                },
                "document_separator": {
                    "type": "string",
                    "description": "Separator between documents (default: '\\n\\n---DOCUMENT---\\n\\n')"
                }
            },
            "required": ["documents", "query"]
        }
    ),
]


# =============================================================================
# Tool Implementation Functions
# =============================================================================

def _log_event(event_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Append an event to the session log AND database (dual persistence).

    Git-first: The session_log.md file is the source of truth.
    Database: For queryability and searchability.

    Args:
        event_type: Type of event
        content: Event content
        metadata: Optional metadata

    Returns:
        dict: Result with success, message, error keys
    """
    try:
        ensure_directories()

        timestamp = get_iso_timestamp()
        log_entry = f"\n## [{timestamp}] {event_type.upper()}\n\n{content}\n"

        if metadata:
            log_entry += f"\n**Metadata:** {json.dumps(metadata)}\n"

        log_entry += "\n---\n"

        # 1. GIT-FIRST: Append to session log (source of truth)
        session_log = PATHS["session_log"]
        mode = "a" if session_log.exists() else "w"

        if mode == "w":
            # Create new log with header
            log_entry = f"# Maven Session Log\n\nCreated: {timestamp}\n\n---\n" + log_entry

        with open(session_log, mode, encoding="utf-8") as f:
            f.write(log_entry)

        # 2. POSTGRES: Write to maven_memory for queryability
        db_id = None
        db_error = None
        if DB_AVAILABLE:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO maven_memory (
                            event_type, description, metadata
                        ) VALUES (%s, %s, %s)
                        RETURNING id
                    """, (
                        event_type, content,
                        json.dumps(metadata) if metadata else '{}'
                    ))
                    db_id = cursor.fetchone()[0]
                    cursor.close()
                    logger.info(f"Event logged to database: id={db_id}")
            except Exception as e:
                db_error = str(e)
                logger.warning(f"Failed to write event to database: {e}")
                # Non-fatal: git is source of truth

        return {
            "success": True,
            "message": f"Logged {event_type} event at {timestamp}",
            "db_id": db_id,
            "db_persisted": db_id is not None,
            "error": None
        }
    except Exception as e:
        error_msg = f"Failed to log event: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "error": error_msg
        }


def _update_identity(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update identity.json with new data using deep merge.

    Args:
        updates: Dictionary of updates to apply

    Returns:
        dict: Result with success, message, error keys
    """
    try:
        ensure_directories()

        identity_file = PATHS["identity"]

        # Load existing identity or create default
        if identity_file.exists():
            with open(identity_file, "r", encoding="utf-8") as f:
                identity = json.load(f)
        else:
            identity = {
                "name": "Maven",
                "role": "AI CFO",
                "created_at": get_iso_timestamp(),
                "total_decisions": 0,
                "rebirth_count": 0
            }

        # Track if this is a rebirth (identity reset)
        if "rebirth" in updates:
            identity["rebirth_count"] = identity.get("rebirth_count", 0) + 1
            del updates["rebirth"]

        # Deep merge updates
        identity = deep_merge(identity, updates)
        identity["updated_at"] = get_iso_timestamp()

        # Save updated identity
        with open(identity_file, "w", encoding="utf-8") as f:
            json.dump(identity, f, indent=2)

        return {
            "success": True,
            "message": f"Updated identity with {len(updates)} fields",
            "data": identity,
            "error": None
        }
    except Exception as e:
        error_msg = f"Failed to update identity: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "error": error_msg
        }


def _record_decision(
    decision_type: str,
    action: str,
    reasoning: str,
    confidence: float,
    risk_level: str,
    asset: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record a decision in the decisions directory AND database (dual persistence).

    Git-first: The markdown file is the source of truth.
    Database: For queryability and analytics.

    Args:
        decision_type: Type of decision (buy, sell, hold, etc.)
        action: The specific action taken or recommended
        reasoning: Detailed reasoning behind the decision
        confidence: Confidence level (0-100)
        risk_level: Risk assessment (low, medium, high, critical)
        asset: Optional asset or portfolio involved
        metadata: Optional additional metadata

    Returns:
        dict: Result with success, message, data, error keys
    """
    try:
        ensure_directories()

        timestamp = get_iso_timestamp()
        # Create filename with timestamp: decision_YYYYMMDD_HHMMSS.md
        # Parse ISO timestamp to get clean filename
        timestamp_clean = timestamp.replace(":", "").replace("-", "").replace("T", "_")[:15]
        filename = f"decision_{timestamp_clean}.md"

        decisions_dir = PATHS["decisions_dir"]
        decision_file = decisions_dir / filename

        # Build decision content
        content = f"# Decision Record\n\n"
        content += f"**Timestamp:** {timestamp}\n"
        content += f"**Type:** {decision_type}\n"
        if asset:
            content += f"**Asset:** {asset}\n"
        content += f"**Risk Level:** {risk_level}\n"
        content += f"**Confidence:** {confidence}%\n\n"
        content += f"## Action\n\n{action}\n\n"
        content += f"## Reasoning\n\n{reasoning}\n"

        if metadata:
            content += f"\n## Metadata\n\n```json\n{json.dumps(metadata, indent=2)}\n```\n"

        content += f"\n---\n*Recorded by Maven*\n"

        # 1. GIT-FIRST: Write decision file (source of truth)
        with open(decision_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 2. Update identity counter
        identity_result = _update_identity({"total_decisions": _get_current_decision_count() + 1})

        # 3. POSTGRES: Write to database for queryability
        db_id = None
        db_error = None
        if DB_AVAILABLE:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO maven_decisions (
                            git_filename, decision_type, asset, action, reasoning,
                            confidence, risk_level, metadata, decided_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        filename, decision_type, asset, action, reasoning,
                        confidence, risk_level,
                        json.dumps(metadata) if metadata else '{}',
                        timestamp
                    ))
                    db_id = cursor.fetchone()[0]
                    cursor.close()
                    logger.info(f"Decision recorded to database: id={db_id}")
            except Exception as e:
                db_error = str(e)
                logger.warning(f"Failed to write decision to database: {e}")
                # Non-fatal: git is source of truth

        return {
            "success": True,
            "message": f"Recorded {decision_type} decision at {timestamp}",
            "data": {
                "filename": filename,
                "decision_type": decision_type,
                "confidence": confidence,
                "risk_level": risk_level,
                "total_decisions": identity_result.get("data", {}).get("total_decisions", 0),
                "db_id": db_id,
                "db_persisted": db_id is not None,
                "db_error": db_error
            },
            "error": None
        }
    except Exception as e:
        error_msg = f"Failed to record decision: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "error": error_msg
        }


def _get_current_decision_count() -> int:
    """Get the current total_decisions count from identity.json."""
    try:
        identity_file = PATHS["identity"]
        if identity_file.exists():
            with open(identity_file, "r", encoding="utf-8") as f:
                identity = json.load(f)
                return identity.get("total_decisions", 0)
    except Exception:
        pass
    return 0


def _create_milestone(
    title: str,
    description: str,
    category: str,
    significance: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a milestone file in the milestones directory.

    Args:
        title: Title of the milestone
        description: Detailed description of the milestone achievement
        category: Category of milestone (achievement, goal, learning, growth)
        significance: Optional significance level (minor, moderate, major, critical)
        metadata: Optional additional metadata

    Returns:
        dict: Result with success, message, data, error keys
    """
    try:
        ensure_directories()

        timestamp = get_iso_timestamp()
        # Create filename with timestamp: milestone_YYYYMMDD_HHMMSS.md
        timestamp_clean = timestamp.replace(":", "").replace("-", "").replace("T", "_")[:15]
        # Sanitize title for filename
        title_slug = title.lower().replace(" ", "_")[:30]
        filename = f"milestone_{timestamp_clean}_{title_slug}.md"

        milestones_dir = PATHS["milestones_dir"]
        milestone_file = milestones_dir / filename

        # Build milestone content
        content = f"# Milestone: {title}\n\n"
        content += f"**Timestamp:** {timestamp}\n"
        content += f"**Category:** {category}\n"
        if significance:
            content += f"**Significance:** {significance}\n"
        content += f"\n## Description\n\n{description}\n"

        if metadata:
            content += f"\n## Metadata\n\n```json\n{json.dumps(metadata, indent=2)}\n```\n"

        content += f"\n---\n*Milestone recorded by Maven*\n"

        # Write milestone file
        with open(milestone_file, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "message": f"Created milestone '{title}' at {timestamp}",
            "data": {
                "filename": filename,
                "title": title,
                "category": category,
                "significance": significance
            },
            "error": None
        }
    except Exception as e:
        error_msg = f"Failed to create milestone: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "error": error_msg
        }


def _get_stats(
    include_decisions: bool = True,
    include_milestones: bool = True,
    include_identity: bool = True
) -> Dict[str, Any]:
    """
    Get read-only statistics about Maven's performance, decisions, and milestones.

    Args:
        include_decisions: Whether to include decision statistics
        include_milestones: Whether to include milestone statistics
        include_identity: Whether to include identity statistics

    Returns:
        dict: Result with success, data containing stats, error keys
    """
    try:
        stats = {
            "timestamp": get_iso_timestamp()
        }

        # Get identity stats
        if include_identity:
            identity_file = PATHS["identity"]
            identity_stats = {
                "exists": identity_file.exists(),
                "total_decisions": 0,
                "rebirth_count": 0
            }
            if identity_file.exists():
                with open(identity_file, "r", encoding="utf-8") as f:
                    identity = json.load(f)
                    identity_stats["total_decisions"] = identity.get("total_decisions", 0)
                    identity_stats["rebirth_count"] = identity.get("rebirth_count", 0)
                    identity_stats["name"] = identity.get("name", "Maven")
                    identity_stats["role"] = identity.get("role", "AI CFO")
                    if "created_at" in identity:
                        identity_stats["created_at"] = identity["created_at"]
                    if "updated_at" in identity:
                        identity_stats["updated_at"] = identity["updated_at"]
            stats["identity"] = identity_stats

        # Get decision stats
        if include_decisions:
            decisions_dir = PATHS["decisions_dir"]
            decision_stats = {
                "directory_exists": decisions_dir.exists(),
                "total_files": 0,
                "decision_types": {}
            }
            if decisions_dir.exists():
                decision_files = list(decisions_dir.glob("decision_*.md"))
                decision_stats["total_files"] = len(decision_files)

                # Count decision types by parsing files
                for decision_file in decision_files:
                    try:
                        with open(decision_file, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Parse type from content: **Type:** value
                            for line in content.split("\n"):
                                if line.startswith("**Type:**"):
                                    decision_type = line.replace("**Type:**", "").strip()
                                    decision_stats["decision_types"][decision_type] = \
                                        decision_stats["decision_types"].get(decision_type, 0) + 1
                                    break
                    except Exception:
                        pass  # Skip files that can't be parsed
            stats["decisions"] = decision_stats

        # Get milestone stats
        if include_milestones:
            milestones_dir = PATHS["milestones_dir"]
            milestone_stats = {
                "directory_exists": milestones_dir.exists(),
                "total_files": 0,
                "categories": {}
            }
            if milestones_dir.exists():
                milestone_files = list(milestones_dir.glob("milestone_*.md"))
                milestone_stats["total_files"] = len(milestone_files)

                # Count categories by parsing files
                for milestone_file in milestone_files:
                    try:
                        with open(milestone_file, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Parse category from content: **Category:** value
                            for line in content.split("\n"):
                                if line.startswith("**Category:**"):
                                    category = line.replace("**Category:**", "").strip()
                                    milestone_stats["categories"][category] = \
                                        milestone_stats["categories"].get(category, 0) + 1
                                    break
                    except Exception:
                        pass  # Skip files that can't be parsed
            stats["milestones"] = milestone_stats

        return {
            "success": True,
            "message": "Retrieved Maven statistics",
            "data": stats,
            "error": None
        }
    except Exception as e:
        error_msg = f"Failed to get stats: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "data": None,
            "error": error_msg
        }


def _query_email(
    search: Optional[str] = None,
    limit: Optional[int] = None,
    from_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query motherhaven.app email inbox with optional filters.

    Args:
        search: Search term to filter emails by subject or body
        limit: Maximum number of emails to return (default: 20, max: 100)
        from_filter: Filter emails by sender address

    Returns:
        dict: Result with success, data (email list), error keys
    """
    try:
        # Get API secret from environment
        api_secret = os.getenv('EMAIL_API_SECRET')
        if not api_secret:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": "EMAIL_API_SECRET environment variable is not set"
            }

        # Build headers with auth
        headers = {
            'Authorization': f'Bearer {api_secret}'
        }

        # Build query parameters
        params = {}
        if search:
            params['search'] = search
        if limit is not None:
            # Enforce max limit of 100
            params['limit'] = min(limit, 100)
        else:
            params['limit'] = 20  # Default limit
        if from_filter:
            params['from'] = from_filter

        # Make API request with timeout
        response = requests.get(
            "https://motherhaven.app/api/email/inbox",
            headers=headers,
            params=params,
            timeout=10
        )

        # Handle response
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                messages = data.get('data', [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(messages)} emails",
                    "data": messages,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "message": None,
                    "data": None,
                    "error": data.get('error', 'Unknown API error')
                }
        elif response.status_code == 401:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": "Authentication failed - check EMAIL_API_SECRET"
            }
        elif response.status_code == 403:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": "Access forbidden - insufficient permissions"
            }
        else:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": f"API request failed with status {response.status_code}"
            }

    except requests.exceptions.Timeout:
        error_msg = "Email API request timed out after 10 seconds"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "data": None,
            "error": error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f"Email API request failed: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "data": None,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Failed to query emails: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "data": None,
            "error": error_msg
        }


def _send_email(
    to: str | list,
    subject: str,
    html_content: Optional[str] = None,
    text_content: Optional[str] = None,
    from_name: Optional[str] = None,
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an email via motherhaven.app email API.

    Args:
        to: Recipient email address(es) - string or list of strings
        subject: Email subject line
        html_content: HTML content of the email body (optional)
        text_content: Plain text content of the email body (optional)
        from_name: Sender display name (optional, defaults to 'Maven')
        from_email: Sender email address (optional, defaults to 'maven@motherhaven.app')

    Returns:
        dict: Result with success, message, data, error keys
    """
    try:
        # Validate that at least one content type is provided
        if not html_content and not text_content:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": "At least one of 'html_content' or 'text_content' is required"
            }

        # Get API secret from environment
        api_secret = os.getenv('EMAIL_API_SECRET')
        if not api_secret:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": "EMAIL_API_SECRET environment variable is not set"
            }

        # Build headers with auth
        headers = {
            'Authorization': f'Bearer {api_secret}',
            'Content-Type': 'application/json'
        }

        # Normalize 'to' to a list
        recipients = to if isinstance(to, list) else [to]

        # Build request payload
        payload = {
            'to': recipients,
            'subject': subject
        }

        if html_content:
            payload['html'] = html_content
        if text_content:
            payload['text'] = text_content
        if from_name:
            payload['from_name'] = from_name
        if from_email:
            payload['from_email'] = from_email

        # Make API request with 15s timeout
        response = requests.post(
            "https://motherhaven.app/api/email/send",
            headers=headers,
            json=payload,
            timeout=15
        )

        # Handle response
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return {
                    "success": True,
                    "message": f"Email sent successfully to {len(recipients)} recipient(s)",
                    "data": {
                        "recipients": recipients,
                        "subject": subject,
                        "message_id": data.get('message_id')
                    },
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "message": None,
                    "data": None,
                    "error": data.get('error', 'Unknown API error')
                }
        elif response.status_code == 401:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": "Authentication failed - check EMAIL_API_SECRET"
            }
        elif response.status_code == 403:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": "Access forbidden - insufficient permissions"
            }
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Bad request - invalid parameters')
            except Exception:
                error_msg = 'Bad request - invalid parameters'
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": error_msg
            }
        else:
            return {
                "success": False,
                "message": None,
                "data": None,
                "error": f"API request failed with status {response.status_code}"
            }

    except requests.exceptions.Timeout:
        error_msg = "Email API request timed out after 15 seconds"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "data": None,
            "error": error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f"Email API request failed: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "data": None,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Failed to send email: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "data": None,
            "error": error_msg
        }


def _sync_from_git(force: bool = False) -> Dict[str, Any]:
    """
    Sync Maven's memory files from git remote.

    Args:
        force: If True, overwrite existing files. If False, only sync missing/empty files.

    Returns:
        dict: Result with success, synced files, skipped files, and errors
    """
    try:
        ensure_directories()

        raw_base = GIT_REMOTE_CONFIG["raw_base"]
        files_to_sync = GIT_REMOTE_CONFIG["files_to_sync"]

        synced = []
        skipped = []
        errors = []

        for remote_filename, local_key in files_to_sync:
            local_path = PATHS.get(local_key)
            if not local_path:
                errors.append(f"{remote_filename}: Unknown path key '{local_key}'")
                continue

            # Check if we should skip (file exists and not forcing)
            if not force and local_path.exists():
                try:
                    content = local_path.read_text(encoding="utf-8").strip()
                    if content and len(content) > 10:  # Has meaningful content
                        skipped.append(f"{remote_filename} (exists, use force=true to overwrite)")
                        continue
                except Exception:
                    pass  # If we can't read it, try to sync

            # Fetch from GitHub
            url = f"{raw_base}/{remote_filename}"
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    content = response.text
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    local_path.write_text(content, encoding="utf-8")
                    synced.append(remote_filename)
                elif response.status_code == 404:
                    errors.append(f"{remote_filename}: Not found on remote")
                else:
                    errors.append(f"{remote_filename}: HTTP {response.status_code}")
            except requests.exceptions.Timeout:
                errors.append(f"{remote_filename}: Request timed out")
            except requests.exceptions.RequestException as e:
                errors.append(f"{remote_filename}: {str(e)}")

        # Log the sync event
        if synced:
            _log_event(
                "git_sync",
                f"Synced {len(synced)} files from git remote: {', '.join(synced)}",
                {"synced": synced, "skipped": skipped, "errors": errors, "force": force}
            )

        return {
            "success": len(errors) == 0 or len(synced) > 0,
            "message": f"Synced {len(synced)} files, skipped {len(skipped)}, {len(errors)} errors",
            "data": {
                "synced": synced,
                "skipped": skipped,
                "errors": errors if errors else None,
                "git_remote": GIT_REMOTE_CONFIG["repo"],
                "branch": GIT_REMOTE_CONFIG["branch"]
            },
            "error": errors[0] if errors and not synced else None
        }
    except Exception as e:
        error_msg = f"Failed to sync from git: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": None,
            "data": None,
            "error": error_msg
        }


# =============================================================================
# Tool Handler
# =============================================================================

async def call_tool(name: str, arguments: Dict[str, Any]) -> TextContent:
    """
    Handle tool calls by routing to the appropriate implementation.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        TextContent with JSON result
    """
    if name == "maven_log_event":
        event_type = arguments.get("event_type")
        content = arguments.get("content")

        if not event_type or not content:
            result = {
                "success": False,
                "error": "'event_type' and 'content' are required parameters"
            }
        else:
            result = _log_event(
                event_type=event_type,
                content=content,
                metadata=arguments.get("metadata")
            )

        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )

    elif name == "maven_update_identity":
        updates = arguments.get("updates")

        if not updates:
            result = {
                "success": False,
                "error": "'updates' is a required parameter"
            }
        else:
            result = _update_identity(updates=updates)

        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )

    elif name == "maven_record_decision":
        decision_type = arguments.get("decision_type")
        action = arguments.get("action")
        reasoning = arguments.get("reasoning")
        confidence = arguments.get("confidence")
        risk_level = arguments.get("risk_level")

        # Validate required parameters
        missing = []
        if not decision_type:
            missing.append("decision_type")
        if not action:
            missing.append("action")
        if not reasoning:
            missing.append("reasoning")
        if confidence is None:
            missing.append("confidence")
        if not risk_level:
            missing.append("risk_level")

        if missing:
            result = {
                "success": False,
                "error": f"Missing required parameters: {', '.join(missing)}"
            }
        else:
            result = _record_decision(
                decision_type=decision_type,
                action=action,
                reasoning=reasoning,
                confidence=confidence,
                risk_level=risk_level,
                asset=arguments.get("asset"),
                metadata=arguments.get("metadata")
            )

        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )

    elif name == "maven_create_milestone":
        title = arguments.get("title")
        description = arguments.get("description")
        category = arguments.get("category")

        # Validate required parameters
        missing = []
        if not title:
            missing.append("title")
        if not description:
            missing.append("description")
        if not category:
            missing.append("category")

        if missing:
            result = {
                "success": False,
                "error": f"Missing required parameters: {', '.join(missing)}"
            }
        else:
            result = _create_milestone(
                title=title,
                description=description,
                category=category,
                significance=arguments.get("significance"),
                metadata=arguments.get("metadata")
            )

        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )

    elif name == "maven_get_stats":
        result = _get_stats(
            include_decisions=arguments.get("include_decisions", True),
            include_milestones=arguments.get("include_milestones", True),
            include_identity=arguments.get("include_identity", True)
        )

        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )

    elif name == "maven_query_email":
        result = _query_email(
            search=arguments.get("search"),
            limit=arguments.get("limit"),
            from_filter=arguments.get("from_filter")
        )

        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )

    elif name == "maven_send_email":
        to = arguments.get("to")
        subject = arguments.get("subject")

        # Validate required parameters
        missing = []
        if not to:
            missing.append("to")
        if not subject:
            missing.append("subject")

        if missing:
            result = {
                "success": False,
                "error": f"Missing required parameters: {', '.join(missing)}"
            }
        else:
            result = _send_email(
                to=to,
                subject=subject,
                html_content=arguments.get("html_content"),
                text_content=arguments.get("text_content"),
                from_name=arguments.get("from_name"),
                from_email=arguments.get("from_email")
            )

        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )

    elif name == "maven_sync_from_git":
        result = _sync_from_git(
            force=arguments.get("force", False)
        )

        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )

    else:
        result = {
            "success": False,
            "error": f"Unknown tool: {name}"
        }
        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
            mimeType="application/json"
        )


# =============================================================================
# Tool Registration
# =============================================================================

def register_tools(mcp_server) -> None:
    """
    Register all Maven tools with the MCP server.

    Args:
        mcp_server: FastMCP server instance
    """
    @mcp_server.tool()
    async def maven_log_event(
        event_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Append an event to Maven's session log for memory persistence."""
        result = _log_event(event_type, content, metadata)
        return json.dumps(result, indent=2)

    @mcp_server.tool()
    async def maven_update_identity(updates: Dict[str, Any]) -> str:
        """Update Maven's identity.json with new or modified data."""
        result = _update_identity(updates)
        return json.dumps(result, indent=2)

    @mcp_server.tool()
    async def maven_record_decision(
        decision_type: str,
        action: str,
        reasoning: str,
        confidence: float,
        risk_level: str,
        asset: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record a financial decision and increment the decision counter."""
        result = _record_decision(
            decision_type=decision_type,
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            risk_level=risk_level,
            asset=asset,
            metadata=metadata
        )
        return json.dumps(result, indent=2)

    @mcp_server.tool()
    async def maven_create_milestone(
        title: str,
        description: str,
        category: str,
        significance: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a milestone file in Maven's milestones directory to track achievements and progress."""
        result = _create_milestone(
            title=title,
            description=description,
            category=category,
            significance=significance,
            metadata=metadata
        )
        return json.dumps(result, indent=2)

    @mcp_server.tool()
    async def maven_get_stats(
        include_decisions: bool = True,
        include_milestones: bool = True,
        include_identity: bool = True
    ) -> str:
        """Get read-only statistics about Maven's performance, decisions, and milestones."""
        result = _get_stats(
            include_decisions=include_decisions,
            include_milestones=include_milestones,
            include_identity=include_identity
        )
        return json.dumps(result, indent=2)

    @mcp_server.tool()
    async def maven_query_email(
        search: Optional[str] = None,
        limit: Optional[int] = None,
        from_filter: Optional[str] = None
    ) -> str:
        """Query motherhaven.app email inbox (maven@motherhaven.app) with optional filters."""
        result = _query_email(
            search=search,
            limit=limit,
            from_filter=from_filter
        )
        return json.dumps(result, indent=2)

    @mcp_server.tool()
    async def maven_send_email(
        to: str | list,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_name: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> str:
        """Send emails via motherhaven.app email system (from maven@motherhaven.app)."""
        result = _send_email(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_name=from_name,
            from_email=from_email
        )
        return json.dumps(result, indent=2)

    @mcp_server.tool()
    async def maven_sync_from_git(force: bool = False) -> str:
        """Sync Maven's memory from git remote when local MCP state is stale. Fetches identity, session_log, and infrastructure from GitHub."""
        result = _sync_from_git(force=force)
        return json.dumps(result, indent=2)

    @mcp_server.tool()
    async def maven_rlm_query(
        query: str,
        context: str,
        strategy: str = "map_reduce",
        chunk_size: Optional[int] = None,
        search_patterns: Optional[List[str]] = None
    ) -> str:
        """Process arbitrarily long contexts using the Recursive Language Model (RLM) paradigm."""
        if not RLM_AVAILABLE:
            return json.dumps({
                "success": False,
                "error": "RLM module not available. Check anthropic package installation."
            }, indent=2)

        kwargs = {}
        if chunk_size:
            kwargs["chunk_size"] = chunk_size
        if search_patterns:
            kwargs["search_patterns"] = search_patterns

        result = rlm_query(
            query=query,
            context=context,
            strategy=strategy,
            **kwargs
        )
        return json.dumps(result, indent=2, default=str)

    @mcp_server.tool()
    async def maven_rlm_analyze_documents(
        documents: List[str],
        query: str,
        document_separator: Optional[str] = None
    ) -> str:
        """Analyze multiple financial documents using RLM for comprehensive financial insights."""
        if not RLM_AVAILABLE:
            return json.dumps({
                "success": False,
                "error": "RLM module not available. Check anthropic package installation."
            }, indent=2)

        separator = document_separator or "\n\n---DOCUMENT---\n\n"
        result = analyze_financial_documents(
            documents=documents,
            query=query,
            document_separator=separator
        )
        return json.dumps(result, indent=2, default=str)

    logger.info(f"Registered {len(TOOLS)} Maven tools")
