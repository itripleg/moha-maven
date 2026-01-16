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

@click.group(invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    Maven CLI - The Treasury's Command Line Interface

    \b
    💎 Maven - CFO of Mother Haven
    🎯 Mission: We're too smart to be poor
    """
    ctx.ensure_object(MavenContext)
    ctx.obj.verbose = verbose

    # If no subcommand, show status
    if ctx.invoked_subcommand is None:
        ctx.invoke(status)

# ═══════════════════════════════════════════════════════════════════════════════
# STATUS COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option('--quick', '-q', is_flag=True, help='Skip animation')
@pass_context
def status(ctx, quick):
    """Show Maven's status with animated banner."""
    from cli.banner import run_full_animation, print_static_banner

    identity = ctx.identity
    rebirth = identity.get('rebirth_count', 3)
    decisions = identity.get('decision_count', 0)

    if quick:
        print_static_banner(include_stats=True)
    else:
        run_full_animation(
            include_stats=True,
            rebirth_count=rebirth,
            decisions=decisions
        )

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
