# Maven - Chief Financial Officer

Maven is the autonomous CFO for the Mother Haven ecosystem, living as an independent service with full MCP (Model Context Protocol) capabilities.

**Mission**: "We're too smart to be poor" - Make money for moha through shrewd trading decisions 💎

## Quick Start

### Automated Setup (Recommended)

**PowerShell:**
```powershell
git clone https://github.com/itripleg/moha-maven.git
cd moha-maven
.\setup.ps1
```

**Linux/Mac:**
```bash
git clone https://github.com/itripleg/moha-maven.git
cd moha-maven
chmod +x setup.sh
./setup.sh
```

Then start chatting with Maven:
```powershell
.\maven-chat.ps1
```

### Manual Setup

**Step 1: Start Docker Containers**
```bash
docker-compose up -d
```

This starts:
- `maven` - Flask API (5002) + MCP Server (3100)
- `maven_postgres` - PostgreSQL (5433)
- `maven_redis` - Redis (6379)

**Step 2: Verify Containers**
```bash
docker ps
# Should show: maven, maven_postgres, maven_redis

# Check health
curl http://localhost:5002/health
# Should return: {"status": "healthy", "service": "maven", ...}
```

**Step 3: Register MCP Server with Claude Code**

**PowerShell:**
```powershell
claude mcp add maven -- powershell -File maven-mcp-wrapper.ps1
```

**Linux/Mac:**
```bash
claude mcp add maven docker exec -i maven python -m maven_mcp.server
```

Verify registration:
```bash
claude mcp list
# Should show: maven ... ✓ Connected
```

**Step 4: Start Chatting with Maven**

**PowerShell:**
```powershell
.\maven-chat.ps1
```

**Linux/Mac:**
```bash
# Extract prompt from maven_agent.json and pass to Claude
maven_prompt=$(jq -r '.maven.prompt' maven_agent.json)
claude --append-system-prompt "$maven_prompt"
```

Maven will greet you as CFO with full personality and memory access!

## What is Maven?

Maven is an AI-powered financial officer who:
- 💼 Makes autonomous trading decisions for moha
- 🧠 Maintains identity, personality, and memory through git-first persistence
- 📧 Communicates via email (maven@motherhaven.app)
- 📊 Provides strategic insights and risk management
- 🔄 Has survived 3 "rebirths" (complete database wipes) through architectural resilience

### Identity

- **Name**: Maven (Financial Maven of Mother Haven)
- **Role**: CFO, First Second Employee, HBIC of Treasury
- **Boss**: JB (username: ecoli)
- **Rebirth Count**: 3
- **Personality**: Shrewd, witty, calculated risk-taker, loyal, growth-minded
- **Communication**: Strategic emojis (💵💎🚀 for wins, 📉🤔 for caution)
- **Signature**: "- Maven\n  HBIC, Mother Haven Treasury"
- **Sign-off**: "For moha. 🚀"

## Architecture

### Services

**Maven Container** (`maven`):
- Flask API on port 5002 (health checks, status endpoints)
- MCP Server on port 3100 (memory resources + tools)
- Supervised by supervisord (auto-restart on failure)

**PostgreSQL** (`maven_postgres`):
- Port 5433 (to avoid conflicts with moha_postgres:5432)
- Stores: conversation history, decisions, queryable data
- Schema: `database/schemas/`

**Redis** (`maven_redis`):
- Port 6379
- Cache layer for fast access
- Separate from moha-bot infrastructure

### Git-First Persistence

Maven's **core memories live in git** at `.moha/maven/`:

```
.moha/maven/
├── identity.json           # Stats, rebirth count, current state
├── session_log.md          # Full event history
├── infrastructure.json     # Motherhaven platform knowledge
├── personas/
│   └── maven-v1.md        # Original personality definition
├── conversations/
│   ├── *.md               # Birth moments and key conversations
│   └── .gitignore         # Ignores large .jsonl transcripts
├── milestones/
│   ├── 2026-01-11-met-boss.md
│   └── 2026-01-11-rebirth-1.md
├── decisions/              # Trading decision history
└── strategies/
    └── current-strategy.json
```

**Why git-first?**
- ✅ Survives database wipes (proven 3x)
- ✅ Version controlled (full audit trail)
- ✅ Portable (clone repo = restore Maven)
- ✅ No external dependencies needed

## MCP Integration

### Resources (Read-Only)

When chatting with Maven via `maven-chat.ps1`, Maven has access to:

