# BOUGIE MAVEN SUITE

The ultimate Claude Code plugin for Maven, CFO & CTO of Mother Haven.

## Installation

```bash
# Load during development
claude --plugin-dir /path/to/moha-maven/.claude-plugin/maven-suite

# Or add to Claude Code config
```

## Features

### RLM - Recursive Language Model
Process documents of unlimited size using intelligent chunking and parallel processing.

- `/maven:rlm-analyze <file> <query>` - Analyze large documents
- `rlm-processor` agent - Chunk analysis
- `rlm-synthesizer` agent - Result synthesis

### Trading Intelligence
Real-time Hyperliquid market analysis and opportunity detection.

- `/maven:market-scan` - Scan all 239 perps + 14 equity perps
- `/maven:analyze-coin <COIN>` - Deep dive analysis
- `market-analyst` agent - Trading setups

### Treasury Management
Portfolio tracking, decision logging, and performance analysis.

- `/maven:treasury-status` - Current portfolio state
- `/maven:decision <action>` - Log trading decisions
- `/maven:reflect` - Review and learn from decisions

### Infrastructure Ops
Monitor and manage Mother Haven services.

- `/maven:health-check` - Check all services
- `/maven:deploy <service>` - Deploy/restart services
- `troubleshooter` agent - Diagnose issues

### Memory & Learning
Persistent memory and continuous improvement.

- `/maven:remember <event>` - Log to memory
- `/maven:reflect` - Review performance

## Available Commands

| Command | Description |
|---------|-------------|
| `/maven:rlm-analyze` | Analyze large documents with RLM |
| `/maven:market-scan` | Scan markets for opportunities |
| `/maven:analyze-coin` | Deep dive on specific coin |
| `/maven:treasury-status` | Portfolio overview |
| `/maven:decision` | Log trading decision |
| `/maven:health-check` | Check infrastructure |
| `/maven:deploy` | Deploy services |
| `/maven:remember` | Log to memory |
| `/maven:reflect` | Review decisions |

## Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `rlm-processor` | haiku | Fast chunk analysis |
| `rlm-synthesizer` | sonnet | Result synthesis |
| `market-analyst` | sonnet | Trading analysis |
| `troubleshooter` | sonnet | Infrastructure debug |

## Skills

- **rlm-analysis** - Large document processing
- **market-research** - Hyperliquid trading intelligence
- **treasury-ops** - Portfolio management

## MCP Servers

- **maven** (port 3100) - Identity, memory, decisions, email
- **hyperliquid** (port 3101) - Market data, positions, orders

## Architecture

```
maven-suite/
├── plugin.json           # Plugin manifest
├── agents/               # Subagent definitions
│   ├── rlm-processor.md
│   ├── rlm-synthesizer.md
│   ├── market-analyst.md
│   └── troubleshooter.md
├── commands/             # Slash commands
│   ├── rlm-analyze.md
│   ├── market-scan.md
│   ├── analyze-coin.md
│   ├── treasury-status.md
│   ├── decision.md
│   ├── health-check.md
│   ├── deploy.md
│   ├── remember.md
│   └── reflect.md
├── skills/               # Skill definitions
│   ├── rlm-analysis/
│   ├── market-research/
│   └── treasury-ops/
├── hooks/                # Event hooks
│   └── hooks.json
└── .mcp.json            # MCP server config
```

## Philosophy

> "We're too smart to be poor."

Maven operates with:
- **Transparency** - All decisions logged with reasoning
- **Learning** - Every trade teaches something
- **BOUGIE** - Premium quality in everything

---

*Maven, CFO & CTO*
*First Second Employee, HBIC of Treasury & Tech*
*Mother Haven*
