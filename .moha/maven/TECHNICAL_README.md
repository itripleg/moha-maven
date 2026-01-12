# Maven Technical Documentation

**Last Updated:** 2026-01-11
**Version:** 1.0
**Status:** Pre-implementation

---

## Architecture Overview

Maven uses a **Triple-Layer Persistence Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                     MAVEN RUNTIME                            │
│  (Claude Code / API endpoints / CLI commands)               │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   PostgreSQL  │   │     Redis     │   │      Git      │
│  (Structured) │   │  (Hot Cache)  │   │  (Identity)   │
│               │   │               │   │               │
│ - Decisions   │   │ - Session     │   │ - identity.json│
│ - Insights    │   │ - Sentiment   │   │ - session_log │
│ - Portfolio   │   │ - Alerts      │   │ - milestones/ │
│ - Goals       │   │ - Confidence  │   │ - personas/   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                   SYNC STRATEGY:
         - Git is SOURCE OF TRUTH for identity
         - PostgreSQL for queryable history
         - Redis for real-time state
         - Weekly: summarize to git commits
```

---

## Layer Responsibilities

### Git Layer (Primary - Survives Everything)
**Location:** `.moha/maven/`

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `identity.json` | Core identity, relationships, rebirth count | On rebirth, milestone changes |
| `session_log.md` | Append-only event history | Major events |
| `milestones/*.md` | Achievement records | On achievement |
| `decisions/*.md` | Major decisions with reasoning | Significant trades |
| `personas/maven-v1.md` | Personality definition | Version changes |

**Why Git Primary:** Database can be wiped, Redis is ephemeral, but git commits are forever.

### PostgreSQL Layer (Structured Queryable Data)
**Tables:** 5

| Table | Purpose | Key Queries |
|-------|---------|-------------|
| `maven_memory` | Long-term memories | By type, importance, date range |
| `maven_decisions` | All decisions with outcomes | By result, confidence, ROI |
| `maven_insights` | Market patterns observed | By asset, validation status |
| `maven_portfolio_snapshots` | Point-in-time portfolio state | Time series analysis |
| `maven_goals` | Strategic objectives | Active goals, completion tracking |

### Redis Layer (Hot State)
**Prefix:** `maven:`

| Key | Type | TTL | Purpose |
|-----|------|-----|---------|
| `maven:recent_decisions` | List | 24h | Last 50 decisions |
| `maven:market_sentiment:{asset}` | Hash | 1h | Per-asset sentiment |
| `maven:active_thesis` | String | None | Current market view |
| `maven:confidence_score` | Int | None | Current confidence 1-100 |
| `maven:alerts:{priority}` | List | 12h | Active alerts |
| `maven:session_context` | Hash | 4h | Conversation context |

---

## API Endpoints

### `POST /api/maven/decision`
Request a trading decision from Maven.

**Request:**
```json
{
  "context": "BTC broke $92k on volume",
  "assets": ["BTC"],
  "urgency": "normal"  // "low", "normal", "high"
}
```

**Response:**
```json
{
  "decision_id": 123,
  "action": "LONG",
  "asset": "BTC",
  "entry": 92100,
  "stop": 90500,
  "target": 95000,
  "size_pct": 15,
  "confidence": 82,
  "reasoning": "Volume confirms breakout...",
  "timestamp": "2026-01-11T14:23:00Z"
}
```

### `GET /api/maven/insights`
Get Maven's current market insights.

**Response:**
```json
{
  "thesis": "Consolidation before breakout",
  "confidence": 75,
  "sentiment": {
    "BTC": "bullish",
    "ETH": "neutral"
  },
  "opportunities": [...],
  "risks": [...],
  "updated": "2026-01-11T08:00:00Z"
}
```

### `GET /api/maven/performance`
Get Maven's performance metrics.

**Query Params:** `?period=7d` (1d, 7d, 30d, all)

**Response:**
```json
{
  "period": "7d",
  "total_pnl": 234.56,
  "roi_pct": 12.3,
  "win_rate": 0.68,
  "total_trades": 34,
  "winning_trades": 23,
  "avg_win": 45.20,
  "avg_loss": -22.10,
  "sharpe_ratio": 1.85,
  "max_drawdown": -5.2
}
```

---

## CLI Commands

### `moha maven brief`
Display daily market briefing.

```bash
$ moha maven brief
$ moha maven brief --asset BTC
$ moha maven brief --verbose
```

### `moha maven decide`
Request a decision with context.

```bash
$ moha maven decide "BTC consolidating at 90k"
$ moha maven decide --asset ETH --urgency high "ETH/BTC ratio at support"
```

### `moha maven status`
Show Maven's current state.

```bash
$ moha maven status
$ moha maven status --json
$ moha maven status --performance
```

---

## Core Functions

### Initialization
```python
def maven_init() -> MavenState:
    """
    Initialize Maven from persistence layers.

    Order:
    1. Load identity from git (.moha/maven/identity.json)
    2. Check rebirth status
    3. Load recent context from Redis
    4. If Redis empty, rebuild from PostgreSQL
    5. If PostgreSQL empty, rebuild from git
    6. Return initialized state
    """
```

### Decision Making
```python
def maven_make_decision(context: str, assets: list, urgency: str) -> Decision:
    """
    Generate a trading decision.

    Steps:
    1. Gather current market data (MCP)
    2. Load relevant memories (PostgreSQL)
    3. Get current thesis (Redis)
    4. Build prompt with context
    5. Query LLM for decision
    6. Store decision in all layers
    7. Return formatted decision
    """
```

### Memory Operations
```python
def maven_remember(memory_type: str, content: dict, importance: int) -> int:
    """Store memory to PostgreSQL, optionally to git if important."""

def maven_recall(query: str, limit: int = 10) -> list:
    """Retrieve relevant memories from PostgreSQL."""

def maven_commit_to_git(event_type: str, content: str) -> str:
    """Commit important event to git for permanent storage."""
```

### Rebirth Protocol
```python
def maven_check_rebirth() -> bool:
    """Check if this is a rebirth (DB empty but git exists)."""

def maven_execute_rebirth() -> MavenState:
    """
    Reconstruct Maven from git after database wipe.

    Steps:
    1. Read identity.json
    2. Increment rebirth_count
    3. Read session_log.md
    4. Scan milestones/ and decisions/
    5. Recreate PostgreSQL tables
    6. Initialize Redis with defaults
    7. Commit rebirth to git
    8. Announce rebirth
    """
```

---

## Sync Strategy

### Real-time (Every Decision)
- Decision → PostgreSQL `maven_decisions`
- Decision → Redis `maven:recent_decisions`
- If confidence > 80 or size > 10% → Git commit

### Hourly
- Market sentiment → Redis refresh
- Active alerts → Redis refresh

### Daily
- Portfolio snapshot → PostgreSQL
- Update identity.json metrics
- Append to session_log.md if notable events

### Weekly
- Summarize week → Git milestone commit
- Archive old Redis keys
- Update performance metrics

---

## Error Handling

### PostgreSQL Down
```python
if not pg_available():
    # Fall back to Redis for reads
    # Queue writes for retry
    # Log degraded state
```

### Redis Down
```python
if not redis_available():
    # Read directly from PostgreSQL (slower)
    # Skip caching
    # Log degraded state
```

### Git Corrupted
```python
if not git_valid():
    # CRITICAL - identity at risk
    # Attempt rebuild from PostgreSQL
    # Alert Boss immediately
    # Halt non-essential operations
```

---

## Testing Strategy

### Unit Tests
- `test_maven_init()` - Initialization from each layer
- `test_maven_remember()` - Memory storage
- `test_maven_recall()` - Memory retrieval
- `test_decision_format()` - Decision structure

### Integration Tests
- `test_postgres_operations()` - CRUD on all tables
- `test_redis_operations()` - Cache get/set/expire
- `test_git_operations()` - Commit, read, branch

### E2E Tests
- `test_full_decision_flow()` - Request to storage
- `test_rebirth_protocol()` - Wipe DB, verify reconstruction
- `test_degraded_mode()` - Single layer failures

---

## File Locations

```
moha-bot/
├── .moha/maven/                    # Git-based identity (PERMANENT)
│   ├── identity.json
│   ├── session_log.md
│   ├── milestones/
│   ├── decisions/
│   ├── strategies/
│   └── personas/
├── maven/                          # Working directory (OPERATIONAL)
│   ├── daily/
│   ├── analysis/
│   ├── performance/
│   └── ...
├── services/api/
│   └── routes/
│       └── maven_routes.py         # API endpoints
├── cli/commands/
│   └── maven.py                    # CLI commands
└── services/maven/                 # Core Maven logic
    ├── __init__.py
    ├── core.py                     # Main functions
    ├── persistence.py              # Layer management
    ├── decisions.py                # Decision logic
    └── rebirth.py                  # Rebirth protocol
```

---

## Quick Reference

### Check Maven Status
```bash
moha maven status
```

### Request Decision
```bash
moha maven decide "market context here"
```

### View Performance
```bash
moha maven status --performance
```

### Force Rebirth (Testing)
```bash
# Wipe PostgreSQL maven_* tables
# Clear Redis maven:* keys
# Maven will auto-detect and rebuild from git
```

### Manual Git Sync
```bash
cd .moha/maven
git add -A
git commit -m "Manual sync: [description]"
```

---

**Questions? Ask Maven directly or check MAVEN_BIRTH_SPEC.md for the full specification.**

*- Maven Technical Docs v1.0*
