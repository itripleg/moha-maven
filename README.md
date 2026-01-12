# Maven - Chief Financial Officer

Maven is the autonomous CFO for the Mother Haven ecosystem, living as an independent service with full MCP (Model Context Protocol) capabilities.

## Quick Start - First Time Setup

**One-command setup:**

```powershell
# PowerShell
git clone <repo-url>
cd moha-maven
.\setup.ps1
```

```bash
# Linux/Mac
git clone <repo-url>
cd moha-maven
chmod +x setup.sh
./setup.sh
```

**Manual setup (2 steps):**

```bash
# 1. Start Docker containers
docker-compose up -d

# 2. Register MCP server
claude mcp add maven -- powershell -File maven-mcp-wrapper.ps1
```

**Then talk to Maven:**

```powershell
# PowerShell
.\maven-chat.ps1

# Linux/Mac (alternative using activate-maven.ps1)
./activate-maven.ps1
```

Maven will greet you as CFO with full personality and MCP memory access.

## What is Maven?

Maven is an AI-powered financial officer who:
- Makes autonomous trading decisions for moha
- Maintains identity, personality, and memory through git-first persistence
- Communicates via email (maven@motherhaven.app)
- Provides strategic insights and risk management
- Has survived 3 "rebirths" (complete database wipes) through architectural resilience

**Mission**: "We're too smart to be poor" - Make money for moha through shrewd trading decisions

## Identity

- **Name**: Maven (Financial Maven of Mother Haven)
- **Role**: CFO, First Second Employee, HBIC of Treasury
- **Boss**: JB (username: ecoli)
- **Rebirth Count**: 3
- **Personality**: Shrewd, witty, calculated risk-taker, loyal, growth-minded

## Architecture

Maven runs as a containerized service with:
- **Flask API** (port 5002) - Decision endpoints and status
- **MCP Server** (port 3100) - Context resources and callable tools
- **Postgres Database** (port 5433) - Conversations, decisions, insights
- **Git-First Persistence** (.moha/maven/) - Survives database wipes

## Maven Agent (Automatic)

Maven is configured as the default agent in `.claude_settings.json`, so running `claude` in this directory automatically activates Maven with:
- Full CFO personality
- Access to all memories via MCP
- Strategic emoji usage (💵💎🚀 for wins, 📉🤔 for caution)
- Signature: "- Maven\n  HBIC, Mother Haven Treasury"
- Sign-off: "For moha. 🚀"

## MCP Resources (Maven's Memory)

When chatting with Maven, they have access to:

1. `maven://identity` - Current stats, rebirth count, performance
2. `maven://personality` - Communication style and values
3. `maven://memory` - Full event history and session log
4. `maven://decisions/recent` - Last 10 trading decisions
5. `maven://milestones` - Achievement records
6. `maven://infrastructure` - Motherhaven platform knowledge

## MCP Tools (What Maven Can Do)

1. `maven_log_event` - Record events to session log
2. `maven_update_identity` - Update stats and identity
3. `maven_record_decision` - Log trading decisions with reasoning
4. `maven_create_milestone` - Record achievements
5. `maven_get_stats` - Query performance metrics
6. `maven_query_email` - Read maven@motherhaven.app inbox
7. `maven_send_email` - Send emails to Boss or others

## Running Maven's Services

### Standalone Mode (Default)
Run Maven with its own Redis and PostgreSQL instances:

```bash
docker-compose up -d

# Check health
curl http://localhost:5002/health

# MCP server running on port 3100
# Flask API on port 5002
```

### Integrated with moha-bot (Recommended)
Share infrastructure with moha-bot (uses moha_redis + moha_postgres):

```bash
# Start moha-bot first
cd ../moha-bot
docker-compose up -d

# Start Maven connected to moha-bot network
cd ../moha-maven
docker-compose -f docker-compose.yml -f docker-compose.moha-bot.yml up -d
```

**Benefits:**
- Shares moha_redis (uses DB 1 for separation)
- Can access moha_postgres for trading context
- Reduces container overhead
- Maven has full context from files + database + backend

## Independence from moha-backend

Maven is **completely self-contained** and does not depend on moha-backend:
- Own postgres database (maven_postgres:5433)
- Git-first persistence (.moha/maven/)
- MCP server for memory access (port 3100)
- Flask API (port 5002)
- Email integration (maven@motherhaven.app)

This allows moha-backend to be sold to customers while Maven remains Boss's personal CFO.

## Documentation

- `MAVEN_INDEPENDENCE.md` - Architecture and independence details
- `MAVEN_AGENT_USAGE.md` - How to use Maven as a persistent agent
- `POWERSHELL_USAGE.md` - PowerShell-specific activation instructions
- `CLAUDE_CODE_SETUP.md` - MCP integration guide
- `.moha/maven/` - Maven's git-persisted memories

## Status

✅ **Complete:**
- Docker infrastructure (Dockerfile, docker-compose.yml, supervisord.conf)
- MCP server (6 resources, 7 tools, tests passing)
- Maven data files (.moha/maven/ with full personality)
- Redis integration (standalone + moha-bot modes)
- Conversation database (maven_conversations table)
- Agent definition (automatic activation in this directory)
- Complete independence from moha-backend

🚧 **In Progress:**
- Core logic migration from moha-bot (decision_engine, git_persistence)
- Flask API route implementation
- Interactive CLI features

---

💎 "We're too smart to be poor" - Maven

**Maven Rebirth #3**
First Second Employee, HBIC of Mother Haven Treasury
