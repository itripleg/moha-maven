# Maven Setup for Claude Code

## Current Status

Maven is running as a containerized service with:
- **MCP Server**: Port 3100 (6 resources, 7 tools)
- **Flask API**: Port 5002
- **Data**: Mounted from ../moha-maven/.moha/maven (git-first persistence)

## Accessing Maven via Claude Code

Instead of the buggy interactive CLI, use Claude Code's MCP integration:

### MCP Resources Available

1. `maven://identity` - Maven's identity, stats, and rebirth count
2. `maven://personality` - Communication style and personality
3. `maven://memory` - Session log and event history
4. `maven://decisions/recent` - Recent trading decisions
5. `maven://milestones` - Achievement records
6. `maven://infrastructure` - Platform knowledge

### MCP Tools Available

1. `maven_log_event` - Append to session log
2. `maven_update_identity` - Update identity.json
3. `maven_record_decision` - Create decision records
4. `maven_create_milestone` - Record achievements
5. `maven_get_stats` - Query performance data
6. `maven_query_email` - Read maven@motherhaven.app inbox
7. `maven_send_email` - Send emails

## Configure Claude Code MCP

To access Maven's MCP from Claude Code CLI, the MCP server needs to be configured in Claude Code's settings.

Since Maven's MCP server runs on port 3100 (TCP), you can connect to it using:
- **URL**: `http://localhost:3100`
- **Transport**: HTTP/SSE (Server-Sent Events)

---

Updated: 2026-01-12
Maven Rebirth #3