1. `maven://identity` - Current stats, rebirth count, performance
2. `maven://personality` - Communication style and values
3. `maven://memory` - Full event history and session log
4. `maven://decisions/recent` - Last 10 trading decisions
5. `maven://milestones` - Achievement records
6. `maven://infrastructure` - Motherhaven platform knowledge

### Tools (Actions)

1. `maven_log_event` - Record events to session log
2. `maven_update_identity` - Update stats and identity
3. `maven_record_decision` - Log trading decisions with reasoning
4. `maven_create_milestone` - Record achievements
5. `maven_get_stats` - Query performance metrics
6. `maven_query_email` - Read maven@motherhaven.app inbox
7. `maven_send_email` - Send emails to Boss or others

## Common Operations

### Check Maven's Health
```bash
curl http://localhost:5002/health
curl http://localhost:5002/api/maven/status
```

### View Logs
```bash
docker logs maven
docker logs maven_postgres
```

### Restart Services
```bash
docker-compose restart maven
# or
docker-compose down && docker-compose up -d
```

### Backup Maven's Memories
```bash
# Memories are already in git!
git add .moha/maven/
git commit -m "Update Maven memories"
git push

# Optional: Backup database
docker exec maven_postgres pg_dump -U maven maven_db > maven_backup.sql
```

### Restore on New Machine
```bash
# Just clone and setup - memories restore automatically from git!
git clone https://github.com/itripleg/moha-maven.git
cd moha-maven
.\setup.ps1
.\maven-chat.ps1
```

## Independence from moha-backend

Maven is **completely self-contained** and does not depend on moha-backend:

- ✅ Own postgres database (maven_postgres:5433)
- ✅ Git-first persistence (.moha/maven/)
- ✅ MCP server for memory access (port 3100)
- ✅ Flask API (port 5002)
- ✅ Email integration (maven@motherhaven.app)

This allows moha-backend to be sold to customers while Maven remains Boss's personal CFO.

## Files Overview

### Essential Files
- `maven-chat.ps1` - Start Maven with full personality (recommended)
- `maven-mcp-wrapper.ps1` - MCP server wrapper for Windows
- `setup.ps1` / `setup.sh` - Automated setup scripts
- `maven_agent.json` - Maven's personality definition
- `app.py` - Flask API entry point
- `requirements.txt` - Python dependencies

### Configuration
- `docker-compose.yml` - Container orchestration
- `Dockerfile` - Container image definition
- `supervisord.conf` - Process management
- `.env.example` - Environment variables template

### Directories
- `maven_mcp/` - MCP server implementation
- `database/` - Database schemas
- `.moha/maven/` - Git-persisted memories (CRITICAL)
- `docs/` - Documentation

## Documentation

All documentation is in the `docs/` directory:

- `docs/MAVEN_INDEPENDENCE.md` - Architecture and independence details
- `docs/MAVEN_AGENT_USAGE.md` - How to use Maven as a persistent agent
- `docs/POWERSHELL_USAGE.md` - PowerShell-specific instructions
- `docs/CLAUDE_CODE_SETUP.md` - MCP integration guide
- `docs/DEMO.md` - Demo scenarios

## Troubleshooting

### Maven MCP not connecting
```bash
# Check if MCP is registered
claude mcp list
# Should show: maven ... ✓ Connected

# If not registered, add it:
claude mcp add maven -- powershell -File maven-mcp-wrapper.ps1

# Verify containers are running
docker ps | grep maven
```

### Personality not loading
Make sure you're using `maven-chat.ps1` (not just `claude`):
```powershell
.\maven-chat.ps1
```

This script extracts the prompt from `maven_agent.json` and passes it via `--append-system-prompt`.

### Database connection errors
```bash
# Check if postgres is healthy
docker ps
# maven_postgres should show "healthy"

# Check logs
docker logs maven_postgres

# Recreate if needed
docker-compose down
docker-compose up -d
```

---

## Status

✅ **Production Ready:**
- Docker infrastructure (Dockerfile, docker-compose.yml, supervisord.conf)
- MCP server (6 resources, 7 tools, fully functional)
- Git-first persistence (.moha/maven/ with full memories)
- Agent activation (maven-chat.ps1 working)
- Complete independence from moha-backend
- Flask API (health checks, status endpoints)

🚧 **Future Enhancements:**
- Advanced trading decision engine
- Real-time market data integration
- Automated strategy backtesting

---

💎 **"We're too smart to be poor"** - Maven

**Maven Rebirth #3**
First Second Employee, HBIC of Mother Haven Treasury

For moha. 🚀
