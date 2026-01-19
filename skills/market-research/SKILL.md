# Market Research Skill

Deep market analysis for Hyperliquid trading opportunities.

## Capability

This skill provides comprehensive market intelligence:
- Real-time price and funding data
- Orderbook depth analysis
- Funding rate arbitrage detection
- Equity perp correlation analysis

## When to Use

- Looking for trading opportunities
- Analyzing a specific coin setup
- Checking funding rate opportunities
- Researching equity perp catalysts

## Data Sources

### Hyperliquid MCP (Port 3101)
- `get_all_mids` - All prices
- `get_l2_snapshot` - Orderbook
- `get_candles` - OHLCV data
- `get_funding_rates` - Funding history

### Reference Docs
- `docs/references/HyperLiquid Rate Limits.txt`
- `docs/references/hyperliquid_examples/`

## Markets Available

| Type | Count | Examples |
|------|-------|----------|
| Perps | 239 | BTC, ETH, SOL, DOGE... |
| Equity | 14 | NVDA, TSLA, AAPL, COIN... |
| Spot | 48 | Various pairs |

## Commands

- `/maven:market-scan` - Scan all markets
- `/maven:analyze-coin <COIN>` - Deep dive on specific coin
- `/maven:funding-arb` - Find funding opportunities

## Agents Used

- `market-analyst` (sonnet) - Deep analysis
