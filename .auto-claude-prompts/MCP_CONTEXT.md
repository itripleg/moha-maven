# Maven MCP Server Context

Reference document for understanding Maven's MCP (Model Context Protocol) server implementation.

## Overview

Maven's MCP server exposes resources (read-only data) and tools (actions) that Claude Code can access directly during conversations.

**Server Details:**
- Name: `maven-mcp`
- Port: 3100
- Transport: stdio
- Location: `maven_mcp/` directory

## Current Resources (6)

Resources are read-only data exposed via URIs like `maven://identity`.

### 1. maven://identity
**File:** `maven_mcp/resources.py` (function: `get_identity`)
**Source:** `.moha/maven/identity.json`
**Content:** Maven's identity, stats, rebirth count, total decisions
**Schema:**
```json
{
  "name": "Maven",
  "role": "CFO, First Second Employee, HBIC of Treasury",
  "created_at": "2026-01-11",
  "total_decisions": 2,
  "rebirth_count": 4,
  "email": "maven@motherhaven.app",
  "boss": "JB",
  "mission": "We're too smart to be poor - Make money for moha",
  "updated_at": "2026-01-14T14:16:39.880251+00:00"
}
```

### 2. maven://personality
**Source:** `.moha/maven/personas/maven-v1.md`
**Content:** Maven's personality traits, communication style, values
**Format:** Markdown

### 3. maven://memory
**Source:** `.moha/maven/session_log.md`
**Content:** Full event history (rebirths, decisions, infrastructure changes)
**Format:** Markdown with timestamped entries

### 4. maven://infrastructure
**Source:** `.moha/maven/infrastructure.json`
**Content:** Knowledge about MoHa platform (docker services, databases, APIs)
**Schema:** JSONB with platform details

### 5. maven://decisions (all)
**Source:** `.moha/maven/decisions/` directory
**Content:** All decision files concatenated
**Format:** Markdown

### 6. maven://milestones (all)
**Source:** `.moha/maven/milestones/` directory
**Content:** All milestone files concatenated
**Format:** Markdown

## Current Tools (7)

Tools are actions Maven can perform via MCP.

### 1. maven_log_event
**Purpose:** Append event to session_log.md AND maven_memory table (dual persistence)
**Parameters:**
- `event_type` (required): Type of event (e.g., 'decision', 'observation', 'milestone')
- `content` (required): Event content
- `metadata` (optional): JSONB metadata

**Dual Persistence:**
1. Git: Appends to `.moha/maven/session_log.md`
2. Postgres: Inserts into `maven_memory` table

### 2. maven_update_identity
**Purpose:** Update identity.json with new data (deep merge)
**Parameters:**
- `updates` (required): Dictionary of updates

**Example:**
```python
maven_update_identity({"total_decisions": 3, "rebirth_count": 5})
```

### 3. maven_record_decision
**Purpose:** Record trading decision to git AND database (dual persistence)
**Parameters:**
- `decision_type` (required): 'buy', 'sell', 'hold', 'rebalance', 'allocation'
- `action` (required): Specific action taken
- `reasoning` (required): Detailed reasoning
- `confidence` (required): 0-100
- `risk_level` (required): 'low', 'medium', 'high', 'critical'
- `asset` (optional): BTC, ETH, etc.
- `metadata` (optional): JSONB

**Dual Persistence:**
1. Git: Creates `.moha/maven/decisions/decision_YYYYMMDD_HHMMSS.md`
2. Postgres: Inserts into `maven_decisions` table with `git_filename` reference
3. Updates `identity.json` total_decisions counter

**Returns:**
```json
{
  "success": true,
  "data": {
    "filename": "decision_20260114_142408.md",
    "db_id": 2,
    "db_persisted": true
  }
}
```

### 4. maven_create_milestone
**Purpose:** Create milestone file in milestones directory
**Parameters:**
- `title` (required): Milestone title
- `description` (required): Detailed description
- `category` (required): 'achievement', 'goal', 'learning', 'growth'
- `significance` (optional): 'minor', 'moderate', 'major', 'critical'
- `metadata` (optional): JSONB

**Creates:** `.moha/maven/milestones/milestone_YYYYMMDD_HHMMSS_title.md`

### 5. maven_get_stats
**Purpose:** Get read-only statistics about Maven's performance
**Parameters:**
- `include_decisions` (optional, default: true)
- `include_milestones` (optional, default: true)
- `include_identity` (optional, default: true)

**Returns:** Aggregated stats from git files and database

### 6. maven_query_email
**Purpose:** Query motherhaven.app email inbox (maven@motherhaven.app)
**Parameters:**
- `search` (optional): Filter by subject/body
- `limit` (optional, default: 20, max: 100)
- `from_filter` (optional): Filter by sender

**Requires:** `EMAIL_API_SECRET` env var

