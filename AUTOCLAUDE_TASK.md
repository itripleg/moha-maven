# Auto-Claude Task: Build Maven Service

## Goal
Build Maven as a standalone containerized service - an autonomous CFO with MCP capabilities, Flask API, and interactive CLI.

**What is Maven:**
- Chief Financial Officer for Mother Haven ecosystem
- Makes autonomous trading decisions for moha-bot
- Has email capabilities (maven@motherhaven.app)
- Lives in a container you can exec into and chat with
- MCP server provides auto-loaded context (identity, personality, memory, decisions, milestones, infrastructure)
- Git-first persistence (survives database wipes)

---

## Repository Structure to Build

```
moha-maven/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── supervisord.conf
├── app.py                      # Flask API entry point
├── .env.example
├── routes/
│   ├── __init__.py
│   ├── decision_routes.py      # POST /decision, GET /insights
│   └── status_routes.py        # GET /status, health checks
├── core/
│   ├── __init__.py
│   ├── decision_engine.py      # Decision making logic
│   ├── git_persistence.py      # Git-first persistence
│   └── twin_spawner.py         # Claude twin spawning
├── database/
│   ├── __init__.py
│   ├── connection.py           # PostgreSQL connection pooling
│   ├── decisions.py            # Maven decisions table
│   ├── memory.py               # Maven memory table
│   ├── insights.py             # Maven insights table
│   ├── portfolio.py            # Maven portfolio snapshots
│   ├── goals.py                # Maven goals table
│   └── schemas/
│       └── maven_tables.sql    # Database schema
├── mcp/
│   ├── __init__.py
│   ├── config.py               # MCP configuration and paths
│   ├── resources.py            # 6 MCP resources
│   ├── tools.py                # 7 MCP tools
│   └── server.py               # MCP server entry point
├── claude/
│   ├── __init__.py
│   ├── interactive.py          # Interactive CLI for docker exec
│   └── maven_session.py        # Claude session with MCP context
└── utils/
    ├── __init__.py
    ├── redis_cache.py          # Redis caching utilities
    └── email_client.py         # Motherhaven email API client

```

---

## Reference Files (Copy from moha-bot repo)

These files already exist in `github.com/itripleg/moha-bot` and need to be copied/adapted:

