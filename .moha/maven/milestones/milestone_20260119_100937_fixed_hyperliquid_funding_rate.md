# Milestone: Fixed Hyperliquid Funding Rate Calculation

**Timestamp:** 2026-01-19T10:09:37.274929+00:00
**Category:** bugfix
**Significance:** Critical - was underreporting funding income by 8x

## Description

Corrected critical bug: Scanner was calculating funding APR as 8-hourly (like Binance) but Hyperliquid pays HOURLY. Fixed calculation from rate*3*365 to rate*24*365. BERA funding now correctly shows ~2,477% APR instead of ~310%. This is an 8x difference that affects all trading decisions.

## Metadata

```json
{
  "files_fixed": [
    "moha-bot/services/api/market_intelligence/funding_detector.py",
    "moha-bot/services/api/market_intelligence/universal_scanner.py"
  ],
  "old_formula": "rate * 3 * 365 * 100",
  "new_formula": "rate * 24 * 365 * 100",
  "example_bera": {
    "old_apr": 310,
    "new_apr": 2477
  }
}
```

---
*Milestone recorded by Maven*
