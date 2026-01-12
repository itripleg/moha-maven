# Accessing Maven via Claude Code

Boss, here's how to use Claude Code CLI to access Maven's memories instead of the buggy interactive CLI.

## Current Setup

Maven container is running with:
- **MCP Server**: Port 3100 (6 resources, 7 tools)
- **Flask API**: Port 5002 ✓ Healthy
- **Data Location**: `.moha/maven/` (mounted from host, synced with moha-bot)

## Option 1: Direct MCP Connection (Recommended)

Add Maven MCP to your Claude Code configuration:

**Location**: `C:\Users\ecoli\.claude\config.json` (or wherever Claude Code stores MCP config)

```json
{
  "mcpServers": {
    "maven": {
      "command": "docker",
      "args": ["exec", "-i", "maven", "python", "-m", "maven_mcp.server"],
      "env": {
        "MAVEN_DATA_PATH": "/app/.moha/maven"
      }
    }
  }
}
```

This lets Claude Code talk directly to Maven's MCP server inside the container.

## Option 2: Use moha-maven as Working Directory

Since `.moha/maven/` is mounted from `moha-maven/.moha/maven/`, you can:

1. Open Claude Code in moha-maven directory:
   ```bash
   cd C:\Users\ecoli\OneDrive\Documents\GitHub\moha-maven
   code .  # Or however you launch Claude Code
   ```

2. Access Maven files directly:
   - Identity: `.moha/maven/identity.json`
   - Session Log: `.moha/maven/session_log.md`
   - Decisions: `.moha/maven/decisions/`
   - Milestones: `.moha/maven/milestones/`

3. Make changes and they'll be live-synced to the container!

## Option 3: Use MCP Tools via HTTP (If Supported)

If Claude Code supports HTTP MCP connections:

```json
{
  "mcpServers": {
    "maven-http": {
      "url": "http://localhost:3100",
      "transport": "sse"
    }
  }
}
```

## Available Maven Resources

Once connected, you'll have access to:

1. `maven://identity` - Full identity, rebirth count (currently 3), stats
2. `maven://personality` - Communication style, personality traits
3. `maven://memory` - Session log with full event history
4. `maven://decisions/recent` - Last 10 trading decisions
5. `maven://milestones` - Achievement records
6. `maven://infrastructure` - Motherhaven platform knowledge

## Available Maven Tools

You can call these tools through MCP:

1. `maven_log_event` - Append events to session log
2. `maven_update_identity` - Update identity.json (rebirth count, stats, etc.)
3. `maven_record_decision` - Create decision records with reasoning
4. `maven_create_milestone` - Record achievements
5. `maven_get_stats` - Query performance metrics
6. `maven_query_email` - Read maven@motherhaven.app inbox
7. `maven_send_email` - Send emails to Boss or others

## Testing the Connection

Once configured, test it:

```bash
# In Claude Code CLI, try to access Maven's identity
# (exact syntax depends on how Claude Code exposes MCP resources)
```

Or manually test the Flask API:
```bash
curl http://localhost:5002/health
curl http://localhost:5002/api/maven/status
```

## Benefits Over Interactive CLI

- **No buggy terminal issues**: Use Claude Code's solid CLI interface
- **Better context**: Claude Code can see Maven files + MCP resources
- **Persistent history**: Claude Code tracks conversations
- **Tool integration**: All Claude Code tools (Read, Write, Edit) work with Maven files
- **Live sync**: Changes to files are immediately reflected in container

---

**Current State**: Maven healthy, files synced, ready for Claude Code connection.

Updated: 2026-01-12
Maven Rebirth #3
