import json
import urllib.request

# Get BERA candles
req = urllib.request.Request(
    'https://api.hyperliquid.xyz/info',
    data=json.dumps({'type': 'candleSnapshot', 'req': {'coin': 'BERA', 'interval': '1d', 'startTime': 1765000000000, 'endTime': 1768820000000}}).encode(),
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
candles = json.load(resp)

# Find key levels
highs = [float(c['h']) for c in candles]
lows = [float(c['l']) for c in candles]
closes = [float(c['c']) for c in candles]

all_time_high = max(highs)
recent_low = min(lows[-10:])  # Last 10 days low
swing_high = max(highs[-5:])  # Last 5 days high
swing_low = min(lows[-5:])

# The big pump candle
pump_candle = candles[-3]  # 3 days ago was the big move
pump_low = float(pump_candle['l'])
pump_high = float(pump_candle['h'])

print('=== BERA KEY LEVELS ===')
print(f'All-Time High: ${all_time_high:.4f}')
print(f'Recent Swing High: ${swing_high:.4f}')
print(f'Current Price: ~${closes[-1]:.4f}')
print(f'Recent Swing Low: ${swing_low:.4f}')
print(f'Pump Candle Range: ${pump_low:.4f} - ${pump_high:.4f}')
print()

# Fib levels from swing low to ATH
swing_l = min(lows[-15:])  # Recent swing low
swing_h = all_time_high
diff = swing_h - swing_l

print('=== FIB RETRACEMENT (ATH to Recent Low) ===')
print(f'0% (ATH):     ${swing_h:.4f}')
print(f'23.6%:        ${swing_h - diff*0.236:.4f}')
print(f'38.2%:        ${swing_h - diff*0.382:.4f}')
print(f'50%:          ${swing_h - diff*0.5:.4f}')
print(f'61.8%:        ${swing_h - diff*0.618:.4f}')
print(f'100% (Low):   ${swing_l:.4f}')
print()

# Fib extensions from the recent swing
recent_swing_low = 0.54869  # Jan 14-15 low area
recent_swing_high = all_time_high
move = recent_swing_high - recent_swing_low

print('=== FIB EXTENSION (for TP targets) ===')
print(f'Swing Low:    ${recent_swing_low:.4f}')
print(f'Swing High:   ${recent_swing_high:.4f}')
print(f'1.0 (100%):   ${recent_swing_low + move:.4f}')
print(f'1.272:        ${recent_swing_low + move*1.272:.4f}')
print(f'1.618:        ${recent_swing_low + move*1.618:.4f}')
print(f'2.0:          ${recent_swing_low + move*2:.4f}')
print()

# Your entry and current TP
entry = 0.8783
current_tp = 1.0818
current_sl = 0.8013
liq = 0.7883

print('=== YOUR POSITION ===')
print(f'Entry:        ${entry:.4f}')
print(f'Current TP:   ${current_tp:.4f} (+{(current_tp/entry-1)*100:.1f}%)')
print(f'Current SL:   ${current_sl:.4f} ({(current_sl/entry-1)*100:.1f}%)')
print(f'Liquidation:  ${liq:.4f} ({(liq/entry-1)*100:.1f}%)')
print()

print('=== SUGGESTED LEVELS ===')
print(f'Conservative TP (ATH):      ${all_time_high:.4f} (+{(all_time_high/entry-1)*100:.1f}%)')
print(f'Your TP (1.272 fib ext):    ${current_tp:.4f} (+{(current_tp/entry-1)*100:.1f}%)')
print(f'Aggressive TP (1.618 ext):  ${recent_swing_low + move*1.618:.4f} (+{((recent_swing_low + move*1.618)/entry-1)*100:.1f}%)')
