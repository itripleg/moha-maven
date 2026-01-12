# Maven MCP Server

Maven MCP (Model Context Protocol) server provides persistent identity, memory, and operational tools for Maven - an AI CFO assistant for the Motherhaven platform.

## Overview

Maven MCP enables Claude Desktop and other MCP clients to:
- **Auto-load Maven's context** - Identity, personality, and memory without manual initialization
- **Persist decisions and milestones** - Track financial decisions and achievements
- **Query and send emails** - Interact with the motherhaven.app email system
- **Maintain session memory** - Chronological event logging across sessions

## Installation

### Prerequisites

- Python 3.10+
- `mcp` package with FastMCP support
- `requests` library

### Setup

```bash
# Navigate to the project root
cd moha-bot

# Install the package in development mode
pip install -e services/maven_mcp

# Or install dependencies manually
pip install mcp requests
```

### Verify Installation

```bash
# Test import
python -c "from services.maven_mcp.server import main; print('OK')"

# Check tool count
python -c "from services.maven_mcp.tools import TOOLS; print(f'Tools: {len(TOOLS)}')"

# Check resource count
python -c "from services.maven_mcp.resources import RESOURCES; print(f'Resources: {len(RESOURCES)}')"
```

## Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "maven": {
      "command": "python",
      "args": ["-m", "services.maven_mcp.server"],
      "cwd": "/path/to/moha-bot",
      "env": {
        "EMAIL_API_SECRET": "your-api-secret-here"
      }
    }
  }
}
```

### Windows Configuration Example

```json
{
  "mcpServers": {
    "maven": {
      "command": "python",
      "args": ["-m", "services.maven_mcp.server"],
      "cwd": "C:\\Users\\username\\projects\\moha-bot",
      "env": {
        "EMAIL_API_SECRET": "your-api-secret-here"
      }
    }
  }
}
```

## Running the Server

```bash
# Run directly
python -m services.maven_mcp.server

# Expected output:
# 2024-XX-XX - INFO - Starting Maven MCP Server...
# 2024-XX-XX - INFO - Ensured Maven data directories exist
# 2024-XX-XX - INFO - Registered 6 Maven resources
# 2024-XX-XX - INFO - Registered 7 Maven tools
# 2024-XX-XX - INFO - Maven MCP Server running: maven-mcp
```

## Resources

Resources provide read-only context that Claude can access:

| URI | Description | MIME Type |
|-----|-------------|-----------|
| `maven://identity` | Core identity data (name, role, stats) | `application/json` |
| `maven://persona` | Personality definition and guidelines | `text/markdown` |
| `maven://memory` | Session log with event history | `text/markdown` |
| `maven://decisions` | Recent decision records | `text/markdown` |
| `maven://milestones` | Achievement records | `text/markdown` |
| `maven://infrastructure` | Motherhaven platform knowledge | `application/json` |

## Tools

Tools allow Claude to perform actions:

### maven_log_event

Append an event to Maven's session log for memory persistence.

```json
{
  "event_type": "observation",
  "content": "Noticed market volatility increasing",
  "metadata": {"market": "crypto", "severity": "moderate"}
}
```

### maven_update_identity

Update Maven's identity.json with new or modified data (deep merged).

```json
{
  "updates": {
    "current_focus": "portfolio rebalancing",
    "preferences": {"risk_tolerance": "moderate"}
  }
}
```

### maven_record_decision

Record a financial decision and increment the decision counter.

```json
{
  "decision_type": "rebalance",
  "asset": "ETH/BTC",
  "action": "Increase ETH allocation by 5%",
  "reasoning": "ETH showing stronger fundamentals...",
  "confidence": 75,
  "risk_level": "medium",
  "metadata": {"trigger": "quarterly_review"}
}
```

### maven_create_milestone

Create a milestone to track achievements and progress.

```json
{
  "title": "First Profitable Quarter",
  "description": "Achieved 12% portfolio growth in Q1",
  "category": "achievement",
  "significance": "major",
  "metadata": {"roi": 12.3}
}
```

### maven_get_stats

Get read-only statistics about Maven's performance.

```json
{
  "include_decisions": true,
  "include_milestones": true,
  "include_identity": true
}
```

### maven_query_email

Query the motherhaven.app email inbox.

```json
{
  "search": "invoice",
  "limit": 10,
  "from_filter": "accounting@example.com"
}
```

### maven_send_email

Send emails via motherhaven.app email system.

```json
{
  "to": ["user@example.com"],
  "subject": "Weekly Portfolio Summary",
  "html_content": "<h1>Portfolio Update</h1><p>Your portfolio grew 5% this week.</p>",
  "text_content": "Portfolio Update\n\nYour portfolio grew 5% this week.",
  "from_name": "Maven"
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_API_SECRET` | For email tools | - | Bearer token for motherhaven email API |
| `MAVEN_BASE_DIR` | No | Project root | Override base directory for Maven data |
| `MAVEN_MCP_HOST` | No | `localhost` | Server host binding |
| `MAVEN_MCP_PORT` | No | `3100` | Server port |

## Data Directory Structure

Maven stores data in `.moha/maven/` relative to the project root:

```
.moha/
└── maven/
    ├── identity.json        # Core identity data
    ├── session_log.md       # Append-only event history
    ├── infrastructure.json  # Platform knowledge
    ├── personas/
    │   └── maven-v1.md      # Personality definition
    ├── decisions/
    │   └── decision_*.md    # Decision records
    └── milestones/
        └── milestone_*.md   # Milestone records
```

## Testing

Run the test suite:

```bash
# Run all Maven MCP tests
python -m pytest services/maven_mcp/tests/ -v

# Run specific test files
python -m pytest services/maven_mcp/tests/test_resources.py -v
python -m pytest services/maven_mcp/tests/test_tools.py -v
```

## Troubleshooting

### Server won't start

1. Verify Python version: `python --version` (requires 3.10+)
2. Check mcp package: `python -c "import mcp; print(mcp.__version__)"`
3. Verify working directory in Claude Desktop config

### Email tools return errors

1. Ensure `EMAIL_API_SECRET` is set in environment or Claude Desktop config
2. Check API connectivity to motherhaven.app
3. Verify bearer token is valid and not expired

### Resources return empty data

1. Check that `.moha/maven/` directory exists
2. Verify file permissions allow read/write access
3. Run `python -m services.maven_mcp.server` once to create directories

### Claude Desktop doesn't show Maven tools

1. Restart Claude Desktop after config changes
2. Verify JSON syntax in `claude_desktop_config.json`
3. Check that `cwd` path is absolute and correct

## License

Part of the moha-bot project.
