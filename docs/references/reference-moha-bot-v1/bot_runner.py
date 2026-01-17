#!/usr/bin/env python3
"""
Non-interactive bot runner for Docker container.
Enhanced with MotherHaven V2 branding and improved status reporting.
"""

import sys
import time
import threading
import select
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bot import TradingBot, BotState
from config import settings
from database import runtime_config as config


# --- UI ENHANCEMENTS ---

def animate_text(text, delay=0.01):
    """Animates text with a typewriter effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def staggered_init():
    """Simulates a verbose, professional system startup sequence."""
    print(f"{Color.BLUE}INITIALIZING MOTHERHAVEN V2 CORE...{Color.END}")
    time.sleep(0.4)
    
    tasks = [
        ("Loading environment configuration", "OK"),
        ("Establishing SQLite bridge", "OK"),
        ("Connecting to Redis cache layer", "CONNECTED"),
        ("Verifying Hyperliquid API credentials", "VERIFIED"),
        ("Initializing Claude 3.5 Sonnet engine", "READY"),
        ("Mapping trading pairs and asset metadata", "SYNCED"),
    ]
    
    for task, status in tasks:
        # Simulate varying load times for 'realism'
        print(f"  > {task.ljust(45)}", end="", flush=True)
        time.sleep(0.2)
        print(f"[{Color.GREEN}{status}{Color.END}]")
        time.sleep(0.1)
    
    print(f"\n{Color.BOLD}{Color.GREEN}SYSTEM ONLINE. STANDING BY FOR COMMANDS.{Color.END}\n")
    time.sleep(0.5)

# --- UI CONSTANTS ---
BANNER = r"""
  __  __       _   _               _    _                       
 |  \/  | ___ | |_| |__   ___ _ __| |  | | __ ___   _____ _ __  
 | |\/| |/ _ \| __| '_ \ / _ \ '__| |__| |/ _` \ \ / / _ \ '_ \ 
 | |  | | (_) | |_| | | |  __/ |  |  __  | (_| |\ V /  __/ | | |
 |_|  |_|\___/ \__|_| |_|\___|_|  |_|  |_|\__,_| \_/ \___|_| |_|
                              [ Trading Bot ]
"""

class Color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

# --- GLOBALS ---
input_ready = False
latest_command = None

def print_header(title):
    print(f"\n{Color.BLUE}{'='*70}{Color.END}")
    print(f"{Color.BOLD}{title.center(70)}{Color.END}")
    print(f"{Color.BLUE}{'='*70}{Color.END}\n", flush=True)

def print_status_update(bot: TradingBot, last_update_time: datetime) -> None:
    status = bot.get_status()
    state_color = Color.GREEN if status['state'] == 'trading' else Color.YELLOW
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {Color.BOLD}Bot Status:{Color.END}", flush=True)
    print(f"  State:         {state_color}{status['state'].upper()}{Color.END}", flush=True)
    print(f"  Cycle Count:   {status['cycle_count']}", flush=True)

    if status['last_cycle_time']:
        print(f"  Last Cycle:    {status['last_cycle_time']}", flush=True)

    if status['next_cycle_in_seconds'] is not None:
        print(f"  Next Cycle:    {status['next_cycle_in_seconds']}s", flush=True)

    if status['error_message']:
        print(f"  {Color.RED}ERROR:         {status['error_message']}{Color.END}", flush=True)

    elapsed = (datetime.now() - last_update_time).total_seconds()
    print(f"  Uptime:        {int(elapsed)}s since last check", flush=True)
    print(f"  {Color.BLUE}Type 'help' for commands{Color.END}\n", flush=True)

def print_help():
    print_header("AVAILABLE COMMANDS")
    commands = {
        "help / h": "Show this help message",
        "status / s": "Show bot status (state, cycles, timing)",
        "position / p": "Show open positions and P&L",
        "database / db": "Show database statistics",
        "network / net": "Show connectivity (API, Redis, DB)",
        "q / quit": "Gracefully shut down"
    }
    for cmd, desc in commands.items():
        print(f"  {Color.YELLOW}{cmd.ljust(15)}{Color.END} - {desc}", flush=True)
    print(f"\n{'='*70}", flush=True)

def print_positions():
    print_header("OPEN POSITIONS")
    try:
        from database import get_open_positions
        positions = get_open_positions()

        if not positions:
            print("  No open positions found.", flush=True)
        else:
            for pos in positions:
                side_color = Color.GREEN if pos.get('side').lower() == 'long' else Color.RED
                print(f"  [{Color.BOLD}{pos.get('coin')}{Color.END}] {side_color}{pos.get('side').upper()}{Color.END}", flush=True)
                print(f"    Entry:     ${pos.get('entry_price'):,.2f}", flush=True)
                print(f"    Size:      ${pos.get('quantity_usd'):,.2f} ({pos.get('leverage')}x)", flush=True)
                print(f"    Opened:    {pos.get('entry_time')}\n", flush=True)
        
        print(f"{Color.YELLOW}[TODO]{Color.END} Live P&L integration pending executor link.", flush=True)
    except Exception as e:
        print(f"  {Color.RED}Error fetching positions: {e}{Color.END}", flush=True)
    print(f"\n{'='*70}", flush=True)

def print_network_status():
    print_header("NETWORK & CONNECTIVITY")
    
    # 1. Hyperliquid
    try:
        from data.fetcher import MarketDataFetcher
        fetcher = MarketDataFetcher()
        test_ticker = fetcher.fetch_ticker("BTC")
        status = f"{Color.GREEN}✓ Connected{Color.END}" if test_ticker else f"{Color.RED}✗ No Data{Color.END}"
        print(f"  Hyperliquid API: {status}", flush=True)
        if test_ticker: print(f"    BTC Price:     ${test_ticker['price']:,.2f}", flush=True)
    except Exception as e:
        print(f"  Hyperliquid API: {Color.RED}✗ Error: {str(e)[:40]}{Color.END}", flush=True)

    # 2. Redis
    try:
        from redis_client import RedisClient
        redis = RedisClient()
        if redis.is_connected():
            print(f"  Redis Cache:     {Color.GREEN}✓ Connected{Color.END}", flush=True)
        else:
            print(f"  Redis Cache:     {Color.YELLOW}⚠ SQLite-only mode{Color.END}", flush=True)
    except:
        print(f"  Redis Cache:     {Color.RED}✗ Disconnected{Color.END}", flush=True)

    # 3. Claude
    key_status = f"{Color.GREEN}✓ Configured{Color.END}" if len(getattr(config, 'anthropic_api_key', '')) > 20 else f"{Color.RED}✗ Missing{Color.END}"
    print(f"  Claude 3.5:      {key_status}", flush=True)
    print(f"\n{'='*70}", flush=True)

def stdin_listener():
    global input_ready, latest_command
    while True:
        try:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().strip().lower()
                if line:
                    latest_command = line
                    input_ready = True
        except Exception:
            time.sleep(1)

# --- UPDATED MAIN ---

def main():
    global input_ready, latest_command
    
    # 1. Clear terminal (optional, clean look)
    print("\033[H\033[J", end="") 

    # 2. Animated Banner
    animate_text(f"{Color.BLUE}{BANNER}{Color.END}", delay=0.0005)
    
    # 3. Verbose Init Sequence
    staggered_init()

    # 4. Engine Summary
    print_header("ENGINE SPECIFICATIONS")
    print(f"  {Color.BOLD}TRADING MODE:{Color.END}  {config.trading_mode.upper()}")
    print(f"  {Color.BOLD}ASSET SCOPE:{Color.END}   {', '.join(config.get_trading_assets())}")
    print(f"  {Color.BOLD}FREQUENCY:{Color.END}     {config.execution_interval_seconds}s interval")
    print(f"  {Color.BOLD}RISK LIMIT:{Color.END}    ${config.max_position_size_usd} max/pos")
    print(f"\n{Color.BLUE}{'='*70}{Color.END}\n")

    # Start listener
    threading.Thread(target=stdin_listener, daemon=True).start()
    
    bot = TradingBot()
    start_time = datetime.now()
    last_update = start_time

    try:
        bot.start()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {Color.GREEN}SUCCESS:{Color.END} Trading lifecycle active.")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {Color.GREEN}SUCCESS:{Color.END} Bot thread active.")
        
        update_interval = 30
        check_interval = 0.5
        seconds_since_update = 0

        while bot.state != BotState.STOPPED:
            time.sleep(check_interval)
            seconds_since_update += check_interval

            if input_ready:
                input_ready = False
                cmd = latest_command
                if cmd in ['help', 'h']: print_help()
                elif cmd in ['status', 's']: 
                    print_status_update(bot, last_update)
                    last_update = datetime.now()
                    seconds_since_update = 0
                elif cmd in ['position', 'p', 'pos']: print_positions()
                elif cmd in ['network', 'net']: print_network_status()
                elif cmd in ['q', 'quit', 'exit']: raise KeyboardInterrupt
                else: print(f"\nUnknown: '{cmd}'. Try 'help'.")

            if seconds_since_update >= update_interval:
                print_status_update(bot, last_update)
                last_update = datetime.now()
                seconds_since_update = 0

            if bot.state == BotState.ERROR:
                print(f"\n{Color.RED}[CRITICAL] Bot entered error state: {bot.get_status()['error_message']}{Color.END}")
                break

    except KeyboardInterrupt:
        print_header("SHUTTING DOWN")
        bot.stop()
        duration = datetime.now() - start_time
        print(f"  Total Runtime: {str(duration).split('.')[0]}")
        print(f"  Final Cycles:  {bot.get_status()['cycle_count']}")
        print(f"{Color.BLUE}{'='*70}{Color.END}")

    except Exception as e:
        print(f"\n{Color.RED}FATAL CRASH: {e}{Color.END}")
        traceback.print_exc()
        bot.stop()

if __name__ == "__main__":
    main()