# Hyperliquid Trading Setup (CRITICAL - READ THIS FIRST)

**Last Updated:** 2026-01-18  
**Status:** WORKING ✅

## The Setup That Works

### Environment Variables (.env.local)
```bash
# TESTNET Agent (0x6fEB...6d7f)
HYPERLIQUID_WALLET_PRIVATE_KEY=0x57e0b10250fee46cd59de95356d06e2b1c2148f43d97e5781ff30b737219518a

# Treasury address (for queries ONLY)
HYPERLIQUID_WATCHED_ADDRESS=0xd85327505Ab915AB0C1aa5bC6768bF4002732258

# DO NOT SET HYPERLIQUID_ACCOUNT_ADDRESS (disables vault mode)
```

### How It Works
- **Agent Wallet** (`0x6fEB...6d7f`): Signs transactions, has $0 balance
- **Treasury** (`0xd853...2258`): Has the funds ($1,109 testnet, $235 mainnet)
- **Agent trades Treasury's balance** via Hyperliquid agent permissions
- Agent permissions configured on **Hyperliquid UI**, not via env vars

### Wallets
| Wallet | Address | Network | Balance | Purpose |
|--------|---------|---------|---------|---------|
| Treasury | `0xd853...2258` | Both | $1,109 (test) / $235 (main) | Has the money |
| Agent (testnet) | `0x6fEB...6d7f` | Testnet | $0 | Signs trades for treasury |
| Agent (mainnet) | `0xFE0d...d7A1` (Moker) | Mainnet | $0 | Signs trades for treasury |

### First Successful Trade
```
Date: 2026-01-18
Network: Testnet
Order: BUY 0.00012 BTC @ $95,400
Value: $11.45
Order ID: 46785355190
Status: FILLED ✅
```

## Critical Rules
1. ❌ **NEVER** set `HYPERLIQUID_ACCOUNT_ADDRESS` - it triggers vault mode which fails
2. ✅ **ALWAYS** use just `HYPERLIQUID_WALLET_PRIVATE_KEY` for the agent
3. ✅ **ALWAYS** set `HYPERLIQUID_WATCHED_ADDRESS` for balance queries
4. ⚠️  Minimum order size: **$10** (Hyperliquid requirement)

## Testing
```bash
# Check balance (treasury)
curl http://localhost:5001/api/account/balance?network=testnet

# Execute trade (via agent)
curl -X POST http://localhost:5001/api/trade/market \
  -H "Content-Type: application/json" \
  -d '{"coin":"BTC","side":"buy","size":0.00012,"leverage":2,"network":"testnet"}'
```

---
*This was painful to figure out. Don't forget it again.* - Maven
