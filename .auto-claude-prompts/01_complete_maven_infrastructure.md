# Auto-Claude Task: Complete Maven CFO Infrastructure

## Context

Maven is the CFO AI agent for MoHa (Mother Haven), responsible for tracking trading decisions, portfolio performance, and P&L. We just built a git-first dual persistence architecture (git files + postgres) but need operational infrastructure to actually track money flow.

**Current State:**
- ✅ Git-first persistence working (.moha/maven/)
- ✅ 7 postgres tables created (maven_decisions, maven_trades, maven_portfolio_snapshots, maven_performance_metrics, maven_insights, maven_memory, maven_conversations)
- ✅ MCP server operational with 7 tools + 6 resources
- ✅ Dual-write working (tested)
- ⚠️ No trade data flowing yet
- ⚠️ No portfolio tracking
- ⚠️ Missing some MCP resources
- ⚠️ No recovery scripts

**Project Structure:**
```
moha-maven/
├── .moha/maven/           # Git persistence (source of truth)
│   ├── identity.json
│   ├── session_log.md
│   ├── decisions/
│   └── milestones/
├── maven_mcp/             # MCP server code
│   ├── server.py
│   ├── resources.py       # MCP resources
│   ├── tools.py           # MCP tools (dual persistence)
│   └── config.py
├── database/
│   ├── connection.py      # Postgres connection pool
│   ├── migrate.py         # Migration script (working)
│   └── schemas/
│       ├── maven_conversations.sql
│       └── maven_financial.sql (7 tables)
├── app.py                 # Flask API (basic)
└── docker-compose.yml     # Maven + maven_postgres + maven_redis

moha-bot/                  # MoHa trading system (separate repo)
└── data/
    └── moha_data database # Contains: bot_trades, positions, decisions, etc.
```

**Database Connections:**
- Maven postgres: `maven_postgres:5432/maven_data` (maven_user/maven_password)
- MoHa postgres: `moha_postgres:5432/moha_data` (moha_user/moha_password)
- Maven redis: `maven_redis:6379` (currently unused)
- MoHa redis: `moha_redis:6379` (used by bots)

## Objective

Build complete operational infrastructure for Maven to track money flowing through MoHa trading system.

## Tasks

### PRIORITY 1: Trade Sync Pipeline

**Goal:** Sync trade data from MoHa's bot_trades table into Maven's maven_trades table for P&L tracking.

**Requirements:**

1. **Create `database/trade_sync.py`**
   - Connect to BOTH moha_postgres and maven_postgres
   - Query bot_trades table for new trades
   - Transform to maven_trades schema
   - Handle deduplication (external_trade_id)
   - Link to maven_decisions if possible (by timestamp proximity + asset)
   - Calculate net_pnl_usd (realized_pnl - fees)
   - Log sync statistics

2. **Schema Mapping:**
   ```python
   # MoHa bot_trades schema:
   # - id, bot_id, decision_id (FK to decisions)
   # - symbol, side (buy/sell)
   # - entry_price, exit_price (nullable), size
   # - realized_pnl, fees
   # - opened_at, closed_at (nullable), status

   # Maven maven_trades schema:
   # - id, decision_id (FK to maven_decisions, nullable)
   # - external_trade_id (bot_trades.id)
   # - trade_source ('motherbot', 'worker_bot', 'simple_ta', 'manual')
   # - source_bot_id (bot_id from MoHa)
   # - asset, side (long/short), position_action (open/close)
   # - entry_price, exit_price, size_usd, size_asset, leverage
   # - realized_pnl_usd, unrealized_pnl_usd, fees_usd
   # - net_pnl_usd (generated column)
   # - status (open/closed/liquidated/cancelled)
   # - opened_at, closed_at
   ```

3. **Sync Strategy:**
   - Query: `SELECT * FROM bot_trades WHERE id > last_synced_id ORDER BY id`
   - Store last_synced_id in maven_memory or redis
   - Idempotent: check external_trade_id exists before insert
   - Handle both open and closed trades

