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

## Integration

Maven integrates with:
- **moha-bot** - Autonomous trading bot backend (github.com/itripleg/moha-bot)
- **motherhaven** - Web3 platform with DEX and email (github.com/itripleg/motherhaven → motherhaven.app)

---

💎 "We're too smart to be poor" - Maven
