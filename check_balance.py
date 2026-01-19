from hyperliquid.info import Info
info = Info(skip_ws=True)

address = '0xd85327505Ab915AB0C1aa5bC6768bF4002732258'

# Get perps state
state = info.user_state(address)
print('=== BOSS WALLET (THE TREASURY) ===')
print(f'Address: {address}')
print(f'Account Value: ${float(state["marginSummary"]["accountValue"]):,.2f}')
print(f'Withdrawable: ${float(state["withdrawable"]):,.2f}')
print(f'Total Position Value: ${float(state["marginSummary"]["totalNtlPos"]):,.2f}')
print(f'Margin Used: ${float(state["marginSummary"]["totalMarginUsed"]):,.2f}')

# Get spot state
spot = info.spot_user_state(address)
print(f'\nSpot Balances: {spot.get("balances", [])}')

# Positions
if state.get('assetPositions'):
    print('\n=== POSITIONS ===')
    for pos in state['assetPositions']:
        p = pos['position']
        print(f'{p["coin"]}: {p["szi"]} @ {p["entryPx"]} | PnL: ${float(p["unrealizedPnl"]):,.2f}')