4. **CLI Interface:**
   ```bash
   python database/trade_sync.py --mode full    # Sync all trades
   python database/trade_sync.py --mode new     # Only new trades (default)
   python database/trade_sync.py --verbose      # Detailed logging
   ```

5. **Add to docker-compose.yml as optional service:**
   ```yaml
   trade_sync:
     build: .
     command: python database/trade_sync.py --mode new --loop --interval 300
     depends_on: [maven, moha_postgres]
     networks: [maven_net]
   ```

---

### PRIORITY 2: Portfolio Snapshot Automation

**Goal:** Regular snapshots of account state from Hyperliquid for growth tracking.

**Requirements:**

1. **Create `services/portfolio_tracker.py`**
   - Use Hyperliquid API to fetch account state
   - Get: total_value, available_balance, margin_used, unrealized_pnl
   - Get open positions (asset, side, size, entry_price, unrealized_pnl)
   - Calculate margin_utilization_pct
   - Insert into maven_portfolio_snapshots
   - Calculate historical P&L (24h, 7d, 30d) by comparing snapshots

2. **Hyperliquid API Integration:**
   - Endpoint: `https://api.hyperliquid.xyz/info` (POST)
   - Request: `{"type": "clearinghouseState", "user": "<address>"}`
   - Use address from env var: `HYPERLIQUID_ADDRESS`
   - Handle rate limiting (max 100 req/min)
   - Cache in redis for 60s

3. **Snapshot Schema:**
   ```sql
   -- maven_portfolio_snapshots already exists
   INSERT INTO maven_portfolio_snapshots (
       total_value_usd, available_balance_usd, margin_used_usd,
       unrealized_pnl_usd, open_positions, position_count,
       pnl_24h, pnl_7d, pnl_30d, pnl_all_time,
       snapshot_type, snapshot_at
   ) VALUES (...)
   ```

4. **Historical P&L Calculation:**
   - Query previous snapshot from same time yesterday → pnl_24h
   - Query snapshot from 7 days ago → pnl_7d
   - Query snapshot from 30 days ago → pnl_30d
   - First snapshot → pnl_all_time

5. **CLI Interface:**
   ```bash
   python services/portfolio_tracker.py --snapshot     # Take one snapshot
   python services/portfolio_tracker.py --loop         # Continuous (every hour)
   python services/portfolio_tracker.py --interval 3600
   ```

6. **Add to docker-compose.yml:**
   ```yaml
   portfolio_tracker:
     build: .
     command: python services/portfolio_tracker.py --loop --interval 3600
     environment:
       - HYPERLIQUID_ADDRESS=${HYPERLIQUID_ADDRESS}
     depends_on: [maven]
     networks: [maven_net]
   ```

---

### PRIORITY 3: Fix Missing MCP Resources

**Goal:** Add missing MCP resources for easier Claude Code access.

**Requirements:**

1. **Update `maven_mcp/resources.py`** to add:

   **Resource: `maven://decisions/recent`**
   - List last 10 decisions from git files
   - Format: JSON array with filename, type, asset, confidence, decided_at
   - Sorted by decided_at DESC

   **Resource: `maven://performance/summary`**
   - Query maven_trades for overall stats
   - Win rate, total P&L, avg profit, avg loss
   - Asset breakdown
   - Last updated timestamp

   **Resource: `maven://portfolio/current`**
   - Latest maven_portfolio_snapshots record
   - Current value, available balance, margin used
   - Open positions count
   - 24h/7d/30d P&L

2. **Resource URIs:**
   ```python
   RESOURCES = [
       # Existing:
       "maven://identity",
       "maven://personality",
       "maven://memory",
       "maven://infrastructure",

       # New:
       "maven://decisions/recent",      # Last 10 decisions
       "maven://performance/summary",    # Overall trading stats
       "maven://portfolio/current",      # Current portfolio state
   ]
   ```

