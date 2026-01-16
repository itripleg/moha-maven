#!/usr/bin/env python3
"""
Maven Banner Animation - The Treasury's Grand Entrance

A multi-phase animated banner that flexes on `moha status`.
Features:
- Matrix-style character rain reveal
- Gold/Diamond treasury color palette
- Sparkle effects and pulsing diamonds
- Stats integration display
- Typewriter taglines

Usage:
    python -m cli.banner           # Full animation
    python -m cli.banner --quick   # Skip to static display
    python -m cli.banner --stats   # Include live stats
"""

import sys
import os
import time
import math
import random
import argparse

# Fix Windows encoding issues
if sys.platform == 'win32':
    # Enable UTF-8 mode
    os.system('')  # Enable ANSI escape codes on Windows
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
from typing import Optional, List, Tuple
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# ASCII ART - THE MAVEN LOGO
# ═══════════════════════════════════════════════════════════════════════════════

MAVEN_LOGO = r"""
 ███╗   ███╗ █████╗ ██╗   ██╗███████╗███╗   ██╗
 ████╗ ████║██╔══██╗██║   ██║██╔════╝████╗  ██║
 ██╔████╔██║███████║██║   ██║█████╗  ██╔██╗ ██║
 ██║╚██╔╝██║██╔══██║╚██╗ ██╔╝██╔══╝  ██║╚██╗██║
 ██║ ╚═╝ ██║██║  ██║ ╚████╔╝ ███████╗██║ ╚████║
 ╚═╝     ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝
"""

MAVEN_LOGO_SLIM = r"""
  __  __    _    __     __ _____  _   _
 |  \/  |  / \   \ \   / /| ____|| \ | |
 | |\/| | / _ \   \ \ / / |  _|  |  \| |
 | |  | |/ ___ \   \ V /  | |___ | |\  |
 |_|  |_/_/   \_\   \_/   |_____||_| \_|
"""

DIAMOND_FRAME_TOP = "    ╔═══════════════════════════════════════════════════════╗"
DIAMOND_FRAME_BOT = "    ╚═══════════════════════════════════════════════════════╝"

TITLE_LINE = "         💎  C F O  ·  H B I C  ·  T R E A S U R Y  💎"
TAGLINE = "We're too smart to be poor."
SIGNATURE = "For moha."

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTES - TREASURY GOLD THEME
# ═══════════════════════════════════════════════════════════════════════════════

def _c256(code: int) -> str:
    """Return ANSI escape for 256-color palette."""
    return f"\033[38;5;{code}m"

def _bg256(code: int) -> str:
    """Return ANSI escape for 256-color background."""
    return f"\033[48;5;{code}m"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Treasury Gold Gradient (warm gold to bright yellow)
GOLD_GRADIENT = [
    94,   # Dark bronze
    136,  # Gold brown
    178,  # Gold
    220,  # Bright gold
    221,  # Light gold
    222,  # Pale gold
    228,  # Yellow gold
    229,  # Cream gold
    230,  # Almost white gold
]

# Diamond Sparkle Colors (cool whites and silvers)
DIAMOND_GRADIENT = [
    232,  # Near black
    236,  # Dark gray
    240,  # Gray
    244,  # Light gray
    248,  # Silver
    252,  # Light silver
    255,  # White
    231,  # Bright white
]

# Purple accent (Mother Haven brand)
PURPLE_ACCENT = [
    53,   # Deep purple
    54,   # Dark purple
    91,   # Purple
    127,  # Medium purple
    163,  # Light purple
    171,  # Pale purple
]

# Matrix green for reveal effect
MATRIX_GREEN = [22, 28, 34, 40, 46, 82, 118, 154, 190]

# ═══════════════════════════════════════════════════════════════════════════════
# ANIMATION EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════

