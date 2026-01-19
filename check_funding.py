import json
import urllib.request
from datetime import datetime, timezone

# Get funding history
req = urllib.request.Request(
    'https://api.hyperliquid.xyz/info',
    data=json.dumps({'type': 'userFunding', 'user': '0xd85327505Ab915AB0C1aa5bC6768bF4002732258'}).encode(),
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
data = json.load(resp)

print('=== ACTUAL FUNDING PAYMENTS ===')
print('Time (UTC)           | USDC Received | Rate       | Size')
print('-' * 65)

total = 0
for entry in data[:10]:
    ts = entry['time']
    delta = entry['delta']
    if delta['coin'] != 'BERA':
        continue
    usdc = float(delta['usdc'])
    rate = float(delta['fundingRate'])
    size = float(delta['szi'])
    coin = delta['coin']

    dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
    time_str = dt.strftime('%Y-%m-%d %H:%M')

    total += usdc
    print(f'{time_str} | ${usdc:>12.6f} | {rate*100:>+.4f}% | {size:.1f} {coin}')

print('-' * 65)
print(f'Total BERA funding: ${total:.2f}')
print()

# Get current market data
req2 = urllib.request.Request(
    'https://api.hyperliquid.xyz/info',
    data=json.dumps({'type': 'metaAndAssetCtxs'}).encode(),
    headers={'Content-Type': 'application/json'}
)
resp2 = urllib.request.urlopen(req2)
market_data = json.load(resp2)
for i, asset in enumerate(market_data[0]['universe']):
    if asset['name'] == 'BERA':
        price = float(market_data[1][i]['markPx'])
        api_funding = float(market_data[1][i]['funding'])
        break

# Use most recent BERA payment for verification
for entry in data:
    if entry['delta']['coin'] == 'BERA':
        sample = entry['delta']
        break

usdc = float(sample['usdc'])
rate = float(sample['fundingRate'])
size = float(sample['szi'])

print('=== KEY QUESTION: What is the rate in the payment record? ===')
print(f'Payment received: ${usdc:.6f}')
print(f'Rate in payment: {rate*100:.4f}%')
print(f'Position size: {size} BERA')
print(f'Price ~${price:.4f}')
print(f'Notional: ${size * price:.2f}')
print()
print('=== BACK-CALCULATING THE RATE ===')
notional = size * price
implied_rate = usdc / notional
print(f'Implied rate from payment: ${usdc:.4f} / ${notional:.2f} = {implied_rate*100:.4f}%')
print(f'Rate in payment record:                                = {rate*100:.4f}%')
print(f'API funding field:                                     = {api_funding*100:.4f}%')
print()
print('=== CONCLUSION ===')
if abs(implied_rate - abs(rate)) < 0.0001:
    print('Payment rate IS the hourly rate (matches payment amount)')
if abs(implied_rate - abs(api_funding)) < 0.0001:
    print('API rate IS the hourly rate')
if abs(implied_rate - abs(api_funding)/8) < 0.0001:
    print('API rate is 8h rate, payment is 1/8th')
print()
print(f'For APR calculation:')
print(f'  If API is hourly:  {abs(api_funding) * 24 * 365 * 100:.1f}% APR')
print(f'  If API is 8h rate: {abs(api_funding) * 3 * 365 * 100:.1f}% APR')