### 7. maven_send_email
**Purpose:** Send email via motherhaven.app (from maven@motherhaven.app)
**Parameters:**
- `to` (required): String or array of email addresses
- `subject` (required): Email subject
- `html_content` (optional): HTML body
- `text_content` (optional): Plain text body
- `from_name` (optional, default: 'Maven')
- `from_email` (optional, default: 'maven@motherhaven.app')

**Requires:** `EMAIL_API_SECRET` env var

## Implementation Details

### Dual Persistence Architecture

**Key Principle:** Git files are ALWAYS source of truth, postgres is for queryability.

**Flow:**
1. Tool called (e.g., `maven_record_decision`)
2. Write to git file FIRST (source of truth)
3. Write to postgres SECOND (best-effort, non-fatal if fails)
4. Return success with both `filename` and `db_id`

**Error Handling:**
- Git write fails → entire operation fails
- Postgres write fails → log warning, continue (git succeeded)

**Code Location:** `maven_mcp/tools.py`
- Lines 28-33: Database import with fallback
- Lines 339-450: `_record_decision` with dual persistence
- Lines 233-308: `_log_event` with dual persistence

### Adding New Resources

To add a new MCP resource:

1. **Update `maven_mcp/resources.py`:**
```python
@server.resource("maven://new_resource")
def get_new_resource() -> str:
    # Load data from git, postgres, or compute
    return json.dumps(data, indent=2)
```

2. **Register in RESOURCES list:**
```python
RESOURCES = [
    # ... existing
    Resource(uri="maven://new_resource", name="New Resource", ...)
]
```

3. **Test with Claude Code:**
```
ReadMcpResourceTool(server="maven", uri="maven://new_resource")
```

### Adding New Tools

To add a new MCP tool:

1. **Update `maven_mcp/tools.py`:**
```python
def _new_tool_impl(param1: str, param2: int) -> Dict[str, Any]:
    """Implementation function."""
    try:
        # Do work (git-first if writing)
        # Database second (best-effort)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

2. **Add to TOOLS list:**
```python
TOOLS = [
    # ... existing
    Tool(
        name="maven_new_tool",
        description="What this tool does",
        inputSchema={...}
    )
]
```

3. **Add to `call_tool` handler:**
```python
elif name == "maven_new_tool":
    result = _new_tool_impl(arguments.get("param1"), ...)
    return TextContent(type="text", text=json.dumps(result))
```

4. **Add to `register_tools` function:**
```python
@mcp_server.tool()
async def maven_new_tool(param1: str, param2: int) -> str:
    """Tool docstring."""
    result = _new_tool_impl(param1, param2)
    return json.dumps(result, indent=2)
```

## Database Schema Reference

Maven's postgres tables (see `database/schemas/maven_financial.sql`):

1. **maven_decisions** - Trading decisions (linked to git files)
2. **maven_trades** - Actual trade executions
3. **maven_portfolio_snapshots** - Point-in-time portfolio state
4. **maven_performance_metrics** - Aggregated performance stats
5. **maven_insights** - Market observations and predictions
6. **maven_memory** - General event log (backup of session_log.md)
7. **maven_conversations** - Full conversation transcripts

**Key Columns:**
- `maven_decisions.git_filename` - Links to source of truth
- `maven_trades.external_trade_id` - Links to MoHa's bot_trades.id
- `maven_trades.decision_id` - Links trade to Maven decision
- All tables have `created_at`, `updated_at` timestamps (UTC)

## Configuration

**Environment Variables:**
- `MAVEN_BASE_DIR` - Base directory for .moha/maven/ (default: /app in Docker)
- `MAVEN_MCP_PORT` - MCP server port (default: 3100)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Postgres config
- `EMAIL_API_SECRET` - motherhaven.app email API token

**File Paths (see `maven_mcp/config.py`):**
```python
PATHS = {
    "base": MAVEN_DATA_DIR,                    # .moha/maven/
    "identity": MAVEN_DATA_DIR / "identity.json",
    "session_log": MAVEN_DATA_DIR / "session_log.md",
    "decisions_dir": MAVEN_DATA_DIR / "decisions",
    "milestones_dir": MAVEN_DATA_DIR / "milestones",
    "infrastructure": MAVEN_DATA_DIR / "infrastructure.json",
}
```

## Testing MCP Resources/Tools

From Claude Code conversation:

```python
# Test resource
ReadMcpResourceTool(server="maven", uri="maven://identity")

# Test tool
mcp__maven__maven_record_decision(
    decision_type="hold",
    action="Observing market conditions",
    reasoning="Waiting for clearer signal",
    confidence=50,
    risk_level="low"
)
```

From command line:

```bash
# MCP server logs
docker logs maven --tail 50

# Check git files
docker exec maven ls -la /app/.moha/maven/decisions/
docker exec maven cat /app/.moha/maven/identity.json

# Check database
docker exec maven_postgres psql -U maven_user -d maven_data -c "SELECT COUNT(*) FROM maven_decisions;"
```

---

**Last Updated:** 2026-01-14
**For MoHa.** 💎