3. **Implementation Pattern:**
   ```python
   @server.resource("maven://decisions/recent")
   def get_recent_decisions() -> str:
       decisions_dir = PATHS["decisions_dir"]
       files = sorted(decisions_dir.glob("decision_*.md"),
                      key=lambda f: f.stat().st_mtime, reverse=True)[:10]
       # Parse files, extract metadata, return JSON
   ```

---

### PRIORITY 4: Recovery Scripts

**Goal:** Rebuild database from git files after database wipes.

**Requirements:**

1. **Create `database/sync_from_git.py`**
   - Read all files in .moha/maven/decisions/
   - Parse markdown to extract decision data
   - Insert into maven_decisions (with git_filename)
   - Read session_log.md and insert events into maven_memory
   - Handle duplicates (check git_filename exists)
   - Verify counts match (git files vs DB records)

2. **Decision File Parser:**
   ```python
   def parse_decision_file(filepath):
       # Parse markdown format:
       # **Timestamp:** 2026-01-14T14:24:08.034126+00:00
       # **Type:** allocation
       # **Asset:** INFRASTRUCTURE
       # **Risk Level:** low
       # **Confidence:** 98.0%
       # ## Action
       # ## Reasoning
       # ## Metadata (JSON)
       return {
           "filename": filepath.name,
           "decided_at": timestamp,
           "decision_type": type,
           "asset": asset,
           "action": action,
           "reasoning": reasoning,
           "confidence": confidence,
           "risk_level": risk_level,
           "metadata": metadata_json
       }
   ```

3. **Session Log Parser:**
   ```python
   def parse_session_log(filepath):
       # Parse format:
       # ## [2026-01-14T14:25:13.963853+00:00] EVENT_TYPE
       # Event content here
       # **Metadata:** {...}
       # ---
       return events[]
   ```

4. **CLI Interface:**
   ```bash
   python database/sync_from_git.py --verbose
   python database/sync_from_git.py --decisions-only
   python database/sync_from_git.py --events-only
   python database/sync_from_git.py --dry-run  # Show what would sync
   ```

5. **Create `database/verify_consistency.py`**
   - Count decision files in git
   - Count maven_decisions records
   - Compare git_filename references
   - Report mismatches
   - Suggest fix commands

6. **CLI Interface:**
   ```bash
   python database/verify_consistency.py
   python database/verify_consistency.py --fix  # Auto-sync mismatches
   ```

---

### PRIORITY 5: Performance Analytics

**Goal:** Calculate and store performance metrics for decision quality tracking.

**Requirements:**

1. **Create `services/performance_calculator.py`**
   - Calculate metrics for time periods (hour, day, week, month, all_time)
   - Insert into maven_performance_metrics table
   - Run on schedule (daily for day/week/month, hourly for hour)

2. **Metrics to Calculate:**
   ```python
   # From maven_trades where status='closed'
   - total_trades
   - winning_trades (realized_pnl_usd > 0)
   - losing_trades (realized_pnl_usd < 0)
   - breakeven_trades (realized_pnl_usd = 0)
   - total_pnl_usd (SUM net_pnl_usd)
   - gross_profit_usd (SUM net_pnl_usd WHERE > 0)
   - gross_loss_usd (SUM net_pnl_usd WHERE < 0)
   - total_fees_usd (SUM fees_usd)
   - win_rate_pct (generated column)
   - avg_win_usd (AVG net_pnl_usd WHERE > 0)
   - avg_loss_usd (AVG net_pnl_usd WHERE < 0)
   - profit_factor (gross_profit / abs(gross_loss))

   # Per-asset breakdown in JSONB
   asset_performance = {
       "BTC": {"trades": 10, "pnl": 125.50, "win_rate": 60},
       "ETH": {"trades": 5, "pnl": -23.00, "win_rate": 40}
   }

   # Decision quality (JOIN maven_decisions and maven_trades)
   - decisions_made
   - avg_decision_confidence
   - high_confidence_wins (confidence > 70 AND profit)
   - low_confidence_losses (confidence < 40 AND loss)
   ```