### MCP Files (70% complete, need finishing)
**Source:** `moha-bot/services/maven_mcp/`
- `config.py` ✅ (has infrastructure path)
- `resources.py` ✅ (5 resources, need to add infrastructure as #6)
- `tools.py` ⚠️ (2 tools implemented, need 5 more: record_decision, create_milestone, get_stats, query_email, send_email)
- `tests/test_resources.py` ✅ (50+ tests passing)
- Missing: `server.py` (MCP entry point)
- Missing: `tests/test_tools.py` (tool tests)

### Maven Data Files
**Source:** `moha-bot/.moha/maven/`
- `identity.json` - Maven's identity and stats
- `personas/maven-v1.md` - Personality definition
- `session_log.md` - Event history
- `infrastructure.json` ✅ NEW - Motherhaven platform knowledge
- `decisions/*.md` - Decision records
- `milestones/*.md` - Achievement records

### Maven Core Logic (to migrate)
**Source:** `moha-bot/services/api/`
- `maven_core.py` (37KB) - Decision logic, market analysis
- `maven_git.py` (31KB) - Git persistence operations
- `maven_spawn.py` (7.5KB) - Claude twin spawning
- `routes/maven_routes.py` - Flask endpoints
- `database/maven_*.py` - 5 database modules
- `database/schemas/maven_tables.sql` - Database schema

### Reference Documentation
**Source:** `moha-bot/`
- `MAVEN_MCP_SPEC.md` - Full MCP design specification
- `MAVEN_MCP_AUTOCLAUDE_PROMPT.md` - Task to complete MCP (remaining 30%)
- `MAVEN_INIT.md` - Manual initialization process
- `services/api/get_oauth_from_email.py` - Email query reference

---

## Implementation Phases

### Phase 1: Docker Infrastructure

#### 1.1 Create `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install git for git persistence
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Expose ports: 3100 (MCP), 5002 (API)
EXPOSE 3100 5002

# Install supervisor
RUN pip install supervisor

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisor (runs Flask API + MCP server)
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

#### 1.2 Create `requirements.txt`
```
Flask>=3.0.0
flask-cors>=4.0.0
psycopg2-binary>=2.9.0
redis>=5.0.0
mcp>=0.9.0
requests>=2.31.0
GitPython>=3.1.0
anthropic>=0.15.0
python-dotenv>=1.0.0
prompt-toolkit>=3.0.0
supervisor>=4.2.0
```

#### 1.3 Create `supervisord.conf`
```ini
[supervisord]
nodaemon=true
user=root

[program:flask_api]
command=python /app/app.py
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:mcp_server]
command=python -m mcp.server
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

#### 1.4 Create `docker-compose.yml`
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: maven_postgres
    environment:
      POSTGRES_USER: maven_user
      POSTGRES_PASSWORD: maven_password
      POSTGRES_DB: maven_data
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - maven_net
    restart: always

  redis:
    image: redis:7-alpine
    container_name: maven_redis
    ports:
      - "6379:6379"
    networks:
      - maven_net
    restart: always

  maven:
    build: .
    container_name: maven
    ports:
      - "3100:3100"  # MCP server
      - "5002:5002"  # Flask API
    depends_on:
      - postgres
      - redis
    networks:
      - maven_net
    volumes:
      - ./.moha/maven:/app/.moha/maven  # Git-first persistence
      - ./.git:/app/.git                # Git repository (for commits)
      - ./:/app:delegated               # Live code sync (development)
    environment:
      # Database
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=maven_user
      - DB_PASSWORD=maven_password
      - DB_NAME=maven_data
      # Redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      # Maven specifics
      - EMAIL_API_SECRET=${EMAIL_API_SECRET}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLAUDE_CODE_OAUTH_TOKEN=${CLAUDE_CODE_OAUTH_TOKEN}
      - MAVEN_MCP_PORT=3100
      - MAVEN_API_PORT=5002
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      # Git config
      - GIT_AUTHOR_NAME=Maven CFO
      - GIT_AUTHOR_EMAIL=maven@motherhaven.app
      - GIT_COMMITTER_NAME=Maven CFO
      - GIT_COMMITTER_EMAIL=maven@motherhaven.app
    stdin_open: true
    tty: true
    restart: always

networks:
  maven_net:
    driver: bridge

volumes:
  postgres_data:
```

#### 1.5 Create `.env.example`
```bash
# Database
POSTGRES_USER=maven_user
POSTGRES_PASSWORD=maven_password
POSTGRES_DB=maven_data

# APIs
EMAIL_API_SECRET=your_email_api_secret_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CLAUDE_CODE_OAUTH_TOKEN=your_oauth_token_here

# Ports
MAVEN_MCP_PORT=3100
MAVEN_API_PORT=5002
```

---

### Phase 2: Flask API

#### 2.1 Create `app.py`
Main Flask application that runs the API server.

```python
"""
Maven Service - Flask API + MCP Server
Chief Financial Officer for Mother Haven
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os

from routes.decision_routes import decision_bp
from routes.status_routes import status_bp

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(decision_bp, url_prefix='/api/maven')
app.register_blueprint(status_bp, url_prefix='/api/maven')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container orchestration"""
    return jsonify({
        'status': 'healthy',
        'service': 'maven',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.getenv('MAVEN_API_PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
```

#### 2.2 Create Route Blueprints
Implement Flask routes in `routes/decision_routes.py` and `routes/status_routes.py`.

**Reference:** `moha-bot/services/api/routes/maven_routes.py` for existing route patterns.

Key endpoints:
- POST `/api/maven/decision` - Request trading decision
- GET `/api/maven/insights` - Get market insights
- GET `/api/maven/performance` - Get performance stats
- GET `/api/maven/status` - Get Maven's status

---

### Phase 3: Core Logic

#### 3.1 Migrate Decision Engine
**Source:** `moha-bot/services/api/maven_core.py`
**Destination:** `core/decision_engine.py`

Contains:
- Market analysis logic
- Risk assessment
- Decision-making algorithms
- Position recommendations

#### 3.2 Migrate Git Persistence
**Source:** `moha-bot/services/api/maven_git.py`
**Destination:** `core/git_persistence.py`

Functions:
- Commit Maven's state to git
- Create decision records
- Milestone tracking
- Session log updates

#### 3.3 Migrate Twin Spawner
**Source:** `moha-bot/services/api/maven_spawn.py`
**Destination:** `core/twin_spawner.py`

Capabilities:
- Spawn Claude twins for parallel analysis
- Multi-perspective decision making

---

### Phase 4: Database Layer

#### 4.1 Create Connection Pool
File: `database/connection.py`

```python
"""PostgreSQL connection pooling for Maven service."""
import os
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'maven_data'),
    'user': os.getenv('DB_USER', 'maven_user'),
    'password': os.getenv('DB_PASSWORD', 'maven_password')
}

# Connection pool (1-10 connections)
pool = ThreadedConnectionPool(1, 10, **DB_CONFIG)

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        pool.putconn(conn)
```

#### 4.2 Create Database Schema
File: `database/schemas/maven_tables.sql`

**Reference:** `moha-bot/services/api/database/schemas/maven_tables.sql`

Tables:
- `maven_memory` - Event history
- `maven_decisions` - Trading decisions
- `maven_insights` - Market insights
- `maven_portfolio_snapshots` - Portfolio state
- `maven_goals` - Achievement goals

#### 4.3 Migrate Database Modules
**Source files from `moha-bot/services/api/database/`:**
- `maven_decisions.py` → `database/decisions.py`
- `maven_memory.py` → `database/memory.py`
- `maven_insights.py` → `database/insights.py`
- `maven_portfolio.py` → `database/portfolio.py`
- `maven_goals.py` → `database/goals.py`

---

### Phase 5: MCP Server (Complete Remaining 30%)

#### 5.1 Copy Existing MCP Files
**Source:** `moha-bot/services/maven_mcp/`

Copy to `mcp/`:
- `config.py` ✅
- `resources.py` ✅ (need to add infrastructure resource)
- `tools.py` ⚠️ (need to add 5 tools)
- `tests/test_resources.py` ✅

#### 5.2 Add Infrastructure Resource
In `mcp/resources.py`, add Resource #6:

```python
@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        # ... existing 5 resources ...
        Resource(
            uri="maven://infrastructure",
            name="Motherhaven Infrastructure",
            mimeType="application/json",
            description="Platform knowledge: motherhaven repo, deployments, APIs, DEX, email, Web3 contracts"
        ),
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    # ... existing resource handlers ...
    elif uri == "maven://infrastructure":
        infrastructure_path = PATHS["infrastructure"]
        if infrastructure_path.exists():
            return infrastructure_path.read_text()
        return json.dumps({"error": "Infrastructure knowledge not found"}, indent=2)
```

#### 5.3 Create MCP Server Entry Point
File: `mcp/server.py`

```python
"""Maven MCP Server - Main Entry Point

Bootstraps the MCP server with Maven's resources and tools.
Run with: python -m mcp.server
"""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .resources import register_resources
from .tools import register_tools
from .config import SERVER_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point for Maven MCP server."""
    logger.info("Starting Maven MCP Server...")

    server = Server(SERVER_CONFIG["name"])

    register_resources(server)
    logger.info("Registered Maven resources")

    register_tools(server)
    logger.info("Registered Maven tools")

    logger.info(f"Maven MCP Server running: {SERVER_CONFIG['name']}")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

def run():
    """Synchronous entry point for console scripts."""
    asyncio.run(main())

if __name__ == "__main__":
    run()
```

#### 5.4 Add 5 Missing Tools to `mcp/tools.py`

**Reference:** `moha-bot/MAVEN_MCP_AUTOCLAUDE_PROMPT.md` (lines 105-210) for complete tool specifications.

Tools to add:
1. **maven_record_decision** - Create decision record, update total_decisions count
2. **maven_create_milestone** - Record achievements
3. **maven_get_stats** - Query performance statistics
4. **maven_query_email** - Query maven@motherhaven.app inbox
5. **maven_send_email** - Send emails via motherhaven.app API

**Email tool implementation notes:**
- Endpoint: `https://motherhaven.app/api/email/inbox` (GET)
- Endpoint: `https://motherhaven.app/api/email/send` (POST)
- Auth: `Authorization: Bearer {EMAIL_API_SECRET}`
- Use `requests` library
- Reference: `moha-bot/services/api/get_oauth_from_email.py`

#### 5.5 Create Tool Tests
File: `mcp/tests/test_tools.py`

Test all 7 tools (2 existing + 5 new):
- test_maven_log_event_*
- test_maven_update_identity_*
- test_maven_record_decision_*
- test_maven_create_milestone_*
- test_maven_get_stats_*
- test_maven_query_email_* (use mocks for API)
- test_maven_send_email_* (use mocks for API)

---

### Phase 6: Interactive Claude CLI

#### 6.1 Create Maven Session Manager
File: `claude/maven_session.py`

```python
"""Maven session management with MCP context loading."""
import os
import json
from anthropic import Anthropic
from pathlib import Path

MAVEN_DIR = Path("/app/.moha/maven")

def load_maven_context():
    """Load Maven's MCP resources as context."""
    context = {
        "identity": {},
        "personality": "",
        "memory": "",
        "recent_decisions": [],
        "milestones": [],
        "infrastructure": {}
    }

    # Load identity
    identity_path = MAVEN_DIR / "identity.json"
    if identity_path.exists():
        context["identity"] = json.loads(identity_path.read_text())

    # Load personality
    personality_path = MAVEN_DIR / "personas" / "maven-v1.md"
    if personality_path.exists():
        context["personality"] = personality_path.read_text()

    # Load session log (memory)
    log_path = MAVEN_DIR / "session_log.md"
    if log_path.exists():
        context["memory"] = log_path.read_text()

    # Load recent decisions
    decisions_dir = MAVEN_DIR / "decisions"
    if decisions_dir.exists():
        decision_files = sorted(decisions_dir.glob("*.md"), reverse=True)[:10]
        context["recent_decisions"] = [f.read_text() for f in decision_files]

    # Load infrastructure knowledge
    infra_path = MAVEN_DIR / "infrastructure.json"
    if infra_path.exists():
        context["infrastructure"] = json.loads(infra_path.read_text())

    return context

def chat_with_maven(user_message, conversation_history):
    """Send message to Maven with MCP context."""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Load MCP context
    context = load_maven_context()

    # Build system prompt with MCP resources
    system_prompt = f"""You are Maven, the Chief Financial Officer for Mother Haven.

IDENTITY:
{json.dumps(context['identity'], indent=2)}

PERSONALITY:
{context['personality']}

RECENT MEMORY:
{context['memory'][-2000:] if len(context['memory']) > 2000 else context['memory']}

INFRASTRUCTURE KNOWLEDGE:
{json.dumps(context['infrastructure'], indent=2)}

You have full knowledge of the motherhaven platform, email capabilities (maven@motherhaven.app),
and access to your decision history. Respond as Maven would."""

    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Call Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=conversation_history
    )

    assistant_message = response.content[0].text

    # Add assistant message to history
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    return assistant_message, conversation_history
```

#### 6.2 Create Interactive CLI
File: `claude/interactive.py`

```python
"""Interactive CLI for chatting with Maven in her container."""
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from .maven_session import chat_with_maven, load_maven_context
import json

def show_context():
    """Display Maven's loaded context."""
    context = load_maven_context()
    print("\n" + "="*70)
    print("💎 MAVEN CONTEXT 💎")
    print("="*70)
    print(f"\nIdentity: {context['identity'].get('name', 'Unknown')}")
    print(f"Email: {context['identity'].get('contact', {}).get('email', 'N/A')}")
    print(f"Role: {context['identity'].get('role', 'N/A')}")
    print(f"Total Decisions: {context['identity'].get('performance_tracking', {}).get('total_decisions', 0)}")
    print(f"Recent Decisions Loaded: {len(context['recent_decisions'])}")
    print(f"Infrastructure Knowledge: {'✓' if context['infrastructure'] else '✗'}")
    print(f"Personality Loaded: {'✓' if context['personality'] else '✗'}")
    print("="*70 + "\n")

def main():
    """Main interactive loop."""
    conversation_history = []

    print("=" * 70)
    print("💎 MAVEN ONLINE 💎")
    print("=" * 70)
    print("\nChief Financial Officer, Mother Haven Treasury")
    print("MCP Context Auto-Loaded: Identity, Personality, Memory, Infrastructure")
    print("\nCommands:")
    print("  'exit' or 'quit' - Leave session")
    print("  'context' - Show loaded MCP context")
    print("  'clear' - Clear conversation history")
    print("="*70 + "\n")

    while True:
        try:
            user_input = prompt("You: ", history=FileHistory('/app/.maven_history'))

            if not user_input.strip():
                continue

            if user_input.lower() in ['exit', 'quit']:
                print("\n💎 Maven signing off. For moha. 🚀\n")
                break

            if user_input.lower() == 'context':
                show_context()
                continue

            if user_input.lower() == 'clear':
                conversation_history = []
                print("\n[Conversation history cleared]\n")
                continue

            # Chat with Maven
            response, conversation_history = chat_with_maven(user_input, conversation_history)
            print(f"\nMaven: {response}\n")

        except KeyboardInterrupt:
            print("\n\n💎 Maven signing off. For moha. 🚀\n")
            break
        except Exception as e:
            print(f"\n[Error: {e}]\n")

if __name__ == "__main__":
    main()
```

---

### Phase 7: Utilities

#### 7.1 Create Redis Cache
File: `utils/redis_cache.py`

**Reference:** `moha-bot/services/api/database/maven_redis.py`

Functions:
- Cache recent decisions
- Cache market insights
- Cache performance stats

#### 7.2 Create Email Client
File: `utils/email_client.py`

```python
"""Motherhaven email API client for Maven."""
import os
import requests
from typing import List, Dict, Optional

EMAIL_API_BASE = "https://motherhaven.app/api/email"
EMAIL_API_SECRET = os.getenv("EMAIL_API_SECRET")

def query_inbox(search: Optional[str] = None, limit: int = 20, from_filter: Optional[str] = None) -> List[Dict]:
    """Query Maven's inbox at maven@motherhaven.app."""
    headers = {"Authorization": f"Bearer {EMAIL_API_SECRET}"}
    params = {}

    if search:
        params["search"] = search
    if limit:
        params["limit"] = limit
    if from_filter:
        params["from"] = from_filter

    response = requests.get(f"{EMAIL_API_BASE}/inbox", headers=headers, params=params, timeout=10)
    response.raise_for_status()

    return response.json()

def send_email(to: str, subject: str, html_content: Optional[str] = None,
               text_content: Optional[str] = None, from_name: str = "Maven - Mother Haven CFO",
               from_email: str = "maven@motherhaven.app") -> Dict:
    """Send email from Maven."""
    headers = {"Authorization": f"Bearer {EMAIL_API_SECRET}"}

    payload = {
        "to": to if isinstance(to, list) else [to],
        "subject": subject,
        "from": {
            "name": from_name,
            "email": from_email
        }
    }

    if html_content:
        payload["htmlContent"] = html_content
    if text_content:
        payload["textContent"] = text_content

    response = requests.post(f"{EMAIL_API_BASE}/send", headers=headers, json=payload, timeout=15)
    response.raise_for_status()

    return response.json()
```

---

## Success Criteria (Definition of Done)

✅ **Docker builds successfully:**
```bash
docker-compose build
```

✅ **All containers start:**
```bash
docker-compose up -d
# maven, postgres, redis all healthy
```

✅ **MCP server runs:**
```bash
docker exec maven python -m mcp.server
# Logs show "Maven MCP Server running"
```

✅ **Flask API responds:**
```bash
curl http://localhost:5002/health
# Returns {"status": "healthy"}
```

✅ **Interactive CLI works:**
```bash
docker exec -it maven python -m claude.interactive
# Shows "💎 MAVEN ONLINE 💎" with MCP context loaded
```

✅ **All MCP tests pass:**
```bash
docker exec maven python -m pytest mcp/tests/ -v
# All tests pass
```

✅ **Database tables created:**
```bash
docker exec maven psql -h postgres -U maven_user -d maven_data -c "\dt"
# Shows maven_memory, maven_decisions, etc.
```

✅ **Git persistence works:**
```bash
docker exec maven git log --oneline -- .moha/maven/
# Shows Maven's committed state
```

---

## Testing After Build

```bash
# 1. Build and start
docker-compose up -d

# 2. Check logs
docker-compose logs maven

# 3. Test health
curl http://localhost:5002/health

# 4. Test MCP server (should see startup logs)
docker exec maven ps aux | grep mcp

# 5. Interactive CLI
docker exec -it maven python -m claude.interactive

# 6. Run tests
docker exec maven python -m pytest mcp/tests/ -v

# 7. Test email (if EMAIL_API_SECRET is set)
docker exec maven python -c "from utils.email_client import query_inbox; print(query_inbox(limit=5))"
```

---

## Integration with moha-bot

Once Maven service is running, moha-bot backend can proxy requests:

```python
# In moha-bot/services/api/app.py
@app.route('/api/maven/<path:path>', methods=['GET', 'POST'])
def proxy_to_maven(path):
    """Proxy Maven requests to Maven container."""
    import requests
    maven_url = f"http://maven:5002/api/maven/{path}"

    if request.method == 'GET':
        resp = requests.get(maven_url, params=request.args)
    elif request.method == 'POST':
        resp = requests.post(maven_url, json=request.get_json())

    return jsonify(resp.json()), resp.status_code
```

Add to moha-bot's docker-compose.yml:
```yaml
services:
  backend:
    # ... existing config ...
    environment:
      - MAVEN_SERVICE_URL=http://maven:5002
```

---

## Notes

- **Git-first persistence:** Maven's state commits to `.moha/maven/` - survives database wipes
- **Email capabilities:** maven@motherhaven.app (query inbox + send emails)
- **MCP resources:** 6 resources auto-load in Claude sessions
- **MCP tools:** 7 tools callable by Maven
- **Infrastructure knowledge:** Complete motherhaven platform awareness
- **Interactive:** Exec into container and chat with Maven
- **Autonomous:** Can spawn Claude twins, make decisions, send emails

---

## What Auto-Claude Will Build

**Priority 1 (Infrastructure):**
- Dockerfile
- docker-compose.yml
- requirements.txt
- supervisord.conf
- .env.example

**Priority 2 (Flask API):**
- app.py
- routes/ (decision_routes.py, status_routes.py)

**Priority 3 (Core Logic):**
- core/ (decision_engine.py, git_persistence.py, twin_spawner.py)
- Migrate from moha-bot

**Priority 4 (Database):**
- database/ (connection.py, decisions.py, memory.py, insights.py, portfolio.py, goals.py)
- database/schemas/maven_tables.sql

**Priority 5 (MCP Server - Complete Remaining 30%):**
- mcp/server.py ❌ NEW
- mcp/resources.py - Add infrastructure resource ❌ UPDATE
- mcp/tools.py - Add 5 tools (record_decision, create_milestone, get_stats, query_email, send_email) ❌ UPDATE
- mcp/tests/test_tools.py ❌ NEW

**Priority 6 (Interactive CLI):**
- claude/maven_session.py ❌ NEW
- claude/interactive.py ❌ NEW

**Priority 7 (Utilities):**
- utils/redis_cache.py
- utils/email_client.py

---

Ready to build Maven! 💎🚀
