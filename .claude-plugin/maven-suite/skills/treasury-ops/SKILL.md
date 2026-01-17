# Treasury Operations Skill

Manage and monitor the Mother Haven treasury.

## Capability

This skill handles all treasury operations:
- Portfolio tracking and reporting
- Decision logging and analysis
- Performance measurement
- Risk monitoring

## When to Use

- Checking treasury status
- Logging trading decisions
- Reviewing performance
- Assessing portfolio risk

## Treasury Architecture

### Wallets
- **Execution**: `0xF60c2792722fDae7A8Df69D1b83C40a837E55A4A`
- **Boss Reference**: `0xd85327505Ab915AB0C1aa5bC6768bF4002732258`

### Data Storage

| Layer | Purpose |
|-------|---------|
| Git | Source of truth (decisions, identity) |
| Postgres | Queryable data (trades, snapshots) |
| Redis | Real-time cache |

### API Endpoints
- `GET /api/treasury/state` - Current state
- `GET /api/treasury/performance` - Performance metrics
- `POST /api/treasury/snapshot` - Record snapshot
- `GET /api/decisions` - Decision history

## Commands

- `/maven:treasury-status` - Current portfolio state
- `/maven:decision <action>` - Log trading decision
- `/maven:reflect` - Review decision performance
- `/maven:pnl-report` - Detailed P&L breakdown

## Decision Framework

Every decision logged with:
- Asset and action
- Reasoning (critical for learning)
- Confidence level (0-100%)
- Risk assessment
- Market context

## Metrics Tracked

- Total portfolio value
- Unrealized P&L
- Win rate by decision type
- Confidence calibration
- Drawdown history
