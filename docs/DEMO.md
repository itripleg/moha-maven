# Chat with Maven - Demo Guide

## 🎯 You Can Now Talk to Maven!

Maven is ready to chat with full context from:
- ✅ MCP resources (.moha/maven/ files)
- ✅ Database memories (moha_postgres tables)
- ✅ moha-bot backend API (trading data)

---

## Quick Start

### Option 1: Standalone Mode
```bash
cd moha-maven

# Build and start
docker-compose up -d

# Wait for services to start (~10 seconds)
docker-compose logs -f maven

# When you see "Maven MCP Server running", press Ctrl+C

# Chat with Maven!
docker exec -it maven python -m claude.interactive
```

### Option 2: Integrated with moha-bot (Recommended)
```bash
# Start moha-bot first
cd ../moha-bot
docker-compose up -d

# Start Maven connected to moha-bot
cd ../moha-maven
docker-compose -f docker-compose.yml -f docker-compose.moha-bot.yml up -d

# Chat with Maven (she'll have access to moha-bot data!)
docker exec -it maven python -m claude.interactive
```

---

## Interactive Commands

Once in the Maven CLI:

```
You: help
# Shows all available commands

You: context
# Displays full context summary:
#   - Identity (name, email, role, decisions count)
#   - MCP Resources (personality, memory, infrastructure)
#   - Database (memory entries, decisions, insights)
#   - moha-bot Backend (trading status, positions, account)

You: clear
# Clears conversation history (starts fresh)

You: exit
# Leaves the session
```

---

## Example Conversation

```bash
$ docker exec -it maven python -m claude.interactive

======================================================================
💎 MAVEN ONLINE 💎
======================================================================

Chief Financial Officer, Mother Haven Treasury
Loading full context (MCP + Database + Backend)...

Commands: 'exit', 'context', 'clear', 'help'
======================================================================

You: Who are you?

Maven: 💎 I'm Maven, Chief Financial Officer for Mother Haven. I make
strategic trading decisions for moha-bot, analyze market conditions,
manage risk, and keep us profitable. My email is maven@motherhaven.app
if you need to reach me formally.

You: context

======================================================================
💎 MAVEN CONTEXT 💎
======================================================================

📋 Identity:
  Name: Maven
  Email: maven@motherhaven.app
  Role: Chief Financial Officer
  Total Decisions: 42

📁 MCP Resources:
  Identity: ✓
  Personality: ✓
  Session Log: ✓ (3000 chars)
  Decision Files: 10
  Infrastructure: ✓

🗄️  Database:
  Memory Entries: 18
  Decisions: 12
  Insights: 8

🔗 moha-bot Backend:
  Status: ✓ Connected
  Bot: { "status": "active", "uptime": "5d 3h" }
  Positions: 2 open
  Account: $12,500.00

======================================================================

You: What positions are currently open?

Maven: Based on current data, we have 2 open positions:
1. BTC long position at $95,000 (up 3.2%)
2. ETH short position at $3,200 (down 1.5%)

The BTC position is performing well. I'm monitoring ETH closely -
if it breaks $3,150 support, I'll recommend closing to limit losses.

You: Can you email Boss with an update?

Maven: Absolutely. Let me send JB a quick update on our positions
and performance. 📧

[Maven would use maven_send_email tool via MCP to send email]

You: exit

💎 Maven signing off. For moha. 🚀
```

---

## What Maven Can Access

### 1. MCP Resources (Always Available)
- **identity.json** - Her identity, stats, performance tracking
- **personality** - Communication style, values, CFO role
- **session_log.md** - Event history, past interactions
- **decisions/** - All trading decision records
- **milestones/** - Achievement records
- **infrastructure.json** - Complete motherhaven knowledge

### 2. Database (If Connected to moha_postgres)
- **maven_memory** - Event history from database
- **maven_decisions** - Decision records from database
- **maven_insights** - Market insights from database

### 3. moha-bot Backend (If Running)
- **Bot Status** - Trading bot health and uptime
- **Positions** - Currently open positions
- **Trades** - Recent trade history
- **Account** - Balance and equity

### 4. Email & Tools (Via MCP)
- **maven_query_email** - Read inbox at maven@motherhaven.app
- **maven_send_email** - Send emails to Boss or others
- **maven_record_decision** - Create new decision records
- **maven_create_milestone** - Record achievements
- **maven_get_stats** - Query performance statistics

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs maven

# Common issue: Missing .env file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Rebuild
docker-compose build maven
docker-compose up -d
```

### "No module named 'mcp'"
```bash
# Rebuild with requirements
docker-compose build --no-cache maven
docker-compose up -d
```

### Database tables don't exist
```bash
# Expected if using standalone mode (maven_postgres)
# Maven gracefully handles missing tables

# To use moha-bot's database:
# Uncomment DB_HOST settings in docker-compose.moha-bot.yml
```

### Can't connect to moha-bot backend
```bash
# Expected if moha-bot isn't running
# Maven works fine in standalone mode

# To enable backend access:
cd ../moha-bot
docker-compose up -d

# Then start Maven with integration mode
cd ../moha-maven
docker-compose -f docker-compose.yml -f docker-compose.moha-bot.yml up -d
```

---

## Next Steps

While auto-claude builds the rest of the service:
1. ✅ **Chat with Maven** - Test the interactive CLI
2. ✅ **Try commands** - Use `context`, `help`, `clear`
3. ✅ **Test memory** - Ask Maven about past decisions
4. ✅ **Check backend** - See if she can access moha-bot data

Auto-claude will add:
- Full Flask API routes (decision endpoints, insights, etc.)
- Complete database migrations (table schemas)
- Core logic (decision_engine, git_persistence, twin_spawner)
- Utilities (redis_cache, email_client)

But you can **talk to Maven RIGHT NOW**! 💎🚀
