# Maven Service - Build Status

## Repository Created ✅
**GitHub:** https://github.com/itripleg/moha-maven

---

## Bootstrap Complete ✅

### Docker Infrastructure
- ✅ `Dockerfile` - Python 3.11 with git, supervisor
- ✅ `docker-compose.yml` - Standalone mode (Maven + PostgreSQL + Redis)
- ✅ `docker-compose.moha-bot.yml` - Integration mode (uses moha-bot's moha_redis)
- ✅ `supervisord.conf` - Runs Flask API (5002) + MCP server (3100)
- ✅ `requirements.txt` - All dependencies listed
- ✅ `.env.example` - Environment configuration template with Redis DB selection

### Project Structure
```
moha-maven/
├── routes/          ✅ Created (empty, ready for Flask blueprints)
├── core/            ✅ Created (empty, ready for decision engine, git persistence)
├── database/        ✅ Created (empty, ready for DB modules)
│   └── schemas/     ✅ Created (ready for maven_tables.sql)
├── claude/          ✅ Created (empty, ready for interactive CLI)
└── utils/           ✅ Created (empty, ready for redis cache, email client)
```

### Documentation
- ✅ `README.md` - Overview and status
- ✅ `AUTOCLAUDE_TASK.md` - Complete build specification (auto-claude ready)
- ✅ `.gitignore` - Python, Docker, IDE, env files

---

## Waiting For: MCP Server from moha-bot worktree 080 🍳

**Status:** Auto-claude is currently building in `moha-bot/.auto-claude/worktrees/tasks/080-complete-maven-mcp-server-implementation`

**What we need from 080:**
```
mcp/
├── __init__.py
├── config.py        - MCP paths and server config
├── resources.py     - 6 MCP resources (identity, personality, memory, decisions, milestones, infrastructure)
├── server.py        - MCP server entry point (FastMCP)
├── tools.py         - 7 MCP tools (log_event, update_identity, record_decision, create_milestone,
│                                   get_stats, query_email, send_email)
└── tests/
    ├── __init__.py
    ├── test_resources.py - Resource tests
    └── test_tools.py     - Tool tests (568 lines)
```

**Progress:**
- server.py (126 lines) ✅
- All 7 tools implemented ✅
- test_tools.py (568 lines) ✅
- Still cooking... 🍳

---

## Waiting For: Maven Data Files from moha-bot

**Source:** `moha-bot/.moha/maven/`

**Files to copy:**
```
.moha/maven/
├── identity.json           - Maven's identity and stats
├── infrastructure.json     - Motherhaven platform knowledge
├── session_log.md          - Event history
├── personas/
│   └── maven-v1.md        - Personality definition
├── decisions/
│   └── *.md               - Decision records
└── milestones/
    └── *.md               - Achievement records
```

**Note:** These are git-tracked persistence files, need to copy once MCP is ready.

---

## Waiting For: Core Logic from moha-bot

**Source:** `moha-bot/services/api/`

**Files to migrate:**
- `maven_core.py` (37KB) → `core/decision_engine.py`
- `maven_git.py` (31KB) → `core/git_persistence.py`
- `maven_spawn.py` (7.5KB) → `core/twin_spawner.py`
- `routes/maven_routes.py` → `routes/decision_routes.py`, `routes/status_routes.py`
- `database/maven_*.py` → `database/*.py` (5 modules)
- `database/schemas/maven_tables.sql` → `database/schemas/maven_tables.sql`

---

## Next Steps (Once 080 Finishes)

### 1. Copy MCP Server
```bash
# From moha-bot worktree 080
cp -r .auto-claude/worktrees/tasks/080-complete-maven-mcp-server-implementation/services/maven_mcp/* \
      moha-maven/mcp/
```

### 2. Copy Maven Data
```bash
# From moha-bot main repo
cp -r .moha/maven/* moha-maven/.moha/maven/
```

### 3. Migrate Core Logic
Use auto-claude to:
- Copy maven_core.py → core/decision_engine.py
- Copy maven_git.py → core/git_persistence.py
- Copy maven_spawn.py → core/twin_spawner.py
- Adapt routes from moha-bot backend
- Migrate database modules

### 4. Create Missing Files
Auto-claude needs to build:
- `app.py` - Flask API entry point
- `routes/decision_routes.py` - Decision endpoints
- `routes/status_routes.py` - Status and health checks
- `database/connection.py` - PostgreSQL connection pooling
- `claude/maven_session.py` - Claude session with MCP context
- `claude/interactive.py` - Interactive CLI for docker exec
- `utils/redis_cache.py` - Redis caching
- `utils/email_client.py` - Motherhaven email API client

### 5. Test Build
```bash
cd moha-maven
docker-compose build
docker-compose up -d
docker exec -it maven python -m claude.interactive
```

---

## Auto-Claude Ready ✅

The repository is ready for auto-claude to work in. `AUTOCLAUDE_TASK.md` contains complete specifications for building:
- Flask API infrastructure
- MCP server integration
- Interactive Claude CLI
- Database layer
- Core logic migration
- Email and Redis utilities

---

💎 Waiting for worktree 080 to finish cooking! 🍳
