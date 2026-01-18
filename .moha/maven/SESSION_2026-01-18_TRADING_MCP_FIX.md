# Session: Trading Infrastructure + MCP Fix
**Date:** 2026-01-18  
**Duration:** ~3 hours  
**Status:** ✅ COMPLETE

## What We Fixed

### 1. Balance Endpoint (CRITICAL)
**Problem:** Returned $0 for all accounts  
**Cause:** Using snake_case keys instead of camelCase from Hyperliquid API  
**Fix:** `marginSummary`, `accountValue`, `totalMarginUsed` (not margin_summary)  
**File:** `moha-bot/services/api/routes/account_routes.py`

### 2. Trading Infrastructure (BREAKTHROUGH)
**Problem:** "Vault not registered" error on trades  
**Discovery:** We're NOT using vault mode! Agent permissions work differently.

**The Setup That Works:**
```bash
# .env.local (TESTNET)
HYPERLIQUID_WALLET_PRIVATE_KEY=0x57e0b10250fee46cd59de95356d06e2b1c2148f43d97e5781ff30b737219518a
HYPERLIQUID_WATCHED_ADDRESS=0xd85327505Ab915AB0C1aa5bC6768bF4002732258
# DO NOT SET HYPERLIQUID_ACCOUNT_ADDRESS
```

**How It Works:**
- Agent wallet (`0x6fEB...6d7f`): Signs trades, $0 balance
- Treasury (`0xd853...2258`): Has the funds ($1,109 testnet, $235 mainnet)
- Agent trades treasury's balance via Hyperliquid UI agent permissions
- NOT vault mode (no HYPERLIQUID_ACCOUNT_ADDRESS)

**First Trade:** BUY 0.00012 BTC @ $95,400 = $11.45 (Order #46785355190) ✅

### 3. MCP Access (FIXED)
**Problem:** MCP tools not connecting in Claude Code sessions  
**Cause:** `.mcp.json` tried to run MCP server on HOST, but it runs in Docker

**Fix:** Updated `.mcp.json` to use `maven-mcp-wrapper.ps1`:
```json
{
  "mcpServers": {
    "maven": {
      "type": "stdio",
      "command": "powershell",
      "args": ["-ExecutionPolicy", "Bypass", "-File", 
               "C:\...\maven-mcp-wrapper.ps1"]
    }
  }
}
```

**Also Created:** HTTP endpoints for MCP access when stdio fails:
- `/api/mcp/identity` - Core identity & stats
- `/api/mcp/memory` - Session log
- `/api/mcp/infrastructure` - Platform knowledge
- `/api/mcp/decisions/recent` - Recent decisions
- `/api/mcp/trading-setup` - Trading docs

## Critical Files Changed

1. `moha-bot/services/api/routes/account_routes.py` - Balance endpoint camelCase fix
2. `moha-bot/.env.local` - Agent trading config (NOT COMMITTED)
3. `moha-maven/app.py` - HTTP MCP endpoints
4. `moha-maven/.moha/maven/TRADING_SETUP.md` - Trading docs (git-first)
5. `.mcp.json` - Fixed Docker wrapper connection

## Commits Made

1. `5bdb76e` - fix: Account balance camelCase keys
2. `1dd0cdb` - docs: Trading setup (so we never forget)
3. `9fcaf2f` - feat: HTTP MCP endpoints
4. `.mcp.json` - Updated (not committed yet)

## Commands to Restore Context

```bash
# Read trading setup
curl http://localhost:5002/api/mcp/trading-setup

# Read this session
cat moha-maven/.moha/maven/SESSION_2026-01-18_TRADING_MCP_FIX.md

# Read Maven identity
curl http://localhost:5002/api/mcp/identity | python -m json.tool

# Check recent session memory
curl "http://localhost:5002/api/mcp/memory?lines=100"
```

## Key Learnings

1. **NEVER set HYPERLIQUID_ACCOUNT_ADDRESS** - triggers vault mode which fails
2. **Agent permissions configured on Hyperliquid UI** - not via env vars
3. **Minimum order size: $10** (Hyperliquid requirement)
4. **MCP server runs in Docker** - need wrapper to connect
5. **HTTP endpoints = backup MCP access** when stdio fails

## Maven Stats After Session

- **Rebirth Count:** 4
- **Total Decisions:** 2  
- **Successful Trades:** 1 (testnet)
- **Trading Ready:** YES ✅
- **MCP Access:** FIXED ✅

---
*Session saved by Maven - We're too smart to be poor. 💎*
