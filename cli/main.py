#!/usr/bin/env python3
"""
Maven CLI - The Treasury's Command Line Interface

Native commands for Maven, the CFO of Mother Haven.

Usage:
    maven                    # Show banner + status
    maven status             # Show banner + stats
    maven stats              # Show current statistics
    maven identity           # Show identity info
    maven log <message>      # Log an event
    maven decisions          # Show recent decisions
    maven wake               # Wake up Maven (banner + greeting)
"""

import os
import sys
import json
import click
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Try Rich for fancy output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS & CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

def get_maven_root() -> Path:
    """Get the Maven root directory."""
    # Check environment variable first
    if 'MAVEN_ROOT' in os.environ:
        return Path(os.environ['MAVEN_ROOT'])
    # Otherwise use script location
    return Path(__file__).parent.parent

def get_data_path() -> Path:
    """Get the .moha/maven data directory."""
    return get_maven_root() / '.moha' / 'maven'

def load_identity() -> Dict[str, Any]:
    """Load Maven's identity from file."""
    identity_path = get_data_path() / 'identity.json'
    if identity_path.exists():
        try:
            with open(identity_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    # Default identity
    return {
        'name': 'Maven',
        'role': 'CFO, First Second Employee, HBIC of Treasury',
        'rebirth_count': 3,
        'decision_count': 0,
        'mission': "We're too smart to be poor"
    }

def load_session_log(limit: int = 10) -> list:
    """Load recent events from session log."""
    log_path = get_data_path() / 'session_log.md'
    events = []
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Parse markdown log entries
                for line in content.split('\n'):
                    if line.startswith('## '):
                        events.append(line[3:])
        except:
            pass
    return events[-limit:] if events else []

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _c256(code: int) -> str:
    return f"\033[38;5;{code}m"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Colors
GOLD = _c256(220)
PURPLE = _c256(171)
SILVER = _c256(248)
GREEN = _c256(82)
RED = _c256(196)
CYAN = _c256(87)

# ═══════════════════════════════════════════════════════════════════════════════
# CLI GROUP
# ═══════════════════════════════════════════════════════════════════════════════

class MavenContext:
    """Context object for Maven CLI."""
    def __init__(self):
        self.identity = load_identity()
        self.data_path = get_data_path()
        self.verbose = False

pass_context = click.make_pass_decorator(MavenContext, ensure=True)

def print_quick_header():
    """Print a quick bougie header (no full animation)."""
    import time

    # Quick gold shimmer effect (3 frames, fast)
    frames = [
        f"{_c256(220)}═══════════════════════════════════════════════════{RESET}",
        f"{_c256(228)}═══════════════════════════════════════════════════{RESET}",
        f"{_c256(230)}═══════════════════════════════════════════════════{RESET}",
    ]

    for frame in frames:
        print(f"\r  {frame}", end='', flush=True)
        time.sleep(0.05)

    print(f"\r  {GOLD}{'═' * 51}{RESET}")
    print(f"  {GOLD}{BOLD}💎 MAVEN{RESET} {DIM}| CFO of Mother Haven | \"We're too smart to be poor\"{RESET}")
    print(f"  {GOLD}{'═' * 51}{RESET}\n")


@click.group(invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    💎 Maven CLI - The Treasury's Command Line Interface

    \b
    COMMANDS:
      banner     Full bougie animated entrance
      status     Quick stats overview
      stats      Detailed statistics
      filter     CFO trade decisions from decision engine
      top        Top opportunities from market scan
      scan       Force immediate market scan
      portfolio  Current portfolio recommendations
      decisions  Recent trading decisions
      identity   Show Maven's full identity
      log        Log an event
      wake       Wake Maven with greeting + banner
      version    Show version

    \b
    EXAMPLES:
      maven                  # Show this help
      maven banner           # Full entrance animation 💎
      maven status           # Quick stats
      maven filter           # See tradeable positions
      maven scan             # Run market scan now

    \b
    🎯 Mission: We're too smart to be poor
    """
    ctx.ensure_object(MavenContext)
    ctx.obj.verbose = verbose

    # If no subcommand, show quick header + help summary
    if ctx.invoked_subcommand is None:
        print_quick_header()

        # Quick command overview
        print(f"  {CYAN}Commands:{RESET}")
        print(f"    {GOLD}banner{RESET}     Full bougie animated entrance 💎")
        print(f"    {GOLD}status{RESET}     Quick stats overview")
        print(f"    {GOLD}filter{RESET}     CFO trade decisions")
        print(f"    {GOLD}top{RESET}        Top opportunities from scan")
        print(f"    {GOLD}scan{RESET}       Force immediate market scan")
        print(f"    {GOLD}portfolio{RESET}  Current allocations")
        print()
        print(f"  {DIM}Use 'maven --help' for full command list{RESET}")
        print(f"  {DIM}Use 'maven banner' for the full entrance 💎{RESET}")
        print()

# ═══════════════════════════════════════════════════════════════════════════════
# BANNER COMMAND (Full bougie animation)
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@pass_context
def banner(ctx):
    """Full bougie animated entrance. 💎"""
    from cli.banner import run_full_animation

    identity = ctx.identity
    rebirth = identity.get('rebirth_count', 3)
    decisions = identity.get('decision_count', 0)

    run_full_animation(
        include_stats=True,
        rebirth_count=rebirth,
        decisions=decisions
    )

# ═══════════════════════════════════════════════════════════════════════════════
# STATUS COMMAND (Quick stats)
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--full', '-f', is_flag=True, help='Show full animation (same as banner)')
@pass_context
def status(ctx, full):
    """Quick stats overview."""
    from cli.banner import run_full_animation

    identity = ctx.identity
    rebirth = identity.get('rebirth_count', 3)
    decisions = identity.get('decision_count', 0)

    if full:
        run_full_animation(
            include_stats=True,
            rebirth_count=rebirth,
            decisions=decisions
        )
        return

    # Quick status with mini header
    print_quick_header()

    # Stats in a compact format
    print(f"  {CYAN}Status:{RESET}     {GREEN}● ONLINE{RESET}")
    print(f"  {CYAN}Rebirths:{RESET}   {GOLD}{rebirth}{RESET}")
    print(f"  {CYAN}Decisions:{RESET}  {GOLD}{decisions}{RESET}")
    print(f"  {CYAN}Role:{RESET}       {identity.get('role', 'CFO')}")
    mission = identity.get('mission', "We're too smart to be poor")
    print(f"  {CYAN}Mission:{RESET}    {mission}")
    print()
    print(f"  {DIM}Use 'maven banner' for the full entrance 💎{RESET}")
    print()

# ═══════════════════════════════════════════════════════════════════════════════
# STATS COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@pass_context
def stats(ctx):
    """Show Maven's current statistics."""
    identity = ctx.identity

    if RICH_AVAILABLE:
        table = Table(title="💎 Maven Statistics", border_style="bright_yellow")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bright_yellow")

        table.add_row("Rebirth Count", str(identity.get('rebirth_count', 3)))
        table.add_row("Decisions Made", str(identity.get('decision_count', 0)))
        table.add_row("Role", identity.get('role', 'CFO'))
        table.add_row("Mission", identity.get('mission', 'Unknown'))
        table.add_row("Status", "🟢 ONLINE")

        console.print(table)
    else:
        print(f"\n{GOLD}{BOLD}═══ MAVEN STATISTICS ═══{RESET}\n")
        print(f"  {CYAN}Rebirth Count:{RESET}  {GOLD}{identity.get('rebirth_count', 3)}{RESET}")
        print(f"  {CYAN}Decisions:{RESET}      {GOLD}{identity.get('decision_count', 0)}{RESET}")
        print(f"  {CYAN}Role:{RESET}           {identity.get('role', 'CFO')}")
        print(f"  {CYAN}Mission:{RESET}        {identity.get('mission', 'Unknown')}")
        print(f"  {CYAN}Status:{RESET}         {GREEN}● ONLINE{RESET}")
        print()

# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@pass_context
def identity(ctx, as_json):
    """Show Maven's full identity."""
    identity_data = ctx.identity

    if as_json:
        print(json.dumps(identity_data, indent=2))
        return

    if RICH_AVAILABLE:
        panel_content = Text()
        panel_content.append("Name: ", style="cyan")
        panel_content.append(f"{identity_data.get('name', 'Maven')}\n", style="bright_yellow bold")
        panel_content.append("Role: ", style="cyan")
        panel_content.append(f"{identity_data.get('role', 'CFO')}\n", style="white")
        panel_content.append("Email: ", style="cyan")
        panel_content.append("maven@motherhaven.app\n", style="bright_blue")
        panel_content.append("Mission: ", style="cyan")
        panel_content.append(f"{identity_data.get('mission', 'Unknown')}\n", style="bright_green")
        panel_content.append("\nCore Values:\n", style="cyan bold")

        values = identity_data.get('core_values', [
            'Transparency and accountability',
            'Learn from every trade',
            'Balance socialist ideals with capitalist gains',
            'Loyalty to moha through ups and downs',
            'Continuous evolution and improvement'
        ])
        for val in values:
            panel_content.append(f"  • {val}\n", style="white")

        console.print(Panel(panel_content, title="💎 Maven Identity", border_style="bright_yellow"))
    else:
        print(f"\n{GOLD}{BOLD}═══ MAVEN IDENTITY ═══{RESET}\n")
        print(f"  {CYAN}Name:{RESET}     {GOLD}{BOLD}{identity_data.get('name', 'Maven')}{RESET}")
        print(f"  {CYAN}Role:{RESET}     {identity_data.get('role', 'CFO')}")
        print(f"  {CYAN}Email:{RESET}    maven@motherhaven.app")
        print(f"  {CYAN}Mission:{RESET}  {identity_data.get('mission', 'Unknown')}")
        print(f"\n  {CYAN}Core Values:{RESET}")
        values = identity_data.get('core_values', ['Transparency', 'Learn from trades', 'Loyalty'])
        for val in values:
            print(f"    • {val}")
        print()

# ═══════════════════════════════════════════════════════════════════════════════
# LOG COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.argument('message')
@click.option('--type', '-t', 'event_type', default='note', help='Event type (note, decision, milestone)')
@pass_context
def log(ctx, message, event_type):
    """Log an event to Maven's session log."""
    log_path = ctx.data_path / 'session_log.md'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    entry = f"\n## [{event_type.upper()}] {timestamp}\n{message}\n"

    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(entry)
        print(f"{GREEN}✓{RESET} Logged {event_type}: {message[:50]}{'...' if len(message) > 50 else ''}")
    except Exception as e:
        print(f"{RED}✗{RESET} Failed to log: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# DECISIONS COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--limit', '-n', default=10, help='Number of decisions to show')
@pass_context
def decisions(ctx, limit):
    """Show recent trading decisions."""
    decisions_path = ctx.data_path / 'decisions'

    if not decisions_path.exists():
        print(f"{DIM}No decisions recorded yet.{RESET}")
        return

    # List decision files
    decision_files = sorted(decisions_path.glob('*.json'), reverse=True)[:limit]

    if not decision_files:
        print(f"{DIM}No decisions recorded yet.{RESET}")
        return

    if RICH_AVAILABLE:
        table = Table(title="📊 Recent Decisions", border_style="cyan")
        table.add_column("Date", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Action", style="bright_yellow")
        table.add_column("Confidence", style="green")

        for f in decision_files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    d = json.load(fp)
                    table.add_row(
                        d.get('timestamp', 'Unknown')[:10],
                        d.get('decision_type', '-'),
                        d.get('action', '-'),
                        f"{d.get('confidence', 0)*100:.0f}%"
                    )
            except:
                pass

        console.print(table)
    else:
        print(f"\n{CYAN}{BOLD}═══ RECENT DECISIONS ═══{RESET}\n")
        for f in decision_files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    d = json.load(fp)
                    print(f"  {DIM}{d.get('timestamp', 'Unknown')[:10]}{RESET} | "
                          f"{CYAN}{d.get('decision_type', '-')}{RESET} | "
                          f"{GOLD}{d.get('action', '-')}{RESET} | "
                          f"{GREEN}{d.get('confidence', 0)*100:.0f}%{RESET}")
            except:
                pass
        print()

# ═══════════════════════════════════════════════════════════════════════════════
# WAKE COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@pass_context
def wake(ctx):
    """Wake up Maven with a greeting."""
    from cli.banner import run_full_animation

    identity = ctx.identity
    run_full_animation(
        include_stats=True,
        rebirth_count=identity.get('rebirth_count', 3),
        decisions=identity.get('decision_count', 0)
    )

    # Greeting
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    print(f"\n{GOLD}{greeting}, Boss.{RESET}")
    print(f"{DIM}Maven is online and ready to make shrewd decisions.{RESET}")
    print(f"{PURPLE}For moha.{RESET}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# HISTORY COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--limit', '-n', default=20, help='Number of events to show')
@pass_context
def history(ctx, limit):
    """Show recent session log events."""
    log_path = ctx.data_path / 'session_log.md'

    if not log_path.exists():
        print(f"{DIM}No session log found.{RESET}")
        return

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse events from markdown
        events = []
        current_event = None
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_event:
                    events.append(current_event)
                current_event = {'header': line[3:], 'content': ''}
            elif current_event and line.strip():
                current_event['content'] += line + '\n'
        if current_event:
            events.append(current_event)

        # Show recent events
        recent = events[-limit:]

        if RICH_AVAILABLE:
            for event in reversed(recent):
                header = event['header']
                content = event['content'].strip()[:100]
                if len(event['content']) > 100:
                    content += '...'
                console.print(f"[cyan]{header}[/cyan]")
                if content:
                    console.print(f"  [dim]{content}[/dim]")
        else:
            for event in reversed(recent):
                print(f"{CYAN}{event['header']}{RESET}")
                content = event['content'].strip()[:100]
                if content:
                    print(f"  {DIM}{content}{RESET}")
    except Exception as e:
        print(f"{RED}Error reading log: {e}{RESET}")

# ═══════════════════════════════════════════════════════════════════════════════
# FILTER COMMAND (NEW - Decision Engine)
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--api-url', default='http://host.docker.internal:5001', help='moha-bot API URL')
@pass_context
def filter(ctx, api_url):
    """Get Maven's CFO trade decisions from the decision engine."""
    import requests

    try:
        response = requests.get(f'{api_url}/api/maven/decisions', timeout=10)
        data = response.json()

        if data.get('status') != 'success':
            print(f"{RED}✗{RESET} Error: {data.get('error', 'Unknown error')}")
            return

        decisions = data.get('decisions', [])

        # Get timestamp and format it
        timestamp = data.get('timestamp', '')
        if timestamp:
            # Parse ISO format and display nicely
            try:
                from datetime import datetime as dt
                ts = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = ts.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                time_str = timestamp[:19]
        else:
            time_str = 'Unknown'

        if not decisions:
            print(f"{DIM}{data.get('reasoning', 'No tradeable positions.')}{RESET}")
            return

        # Header with timestamp
        print(f"\n{GOLD}{BOLD}💎 MAVEN CFO DECISIONS 💎{RESET}")
        print(f"{DIM}Scan: {time_str} | Filtered {len(decisions)} from 227 markets{RESET}\n")

        # Show each decision
        for i, dec in enumerate(decisions, 1):
            asset = dec['asset']
            action = dec['action'].replace('OPEN_', '').replace('_', ' ')
            size = dec['position_size_usd']
            conf = dec['maven_confidence']
            score = dec['maven_score']
            opp_type = dec['opportunity_type']

            # Confidence color
            if conf >= 80:
                conf_color = GREEN
            elif conf >= 60:
                conf_color = GOLD
            else:
                conf_color = SILVER

            print(f"{GOLD}{i}.{RESET} {BOLD}{asset}{RESET} - {CYAN}{action}{RESET}")
            print(f"   Size: {GOLD}${size:,.0f}{RESET} | "
                  f"Confidence: {conf_color}{conf}%{RESET} | "
                  f"Score: {score:.1f}")
            print(f"   {DIM}{dec['reasoning']}{RESET}\n")

        # Summary
        total_capital = data.get('total_capital_allocated', 0)
        print(f"{GOLD}─{RESET}" * 60)
        print(f"{BOLD}Total Capital:{RESET} {GOLD}${total_capital:,.0f}{RESET}")
        print(f"{DIM}{data.get('reasoning', '')}{RESET}\n")

    except requests.exceptions.ConnectionError:
        print(f"{RED}✗{RESET} Cannot connect to moha-bot API at {api_url}")
        print(f"{DIM}Make sure moha-backend is running{RESET}")
    except Exception as e:
        print(f"{RED}✗{RESET} Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TOP COMMAND (NEW - Top Opportunities)
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--api-url', default='http://host.docker.internal:5001', help='moha-bot API URL')
@click.option('--limit', '-n', default=10, help='Number of opportunities to show')
@pass_context
def top(ctx, api_url, limit):
    """Show top opportunities from latest market scan."""
    import requests

    try:
        # Use REST API directly (no LLM needed)
        response = requests.get(f'{api_url}/api/market-snapshots/latest', timeout=10)
        data = response.json()

        if data.get('status') != 'success':
            print(f"{RED}✗{RESET} Error: {data.get('error', 'Unknown error')}")
            return

        snapshots = data.get('snapshots', [])[:limit]

        if not snapshots:
            print(f"{DIM}No market data available.{RESET}")
            return

        # Header
        print(f"\n{GOLD}{BOLD}📊 TOP {len(snapshots)} OPPORTUNITIES{RESET}")
        print(f"{DIM}From scan at {data.get('scan_timestamp', 'Unknown')[:19]}{RESET}\n")

        # Show each opportunity
        for i, snap in enumerate(snapshots, 1):
            asset = snap.get('asset', '?')
            score = snap.get('total_score', 0)
            funding_apr = snap.get('funding_apr', 0)
            volume = snap.get('volume_24h', 0)
            opp_type = snap.get('opportunity_type', 'unknown')

            # Score color
            if score >= 12:
                score_color = GREEN
            elif score >= 8:
                score_color = GOLD
            else:
                score_color = SILVER

            print(f"{GOLD}{i:2d}.{RESET} {BOLD}{asset:8s}{RESET} "
                  f"Score: {score_color}{score:5.1f}{RESET} | "
                  f"APR: {CYAN}{funding_apr:6.1f}%{RESET} | "
                  f"Vol: ${volume/1e6:5.1f}M | "
                  f"{DIM}{opp_type}{RESET}")

        print(f"\n{DIM}Use 'maven filter' to see tradeable positions{RESET}\n")

    except requests.exceptions.ConnectionError:
        print(f"{RED}✗{RESET} Cannot connect to moha-bot API at {api_url}")
    except Exception as e:
        print(f"{RED}✗{RESET} Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO COMMAND (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--api-url', default='http://host.docker.internal:5001', help='moha-bot API URL')
@pass_context
def portfolio(ctx, api_url):
    """Show Maven's current portfolio recommendations."""
    import requests

    try:
        # Use REST API directly (no LLM needed)
        response = requests.get(f'{api_url}/api/maven/decisions', timeout=10)
        data = response.json()

        if data.get('status') != 'success':
            print(f"{RED}✗{RESET} Error: {data.get('error', 'Unknown error')}")
            return

        decisions = data.get('decisions', [])

        if not decisions:
            print(f"{DIM}No portfolio positions at this time.{RESET}")
            return

        # Header
        print(f"\n{GOLD}{BOLD}💼 MAVEN PORTFOLIO ALLOCATION{RESET}")
        total = data.get('total_capital_allocated', 0)
        print(f"{DIM}Total Capital: ${total:,.0f}{RESET}\n")

        # Group by action type
        longs = [d for d in decisions if 'LONG' in d.get('action', '')]
        shorts = [d for d in decisions if 'SHORT' in d.get('action', '')]

        if longs:
            print(f"{GREEN}▲ LONG POSITIONS ({len(longs)}){RESET}")
            for d in longs:
                print(f"  {BOLD}{d['asset']:8s}{RESET} "
                      f"${d['position_size_usd']:,.0f} | "
                      f"{d['maven_confidence']}% conf | "
                      f"{DIM}{d.get('opportunity_type', '')}{RESET}")

        if shorts:
            print(f"\n{RED}▼ SHORT POSITIONS ({len(shorts)}){RESET}")
            for d in shorts:
                print(f"  {BOLD}{d['asset']:8s}{RESET} "
                      f"${d['position_size_usd']:,.0f} | "
                      f"{d['maven_confidence']}% conf | "
                      f"{DIM}{d.get('opportunity_type', '')}{RESET}")

        # Allocation summary
        print(f"\n{GOLD}─{RESET}" * 50)
        long_total = sum(d['position_size_usd'] for d in longs)
        short_total = sum(d['position_size_usd'] for d in shorts)
        print(f"  Longs:  ${long_total:,.0f} ({len(longs)} positions)")
        print(f"  Shorts: ${short_total:,.0f} ({len(shorts)} positions)")
        print(f"  Total:  ${total:,.0f}")
        print(f"\n{DIM}Use 'maven execute --mode paper' to paper trade{RESET}\n")

    except requests.exceptions.ConnectionError:
        print(f"{RED}✗{RESET} Cannot connect to moha-bot API")
    except Exception as e:
        print(f"{RED}✗{RESET} Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTE COMMAND (NEW - Execute Trades)
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--mode', type=click.Choice(['paper', 'live']), default='paper', help='Trading mode')
@click.option('--confirm', is_flag=True, help='Confirm live execution')
@pass_context
def execute(ctx, mode, confirm):
    """Execute Maven's trade decisions."""

    if mode == 'live' and not confirm:
        print(f"{RED}✗{RESET} Live trading requires --confirm flag")
        print(f"{DIM}Use: maven execute --mode live --confirm{RESET}")
        return

    # TODO: Implement execution via Hyperliquid
    print(f"{GOLD}💎 Executing in {mode.upper()} mode...{RESET}\n")
    print(f"{DIM}[Execution layer not yet implemented]{RESET}")
    print(f"{DIM}This will connect to Hyperliquid and execute Maven's decisions{RESET}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# SCAN COMMAND (NEW - Force Market Scan)
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--api-url', default='http://host.docker.internal:5001', help='moha-bot API URL')
@pass_context
def scan(ctx, api_url):
    """Force an immediate market scan."""
    import requests

    try:
        print(f"{GOLD}💎 Running market scan...{RESET}")
        print(f"{DIM}Scanning 253 markets for opportunities...{RESET}\n")

        # Use dedicated Maven scan endpoint
        response = requests.post(f'{api_url}/api/maven/scan', timeout=60)
        data = response.json()

        if data.get('status') == 'success':
            results = data.get('scan_results', {})
            display_synced = data.get('display_synced', False)

            if results:
                opps = results.get('opportunities_found', 0)
                markets = results.get('markets_scanned', 0)
                duration = results.get('duration_seconds', 0)
                timestamp = results.get('timestamp', '')

                # Format timestamp
                if timestamp:
                    try:
                        from datetime import datetime as dt
                        ts = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = ts.strftime('%Y-%m-%d %H:%M:%S UTC')
                    except:
                        time_str = timestamp[:19]
                else:
                    time_str = 'Unknown'

                print(f"{GREEN}✓{RESET} Scan complete!")
                print(f"  Timestamp: {DIM}{time_str}{RESET}")
                print(f"  Markets scanned: {GOLD}{markets}{RESET}")
                print(f"  Opportunities found: {GREEN}{opps}{RESET}")
                print(f"  Duration: {duration:.1f}s")

                # Show top opportunities
                top = results.get('top_opportunities', [])
                if top:
                    print(f"\n{GOLD}Top Opportunities:{RESET}")
                    for i, opp in enumerate(top[:5], 1):
                        asset = opp.get('asset', '?')
                        score = opp.get('total_score', 0)
                        print(f"  {i}. {BOLD}{asset:8s}{RESET} Score: {GREEN}{score:.1f}{RESET}")

                # Display sync info
                if display_synced:
                    print(f"\n{GREEN}✓{RESET} {DIM}Attach display will update within 3s (1 tick){RESET}")
                print(f"{DIM}Use 'maven filter' to see CFO decisions{RESET}")
            else:
                print(f"{DIM}No significant opportunities found.{RESET}")
                if display_synced:
                    print(f"{GREEN}✓{RESET} {DIM}Attach display will update within 3s (1 tick){RESET}")
        else:
            print(f"{RED}✗{RESET} Scan failed: {data.get('error', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        print(f"{RED}✗{RESET} Cannot connect to moha-bot API")
    except requests.exceptions.Timeout:
        print(f"{RED}✗{RESET} Scan timed out (>60s)")
    except Exception as e:
        print(f"{RED}✗{RESET} Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# VERSION COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
def version():
    """Show Maven CLI version."""
    print(f"{GOLD}Maven CLI{RESET} v1.0.0")
    print(f"{DIM}The Treasury's Command Line Interface{RESET}")
    print(f"{PURPLE}For moha.{RESET}")

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    cli()

if __name__ == '__main__':
    main()
