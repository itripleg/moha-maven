#!/bin/bash
# Maven Banner - The Treasury's Grand Entrance
#
# Displays Maven's animated ASCII banner with gold wave effects,
# diamond sparkles, and optional stats integration.
#
# Usage:
#   ./maven-banner.sh           # Full animation
#   ./maven-banner.sh --quick   # Static display
#   ./maven-banner.sh --stats   # Include stats

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ARGS=()

# Parse arguments
for arg in "$@"; do
    case $arg in
        --stats|-s)
            # Try to read stats from identity file
            if [ -f ".moha/maven/identity.json" ]; then
                REBIRTH=$(python3 -c "import json; print(json.load(open('.moha/maven/identity.json')).get('rebirth_count', 3))" 2>/dev/null || echo "3")
                DECISIONS=$(python3 -c "import json; print(json.load(open('.moha/maven/identity.json')).get('decision_count', 0))" 2>/dev/null || echo "0")
                ARGS+=("--rebirth" "$REBIRTH" "--decisions" "$DECISIONS")
            fi
            ARGS+=("--stats")
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

python -m cli.banner "${ARGS[@]}"