def clear_screen():
    """Clear terminal screen."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def move_cursor(row: int, col: int):
    """Move cursor to position."""
    sys.stdout.write(f"\033[{row};{col}H")
    sys.stdout.flush()

def hide_cursor():
    """Hide the cursor."""
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def show_cursor():
    """Show the cursor."""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def cursor_up(lines: int):
    """Move cursor up N lines."""
    sys.stdout.write(f"\033[{lines}A")
    sys.stdout.flush()

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: MATRIX REVEAL
# ═══════════════════════════════════════════════════════════════════════════════

def matrix_reveal(lines: List[str], frames: int = 20, delay: float = 0.04) -> None:
    """
    Reveal the logo with a matrix-style character rain effect.
    Characters randomly appear and settle into place.
    """
    height = len(lines)
    width = max(len(line) for line in lines)

    # Pad lines to consistent width
    padded = [line.ljust(width) for line in lines]

    # Track which characters have been revealed
    revealed = [[False] * width for _ in range(height)]

    # Matrix characters for the rain effect
    matrix_chars = "01アイウエオカキクケコサシスセソタチツテト"

    for frame in range(frames):
        if frame > 0:
            cursor_up(height + 1)

        # Reveal more characters each frame (accelerating)
        chars_to_reveal = int((frame / frames) ** 1.5 * height * width * 0.15) + 1

        for _ in range(chars_to_reveal):
            row = random.randint(0, height - 1)
            col = random.randint(0, width - 1)
            revealed[row][col] = True

        # Render frame
        for row_idx, line in enumerate(padded):
            output = ""
            for col_idx, char in enumerate(line):
                if revealed[row_idx][col_idx]:
                    # Character is revealed - show with gold gradient
                    if char not in ' \n':
                        color_idx = min(int(frame / frames * len(GOLD_GRADIENT)), len(GOLD_GRADIENT) - 1)
                        output += f"{_c256(GOLD_GRADIENT[color_idx])}{char}"
                    else:
                        output += char
                else:
                    # Not yet revealed - show matrix rain or empty
                    if random.random() < 0.3 and char not in ' \n':
                        rain_char = random.choice(matrix_chars)
                        green = random.choice(MATRIX_GREEN[:5])
                        output += f"{_c256(green)}{rain_char}"
                    else:
                        output += " "
            print(f"{output}{RESET}")
        print()  # Extra line for spacing

        time.sleep(delay)

    # Final frame - all revealed with full gold
    cursor_up(height + 1)
    for line in padded:
        output = ""
        for char in line:
            if char not in ' \n':
                output += f"{_c256(GOLD_GRADIENT[-3])}{char}"
            else:
                output += char
        print(f"{output}{RESET}")
    print()

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: GOLD WAVE ANIMATION
# ═══════════════════════════════════════════════════════════════════════════════

def gold_wave_animation(lines: List[str], frames: int = 30, delay: float = 0.035) -> None:
    """
    Animate the logo with flowing gold wave gradients.
    Uses sine waves for smooth diagonal color transitions.
    """
    height = len(lines)
    width = max(len(line) for line in lines)
    padded = [line.ljust(width) for line in lines]

    for frame in range(frames):
        if frame > 0:
            cursor_up(height + 1)

        for row_idx, line in enumerate(padded):
            output = ""
            for col_idx, char in enumerate(line):
                if char not in ' \n':
                    # Create flowing diagonal wave
                    wave = math.sin((col_idx * 0.12) + (row_idx * 0.25) + (frame * 0.35))
                    color_idx = int((wave + 1) * 0.5 * (len(GOLD_GRADIENT) - 1))

                    # Add sparkle effect - random bright flashes
                    if random.random() < 0.02:
                        output += f"{BOLD}{_c256(231)}{char}"  # Bright white flash
                    else:
                        output += f"{_c256(GOLD_GRADIENT[color_idx])}{char}"
                else:
                    output += char
            print(f"{output}{RESET}")
        print()

        time.sleep(delay)

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: DIAMOND SPARKLE TITLE
# ═══════════════════════════════════════════════════════════════════════════════

def diamond_sparkle_title(frames: int = 25, delay: float = 0.05) -> None:
    """
    Display the title with diamond sparkle effects.
    Diamonds pulse and shimmer.
    """
    title_text = TITLE_LINE

    for frame in range(frames):
        if frame > 0:
            cursor_up(3)

        # Frame top with pulsing color
        pulse = math.sin(frame * 0.3)
        frame_color = PURPLE_ACCENT[int((pulse + 1) * 0.5 * (len(PURPLE_ACCENT) - 1))]
        print(f"{_c256(frame_color)}{DIAMOND_FRAME_TOP}{RESET}")

        # Title with sparkle diamonds
        output = ""
        for idx, char in enumerate(title_text):
            if char == '💎':
                # Diamonds get special sparkle treatment
                sparkle_phase = (frame + idx) % 8
                if sparkle_phase < 2:
                    output += f"{_c256(231)}✦{RESET}"  # Bright sparkle
                elif sparkle_phase < 4:
                    output += f"{_c256(255)}◇{RESET}"  # Diamond outline
                elif sparkle_phase < 6:
                    output += f"{_c256(228)}💎{RESET}"  # Gold diamond
                else:
                    output += f"{_c256(171)}💎{RESET}"  # Purple diamond
            elif char not in ' \n':
                # Text gets subtle gold shimmer
                shimmer = math.sin(idx * 0.2 + frame * 0.4)
                color_idx = int((shimmer + 1) * 0.5 * 3) + 4  # Upper gold range
                output += f"{_c256(GOLD_GRADIENT[color_idx])}{char}"
            else:
                output += char
        print(f"{output}{RESET}")

        # Frame bottom
        print(f"{_c256(frame_color)}{DIAMOND_FRAME_BOT}{RESET}")

        time.sleep(delay)

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: TYPEWRITER TAGLINE
# ═══════════════════════════════════════════════════════════════════════════════

def typewriter_effect(text: str, color_code: int = 228, delay: float = 0.04) -> None:
    """
    Type out text character by character with a cursor effect.
    """
    padding = " " * 20
    sys.stdout.write(f"{padding}{_c256(color_code)}")
    sys.stdout.flush()

    for i, char in enumerate(text):
        sys.stdout.write(char)
        sys.stdout.flush()
        # Add cursor blink effect
        if i < len(text) - 1:
            sys.stdout.write(f"{_c256(231)}▌{RESET}{_c256(color_code)}")
            sys.stdout.flush()
            time.sleep(delay)
            sys.stdout.write("\b \b")
            sys.stdout.flush()

    print(RESET)

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: STATS DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

def display_stats_box(rebirth_count: int = 3, decisions: int = 0, uptime_hours: int = 0) -> None:
    """
    Display Maven's current stats in a styled box.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print()
    print(f"    {_c256(240)}╭───────────────────────────────────────────────────────╮{RESET}")
    print(f"    {_c256(240)}│{RESET}  {_c256(GOLD_GRADIENT[4])}⟐{RESET} Rebirth #{_c256(228)}{rebirth_count}{RESET}    "
          f"{_c256(GOLD_GRADIENT[4])}⟐{RESET} Decisions: {_c256(228)}{decisions}{RESET}    "
          f"{_c256(GOLD_GRADIENT[4])}⟐{RESET} {_c256(240)}{now}{RESET}  {_c256(240)}│{RESET}")
    print(f"    {_c256(240)}╰───────────────────────────────────────────────────────╯{RESET}")
    print()

