#!/bin/bash
# Entrypoint script for moha-bot container
# Starts Flask API in background and bot_runner in tmux foreground

set -e

echo "[ENTRYPOINT] Starting Motherhaven bot container..."

# Start Flask API server in background
echo "[ENTRYPOINT] Starting Flask API on port 5000..."
if [ "$DEV_MODE" = "1" ]; then
    echo "[ENTRYPOINT] Development mode enabled - Flask will auto-reload on changes"
    python -m flask run --host=0.0.0.0 --port=5000 --reload --debugger > /var/log/flask.log 2>&1 &
else
    python -m flask run --host=0.0.0.0 --port=5000 > /var/log/flask.log 2>&1 &
fi
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 2

# Check if Flask started successfully
if kill -0 $FLASK_PID 2>/dev/null; then
    echo "[ENTRYPOINT] Flask API started (PID: $FLASK_PID)"
else
    echo "[ENTRYPOINT] ERROR: Flask failed to start"
    exit 1
fi

# Start tmux session with bot_runner
echo "[ENTRYPOINT] Starting bot_runner in tmux..."

# Create tmux session with bot_runner in first window
tmux new-session -d -s moha -n "bot" "python bot_runner.py"

# Create second window for Flask logs
tmux new-window -t moha:1 -n "flask" "tail -f /var/log/flask.log"

# Select bot window by default
tmux select-window -t moha:0

# Check if running in interactive mode (has TTY)
if [ -t 0 ]; then
    echo "[ENTRYPOINT] Interactive mode detected - attaching to tmux"
    echo "[ENTRYPOINT] Use Ctrl+B then D to detach, Ctrl+B then 1 to switch to Flask logs"
    # Attach to tmux session (keeps container running and allows interaction)
    tmux attach-session -t moha
else
    echo "[ENTRYPOINT] Detached mode detected - keeping processes running"
    echo "[ENTRYPOINT] Use 'docker attach moha-bot' to connect to tmux session"
    # Keep container alive by waiting on Flask process
    wait $FLASK_PID
fi