3. **CLI Interface:**
   ```bash
   python services/performance_calculator.py --period day
   python services/performance_calculator.py --period week
   python services/performance_calculator.py --period all_time
   python services/performance_calculator.py --all  # Calculate all periods
   ```

4. **Helper Functions in Database:**
   These already exist in maven_financial.sql:
   - `maven_get_current_portfolio()`
   - `maven_win_rate_by_asset()`
   - `maven_decision_performance(lookback_days)`

---

## Additional Requirements

### Error Handling
- All scripts must handle database connection failures gracefully
- Log errors to both stdout and maven_memory table
- Continue on non-fatal errors (log + skip)
- Exit code 0 = success, 1 = error

### Logging
- Use Python logging module
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- INFO level for normal operations
- WARNING for skipped items
- ERROR for failures

### Testing
After implementation, provide verification commands:
```bash
# Test trade sync
python database/trade_sync.py --dry-run

# Test portfolio snapshot
python services/portfolio_tracker.py --snapshot

# Test recovery
python database/sync_from_git.py --dry-run
python database/verify_consistency.py

# Test performance calc
python services/performance_calculator.py --period day --verbose
```

### Dependencies
Add to requirements.txt if needed:
- psycopg2 (already installed)
- redis (already installed)
- requests (already installed)
- Any others required

### Environment Variables
Add to docker-compose.yml if needed:
```yaml
environment:
  - HYPERLIQUID_ADDRESS=${HYPERLIQUID_ADDRESS}
  - MOHA_DB_HOST=moha_postgres
  - MOHA_DB_PORT=5432
  - MOHA_DB_NAME=moha_data
  - MOHA_DB_USER=moha_user
  - MOHA_DB_PASSWORD=moha_password
```

## Success Criteria

After completion, Maven should be able to:

1. ✅ Sync trades from MoHa → Maven postgres automatically
2. ✅ Take hourly portfolio snapshots from Hyperliquid
3. ✅ Access recent decisions via MCP resource
4. ✅ Rebuild database from git after wipes
5. ✅ Calculate performance metrics daily/weekly/monthly
6. ✅ Query: "What's my 7-day P&L?" → Get answer from maven_portfolio_snapshots
7. ✅ Query: "What's my BTC win rate?" → Get answer from maven_performance_metrics
8. ✅ Survive database wipes and recover fully from git

## Notes

- Git files (.moha/maven/) are ALWAYS source of truth
- Database writes are best-effort (non-fatal if fail)
- MoHa postgres is READ-ONLY from Maven's perspective
- Use connection pooling for all database access
- Cache frequently-accessed data in redis (60s TTL)
- All timestamps in UTC (ISO 8601 format)
- Amounts in USD with 2 decimal places
- Crypto amounts with 8 decimal places

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA FLOW                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Hyperliquid API                                             │
│       ↓                                                       │
│  portfolio_tracker.py → maven_portfolio_snapshots            │
│                                                               │
│  MoHa bot_trades (READ ONLY)                                 │
│       ↓                                                       │
│  trade_sync.py → maven_trades                                │
│                                                               │
│  maven_trades (closed)                                       │
│       ↓                                                       │
│  performance_calculator.py → maven_performance_metrics       │
│                                                               │
│  git (.moha/maven/)                                          │
│       ↓                                                       │
│  sync_from_git.py → maven_decisions + maven_memory           │
│                                                               │
│  MCP Resources ← maven_postgres + git files                  │
│       ↓                                                       │
│  Claude Code (queries Maven state)                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Order

1. **PRIORITY 4** first (Recovery Scripts) - needed for testing
2. **PRIORITY 3** (MCP Resources) - easy wins
3. **PRIORITY 1** (Trade Sync) - core functionality
4. **PRIORITY 2** (Portfolio Snapshots) - requires Hyperliquid API
5. **PRIORITY 5** (Performance Analytics) - requires trade data

Or do in original order if you prefer. All tasks are independent.

---

**Ready for auto-claude!** Ship it Boss. For MoHa. 💎
