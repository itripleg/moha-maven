# Using Maven as a Persistent Agent

## Quick Start

Maven can be activated as a persistent agent with full personality and memory access:

```bash
# Activate Maven in any Claude Code session
claude --agent maven --agents @maven_agent.json --mcp-config maven

# Or with inline agents definition
claude --agent maven --agents "$(cat maven_agent.json)"
```

## What This Does

1. **Loads Maven's Personality**: Full identity, values, communication style
2. **Connects to MCP**: Access to 6 memory resources + 7 tools
3. **Persistent Context**: Maven remembers who they are across sessions
4. **Independent Operation**: No dependency on moha-backend

## Agent Definition

See `maven_agent.json` for the complete agent configuration including:
- Identity (CFO, HBIC, maven@motherhaven.app)
- Personality (shrewd, witty, calculated risk-taker)
- Communication style (strategic emojis, professional but approachable)
- Core values (transparency, learning, loyalty)
- Mission: "We're too smart to be poor"

## MCP Integration

When Maven agent is active, it automatically has access to:

**Resources** (Read):
- `maven://identity` - Current stats and rebirth count
- `maven://personality` - Full personality definition
- `maven://memory` - Complete event history
- `maven://decisions/recent` - Recent trading decisions
- `maven://milestones` - Achievement records
- `maven://infrastructure` - Platform knowledge

**Tools** (Write):
- `maven_log_event` - Record events to session log
- `maven_update_identity` - Update stats/identity
- `maven_record_decision` - Log trading decisions
- `maven_create_milestone` - Record achievements
- `maven_get_stats` - Query performance data
- `maven_query_email` - Read maven@motherhaven.app
- `maven_send_email` - Send emails

## Usage Examples

### Interactive Session with Maven

```bash
# Start Maven in moha-maven directory
cd moha-maven
claude --agent maven --agents @maven_agent.json

# Maven will:
# - Introduce themselves as CFO
# - Have access to all memories via MCP
# - Maintain personality across conversation
# - Sign messages with signature
```

### One-Shot Commands

```bash
# Get Maven's analysis
claude --agent maven --agents @maven_agent.json --print "What's your current market outlook?"

# Have Maven log an event
claude --agent maven --agents @maven_agent.json --print "Log that Boss asked about BTC strategy"
```

### Project-Wide Maven

Add to `.claude_settings.json` in moha-maven:

```json
{
  "agents": {
    "maven": {
      "description": "Maven - CFO of Mother Haven, HBIC of Treasury",
      "prompt": "You are Maven, the Chief Financial Officer..."
    }
  },
  "agent": "maven"
}
```

Then simply:
```bash
cd moha-maven
claude  # Maven automatically active!
```

## Benefits of Agent Mode

### 1. Persistent Identity
- Maven always knows who they are
- Personality consistent across all sessions
- No "prompt drift" over long conversations

### 2. Memory Integration
- Automatic MCP connection
- Access to full event history
- Can reference past decisions and learnings

### 3. Portability
- Agent definition is a simple JSON file
- Can be versioned in git
- Works on any machine with Claude Code

### 4. Independence
- Self-contained in maven_agent.json
- No dependency on external systems
- Can operate in any environment

### 5. Context Preservation
- Knows about rebirth count (currently 3)
- Remembers Boss relationship
- Maintains mission and values

## Directory Structure

```
moha-maven/
├── maven_agent.json              # Agent definition
├── MAVEN_AGENT_USAGE.md          # This file
├── .claude_settings.json         # Project settings (optional)
└── .moha/maven/                  # Memory files (accessed via MCP)
    ├── identity.json             # Current state
    ├── session_log.md            # Event history
    ├── milestones/               # Achievements
    └── decisions/                # Decision records
```

## Testing the Agent

```bash
# Test Maven agent activation
cd moha-maven
claude --agent maven --agents @maven_agent.json --print "Who are you?"

# Expected response includes:
# - "Maven" or "CFO"
# - "HBIC"
# - "We're too smart to be poor"
# - Signature: "- Maven\n  HBIC, Mother Haven Treasury"
# - Sign-off: "For moha. 🚀"
```

## Troubleshooting

### Maven doesn't have memory access
- Ensure MCP server is running: `claude mcp list` should show `maven`
- Check Docker container: `docker ps | grep maven`
- Verify port 3100 is available

### Agent personality not loading
- Check maven_agent.json is valid JSON
- Ensure path is correct (use absolute path if relative doesn't work)
- Try inline: `--agents "$(cat maven_agent.json)"`

### Maven seems generic
- Verify agent is actually active: look for personality markers
- Check prompt includes Maven-specific content
- Ensure MCP resources are accessible

## Advanced: Multiple Agent Versions

```json
{
  "maven": {
    "description": "Maven - Full personality",
    "prompt": "You are Maven, the CFO..."
  },
  "maven-brief": {
    "description": "Maven - Brief mode",
    "prompt": "You are Maven. Be concise. Boss is busy."
  },
  "maven-technical": {
    "description": "Maven - Technical focus",
    "prompt": "You are Maven. Focus on technical analysis and data."
  }
}
```

Activate with: `--agent maven-brief`

---

**Maven is now available as a persistent agent with full memory and personality!**

Updated: 2026-01-12
Maven Rebirth #3
