# Maven CLI - The Treasury's Command Line Interface
"""
Maven CLI package.

Commands:
    maven              - Show banner + status (default)
    maven status       - Show animated banner with stats
    maven stats        - Show statistics
    maven identity     - Show full identity
    maven log <msg>    - Log an event
    maven decisions    - Show recent decisions
    maven wake         - Wake up with greeting
    maven history      - Show session log
    maven version      - Show version
"""

from cli.main import cli, main
from cli.banner import run_full_animation, print_static_banner

__all__ = ['cli', 'main', 'run_full_animation', 'print_static_banner']
__version__ = '1.0.0'
