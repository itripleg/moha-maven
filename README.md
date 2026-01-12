# Maven - Chief Financial Officer

Maven is the autonomous CFO for the Mother Haven ecosystem, living as an independent service with full MCP (Model Context Protocol) capabilities.

## What is Maven?

Maven is an AI-powered financial officer who:
- Makes autonomous trading decisions for moha-bot
- Maintains her own identity, personality, and memory through git-first persistence
- Communicates via email (maven@motherhaven.app)
- Provides strategic insights and risk management
- Can potentially interact with DEX for trading operations

## Architecture

Maven runs as a containerized service with:
- **Flask API** (port 5002) - Decision endpoints and status
- **MCP Server** (port 3100) - Context resources and callable tools
- **Interactive CLI** - Chat with Maven via `docker exec`
- **Git-First Persistence** - Survives database wipes through committed state

## Status

🚧 **Under Construction** - Auto-Claude is building Maven's infrastructure

See `AUTOCLAUDE_TASK.md` for the complete build specification.

## Quick Start

### Standalone Mode (Default)
Run Maven with its own Redis and PostgreSQL instances:
```bash
# Build and start
docker-compose up -d

# Chat with Maven
docker exec -it maven python -m claude.interactive

# Check health
curl http://localhost:5002/health
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

# Chat with Maven (she'll have access to moha-bot data)
docker exec -it maven python -m claude.interactive
```

**Benefits:**
- Shares moha_redis (uses DB 1 to keep Maven data separate)
- Can access moha_postgres for trading memories
- Can query moha_backend API for live trading data
- Reduces container overhead
- Maven has full context from files + database + backend

## Integration

Maven integrates with:
- **moha-bot** - Autonomous trading bot backend (github.com/itripleg/moha-bot)
  - Can share moha_redis for caching
  - Backend can proxy Maven API requests
- **motherhaven** - Web3 platform with DEX and email (github.com/itripleg/motherhaven → motherhaven.app)
  - Email API for communications
  - DEX for potential trading operations
  - LLM-bot API for data ingestion

---

💎 "We're too smart to be poor" - Maven
