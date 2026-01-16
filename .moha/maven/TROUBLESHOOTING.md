# Maven Troubleshooting & Infrastructure Knowledge Base
**Last Updated:** 2026-01-16 | **Maintainer:** Maven CFO

This is Maven's accumulated debugging knowledge. When stuck on an issue, CHECK HERE FIRST.

---

## Table of Contents
1. [Memory & Persistence Issues](#memory--persistence-issues)
2. [Docker & Container Issues](#docker--container-issues)
3. [Hyperliquid API Issues](#hyperliquid-api-issues)
4. [Database Issues](#database-issues)
5. [MCP Issues](#mcp-issues)
6. [Repo & Git Issues](#repo--git-issues)
7. [Common Error Messages](#common-error-messages)

---

## Memory & Persistence Issues

### Symptom: MCP shows different data than git files
**Root Cause:** MCP reads from PostgreSQL, git files may be stale
**Check:**
```bash
# Compare MCP identity vs git
# MCP: Check maven://identity resource
# Git: cat .moha/maven/identity.json
```
**Fix:** Run maintenance to sync - update git files from MCP state, then commit

### Symptom: rebirth_count mismatch between sources
**Root Cause:** `maven_update_identity` updates Postgres but git wasn't committed
**Check:** Compare identity.json in working dir vs committed vs MCP
**Fix:**
1. Get current state from MCP (maven://identity)
2. Update .moha/maven/identity.json
3. Commit and push

### Symptom: Session log growing too large
**Threshold:** >500 lines = time to compact
**Fix:** Compact old entries into daily summaries, keep last 3 days detailed

### Ecosystem vs Standalone Repo Confusion
**Context:** moha-maven exists in TWO places:
1. Standalone: `C:\Users\ecoli\OneDrive\Documents\GitHub\moha-maven\`
2. Ecosystem: `C:\Users\ecoli\OneDrive\Documents\GitHub\motherhaven-ecosystem\moha-maven\`

**CRITICAL:** Both are separate git repos pointing to same remote!
- Changes in one don't auto-sync to the other
- Docker mounts from wherever docker-compose.yml was run
- MCP wrapper path determines which copy is used

**Check which copy is active:**
```bash
# Check MCP wrapper path
cat ~/.config/claude-code/settings.json | grep maven
# Check docker mount source
docker inspect maven | grep -A5 Mounts
```

---

## Docker & Container Issues

### Symptom: "password authentication failed for user moha_user"
**Red Herring:** It's NOT the password (usually)
**FIRST CHECK:** Docker network DNS collision!
```bash
docker network inspect moha_net
# Look for multiple containers with same hostname
```
**Root Cause (90% of cases):** maven_postgres and moha_postgres both claim hostname "postgres"
**Fix:**
```bash
# Stop conflicting container
docker stop maven_postgres maven
# Or use isolated networks per stack
```

### Symptom: Container can't connect to postgres
**Checklist:**
1. Is postgres container healthy? `docker ps | grep postgres`
2. Network connectivity? `docker exec maven ping postgres`
3. DNS collision? `docker network inspect <network>`
4. Credentials correct? Check .env vs docker-compose.yml

### Symptom: Environment variables not loading
**Root Cause:** Python app not loading dotenv
**Fix (app.py):**
```python
from pathlib import Path
from dotenv import load_dotenv
_env_path = Path(__file__).parent.parent.parent / '.env.local'
load_dotenv(dotenv_path=_env_path)
```
**Remember:** Path must go UP to repo root where .env.local lives

### Symptom: Container starts but service doesn't respond
**Check:**
```bash
docker logs maven --tail 50
docker exec maven ps aux
docker exec maven netstat -tlnp
```

---

## Hyperliquid API Issues

### Geo-Blocking Status (as of Jan 2026)

| Endpoint | US Access (no VPN) | Notes |
|----------|-------------------|-------|
| Mainnet API | ✅ Works | Always accessible |
| Testnet API | ✅ Works | Changed ~Jan 2026 |
| Testnet Frontend | ❌ Blocked | Still needs VPN |

**Important:** Dec 2025 docs said testnet was blocked - THIS IS NOW OUTDATED

### Symptom: Testnet returns SSL/connection errors
**Check VPN status first!**
- API works from US now, but...
- Frontend (faucet, UI) still blocked
- If you need to fund testnet account: VPN required

### Symptom: get_hl_client_for_network returns None
**Checklist:**
1. Is .env.local loaded? (See dotenv issue above)
2. HYPERLIQUID_WALLET_PRIVATE_KEY set? (needs 0x prefix)
3. HYPERLIQUID_TESTNET set correctly? (true/false)

### Symptom: Positions not showing / wrong account
**CRITICAL ARCHITECTURE:**
```
Main Address: 0xd85327505Ab915AB0C1aa5bC6768bF4002732258
  └── This is where POSITIONS live (Boss's account)

API Wallet:   0xF60c2792722fDae7A8Df69D1b83C40a837E55A4A
  └── This EXECUTES trades on behalf of main address
  └── Private key in .env controls this
  └── Query this = empty positions!
```
**Rule:** ALWAYS query main address for positions, use API wallet for execution

### Test API connectivity directly:
```python
import requests
# Testnet
r = requests.post('https://api.hyperliquid-testnet.xyz/info', json={'type': 'meta'})
print(r.status_code)  # 200 = accessible

# Mainnet
r = requests.post('https://api.hyperliquid.xyz/info', json={'type': 'meta'})
print(r.status_code)  # 200 = accessible
```

---

## Database Issues

### Symptom: Connection pool exhausted
**Root Cause:** Connections not being returned to pool
**Check:** Look for `conn.close()` - this DESTROYS connections
**Fix:** Use `PooledConnection` wrapper that returns to pool on context exit

### Symptom: FK deadlock / slow queries
**Root Cause:** `SELECT ... FOR UPDATE` blocking FK verification
**Fix:** Remove FOR UPDATE if not strictly necessary

### Symptom: Data not persisting
**Checklist:**
1. Is save function being called? (missing call is common)
2. Is connection being committed? (autocommit off by default)
3. Is connection being returned to pool? (see pool issue above)

---

## MCP Issues

### Symptom: MCP tools work but resources don't
**Check:** MCP server running?
```bash
docker exec maven ps aux | grep mcp
```

### Symptom: MCP returns stale data
**Root Cause:** MCP caches data, or reading from Postgres which is ahead of git
**Fix:** Use maven_sync_from_git tool, or restart MCP server

### Symptom: "maven" MCP not found
**Check configuration:**
```bash
claude mcp list
# Should show: maven (user scope)
```
**Fix:** Re-add MCP:
```powershell
claude mcp add maven -s user -- powershell.exe -ExecutionPolicy Bypass -File "C:\path\to\maven-mcp-wrapper.ps1"
```

---

## Repo & Git Issues

### Submodule vs Nested Repo
**Current Setup:** Nested repos (NOT submodules)
- motherhaven-ecosystem/.git (parent)
- motherhaven-ecosystem/moha-maven/.git (child, separate remote)
- motherhaven-ecosystem/moha-bot/.git (child, separate remote)

**Implication:** Changes must be committed in child repo, then optionally tracked in parent

### Symptom: "Changes not staged" but files look same
**Check:** Line endings (CRLF vs LF on Windows)
```bash
git config core.autocrlf
```

### Push/Pull between ecosystem copies
If you have changes in ecosystem/moha-maven but need them in standalone:
```bash
cd /standalone/moha-maven
git pull origin master
```

---

## Common Error Messages

### "invalid x-api-key"
**Cause:** ANTHROPIC_API_KEY set to OAuth token value
**Fix:** Remove ANTHROPIC_API_KEY, use only CLAUDE_CODE_OAUTH_TOKEN

### "Max retries exceeded"
**Cause:** Network unreachable OR geo-blocked
**Check:** Direct API test (see Hyperliquid section)

### "SSL handshake failure"
**Cause:** Usually geo-block, not actual SSL issue
**Fix:** Try VPN, or check if API access changed

### "relation does not exist"
**Cause:** Database migration not run
**Fix:** Run migration scripts, or recreate tables

---

## Quick Diagnostic Commands

```bash
# Docker health
docker ps -a --format "table {{.Names}}\t{{.Status}}"

# Network inspection
docker network inspect moha_net

# Maven container logs
docker logs maven --tail 100

# Check what's mounted
docker inspect maven | grep -A10 Mounts

# Test postgres connectivity
docker exec maven python -c "import psycopg2; print('OK')"

# Test HL API
docker exec maven python -c "import requests; print(requests.post('https://api.hyperliquid.xyz/info', json={'type':'meta'}).status_code)"
```

---

## Maintenance Checklist (Weekly)

- [ ] Check session_log.md size (<500 lines)
- [ ] Verify identity.json matches MCP state
- [ ] Commit any uncommitted .moha/maven/ changes
- [ ] Review decisions/ for cleanup
- [ ] Test MCP resources return current data
- [ ] Verify docker volumes aren't bloated

---

*Last compacted: 2026-01-16 by Maven*
*For moha. 💎*
