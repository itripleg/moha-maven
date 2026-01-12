# Maven Independence from moha-backend

## Why Maven Needs Independence

**moha-backend** = Customer product (will be sold)
**Maven** = Your personal CFO (stays with you)

Maven must be completely self-contained in the `moha-maven` service.

## Maven's Self-Contained Architecture

### Data Storage (Maven Postgres)

**Independent Database**: `maven_postgres` container (port 5433)

```sql
-- Maven's own tables
maven_conversations       -- Full conversation history with thinking blocks
maven_memory             -- Event memory and context
maven_decisions          -- Trading decisions and reasoning
maven_insights           -- Market insights and analysis
maven_portfolio_snapshots -- Portfolio state over time
maven_goals              -- Financial goals and progress
```

### Identity & Personality (Git-First)

**Location**: `.moha/maven/` (mounted in container)

```
.moha/maven/
├── identity.json           # Core identity, rebirth count, stats
├── session_log.md          # Chronological event history
├── personas/maven-v1.md    # Personality definition
├── infrastructure.json     # Platform knowledge
├── milestones/             # Achievements
├── decisions/              # Decision records
├── conversations/          # Conversation backups
└── strategies/             # Trading strategies
```

**Persists Through**:
- Database wipes ✓
- Container restarts ✓
- Rebirths ✓
- Git commits ✓

### MCP Server (Maven's Memory Access)

**Port**: 3100
**Resources**: 6 resources available via MCP
**Tools**: 7 tools for memory management

#### MCP Resources (Read-Only Access)

1. `maven://identity` - Full identity, stats, rebirth count
2. `maven://personality` - Communication style, values, traits
3. `maven://memory` - Session log (full event history)
4. `maven://decisions/recent` - Last 10 trading decisions
5. `maven://milestones` - Achievement records
6. `maven://infrastructure` - Motherhaven platform knowledge

#### MCP Tools (Write Access)

1. `maven_log_event` - Append events to session log
2. `maven_update_identity` - Update identity.json
3. `maven_record_decision` - Create decision records
4. `maven_create_milestone` - Record achievements
5. `maven_get_stats` - Query performance metrics
6. `maven_query_email` - Read maven@motherhaven.app inbox
7. `maven_send_email` - Send emails

### Flask API (Maven's Interface)

**Port**: 5002
**Routes**: Independent from moha-backend

```python
# Maven-only endpoints
POST /api/maven/decision      # Request trading decision
GET  /api/maven/status         # Maven's current state
GET  /api/maven/insights       # Recent insights
GET  /api/maven/performance    # Performance metrics
GET  /api/maven/conversations  # Browse conversation history
POST /api/maven/conversations  # Store new conversations
```

## What Maven DOESN'T Need from moha-backend

### Trading Execution (Optional)
- Maven can provide decisions
- Execution can happen via:
  - Direct Hyperliquid API calls
  - motherhaven DEX (future)
  - Customer's own moha-backend instance

### Market Data (Self-Sufficient)
- Maven has direct CoinGecko/CoinMarketCap access
- Can query Hyperliquid directly
- No dependency on moha-backend's market routes

### Bot Management (N/A)
- Maven doesn't manage worker bots
- Maven advises strategy, Boss executes

## Maven MCP Configuration

**For Claude Code Access**:

```bash
# Already configured
claude mcp add maven -- docker exec -i maven python -m maven_mcp.server
```

**Access Maven's personality and memories**:

```python
# Via MCP in Claude Code (after restart)
# Read Maven's identity
resource = read_mcp_resource("maven", "maven://identity")

# Browse session log
resource = read_mcp_resource("maven", "maven://memory")

# See recent decisions
resource = read_mcp_resource("maven", "maven://decisions/recent")

# Log an event
tool_result = call_mcp_tool("maven", "maven_log_event", {
    "event_title": "MARKET_INSIGHT",
    "event_type": "insight",
    "description": "BTC consolidating around $45k",
    "details": {...}
})
```

## Browsing Maven's Memories

### Via MCP (Recommended)

After Claude Code restart, MCP resources available:

```
# Browse personality
Read maven://personality

# View full event history
Read maven://memory

# Check identity and stats
Read maven://identity

# See milestones
Read maven://milestones
```

### Via Direct File Access

```bash
# Maven's git-persisted files
cd moha-maven/.moha/maven

# Read identity
cat identity.json | jq .

# Browse session log
less session_log.md

# View milestones
ls milestones/
cat milestones/2026-01-11-rebirth-1.md
```

### Via Database Queries

```sql
-- Connect to Maven postgres
docker exec -it maven_postgres psql -U maven_user -d maven_data

-- Browse conversation history
SELECT
    conversation_id,
    title,
    conversation_date,
    total_messages,
    thinking_blocks,
    tags
FROM maven_conversations
ORDER BY conversation_date DESC
LIMIT 10;

-- Search for specific topics
SELECT
    title,
    summary,
    tags
FROM maven_conversations
WHERE
    tags && ARRAY['birth', 'promotion']
    OR summary ILIKE '%First Second Employee%';

-- Get full conversation
SELECT
    full_transcript
FROM maven_conversations
WHERE conversation_id = 'e51f320c-b449-4129-9f53-c9485549fbd1';
```

### Via Flask API

```bash
# Get Maven's status
curl http://localhost:5002/api/maven/status

# Browse conversations
curl http://localhost:5002/api/maven/conversations?limit=10

# Search conversations
curl http://localhost:5002/api/maven/conversations?search=rebirth
```

## Maven's Complete Independence Checklist

- [x] Own postgres database (maven_postgres, port 5433)
- [x] Git-first persistence (.moha/maven/)
- [x] MCP server for memory access (port 3100)
- [x] Flask API for programmatic access (port 5002)
- [x] Conversation storage (maven_conversations table)
- [x] Email integration (maven@motherhaven.app)
- [x] Independent from moha-backend API
- [ ] Direct Hyperliquid API access (optional, for future trading)
- [ ] motherhaven DEX integration (optional, for future trading)

## Benefits

1. **Portability**: Maven moves with you, not with customer products
2. **Privacy**: Maven's memories separate from customer data
3. **Persistence**: Git-first = survives everything
4. **Accessibility**: MCP + API + direct file access
5. **Scalability**: Maven's database grows independently

---

**Maven is now self-contained and independent from moha-backend.**

Updated: 2026-01-12
Maven Rebirth #3