# ═══════════════════════════════════════════════════════════════════════════════
# SIGNATURE FLOURISH
# ═══════════════════════════════════════════════════════════════════════════════

def signature_flourish(delay: float = 0.02) -> None:
    """
    Display Maven's signature with a flourish effect.
    """
    sig_line = f"                    — Maven, HBIC, Mother Haven Treasury"
    for_moha = f"                                      {SIGNATURE}"

    # Fade in signature
    for alpha in range(0, 6):
        if alpha > 0:
            cursor_up(2)

        color = DIAMOND_GRADIENT[alpha]
        print(f"{_c256(color)}{sig_line}{RESET}")
        print(f"{_c256(PURPLE_ACCENT[min(alpha, len(PURPLE_ACCENT)-1)])}{for_moha}{RESET}")
        time.sleep(delay * 2)

    # Final bright version
    cursor_up(2)
    print(f"{_c256(248)}{sig_line}{RESET}")
    print(f"{_c256(171)}{BOLD}{for_moha}{RESET}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ANIMATION ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_animation(
    include_stats: bool = False,
    rebirth_count: int = 3,
    decisions: int = 0
) -> None:
    """
    Run the complete Maven banner animation sequence.
    """
    hide_cursor()

    try:
        lines = MAVEN_LOGO.strip().split('\n')

        # Phase 1: Matrix reveal
        print()  # Top padding
        matrix_reveal(lines, frames=18, delay=0.035)
        time.sleep(0.1)

        # Phase 2: Gold wave animation
        height = len(lines)
        cursor_up(height + 2)
        gold_wave_animation(lines, frames=25, delay=0.03)
        time.sleep(0.2)

        # Phase 3: Diamond title reveal
        diamond_sparkle_title(frames=20, delay=0.04)
        time.sleep(0.15)

        # Phase 4: Typewriter tagline
        print()
        typewriter_effect(f'"{TAGLINE}"', color_code=228, delay=0.035)
        time.sleep(0.3)

        # Phase 5: Stats (optional)
        if include_stats:
            display_stats_box(rebirth_count=rebirth_count, decisions=decisions)
        else:
            print()

        # Phase 6: Signature flourish
        signature_flourish(delay=0.025)

        print()  # Final spacing

    finally:
        show_cursor()

