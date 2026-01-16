#!/bin/bash
# Maven CLI wrapper - ensures proper Python invocation
# Usage: ./maven.sh [command] [args]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if installed via pip
if command -v maven &> /dev/null; then
    maven "$@"
else
    # Run directly
    python -m cli.main "$@"
fi