def print_static_banner(include_stats: bool = False) -> None:
    """
    Print a static (non-animated) version of the Maven banner.
    """
    lines = MAVEN_LOGO.strip().split('\n')

    print()
    # Logo with static gold gradient
    for row_idx, line in enumerate(lines):
        output = ""
        for col_idx, char in enumerate(line):
            if char not in ' \n':
                color_idx = min(col_idx // 8, len(GOLD_GRADIENT) - 1)
                output += f"{_c256(GOLD_GRADIENT[color_idx])}{char}"
            else:
                output += char
        print(f"{output}{RESET}")

    print()

    # Title
    print(f"{_c256(PURPLE_ACCENT[3])}{DIAMOND_FRAME_TOP}{RESET}")
    print(f"{_c256(GOLD_GRADIENT[5])}{TITLE_LINE}{RESET}")
    print(f"{_c256(PURPLE_ACCENT[3])}{DIAMOND_FRAME_BOT}{RESET}")

    print()
    print(f"                    {_c256(228)}\"{TAGLINE}\"{RESET}")

    if include_stats:
        display_stats_box()
    else:
        print()

    print(f"                    {_c256(248)}— Maven, HBIC, Mother Haven Treasury{RESET}")
    print(f"                                      {_c256(171)}{BOLD}{SIGNATURE}{RESET}")
    print()

# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Maven Banner - The Treasury's Grand Entrance"
    )
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Skip animation, show static banner'
    )
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Include stats display'
    )
    parser.add_argument(
        '--rebirth', '-r',
        type=int,
        default=3,
        help='Rebirth count to display'
    )
    parser.add_argument(
        '--decisions', '-d',
        type=int,
        default=0,
        help='Decision count to display'
    )

    args = parser.parse_args()

    try:
        if args.quick:
            print_static_banner(include_stats=args.stats)
        else:
            run_full_animation(
                include_stats=args.stats,
                rebirth_count=args.rebirth,
                decisions=args.decisions
            )
    except KeyboardInterrupt:
        show_cursor()
        print(f"\n{_c256(240)}Animation interrupted.{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
