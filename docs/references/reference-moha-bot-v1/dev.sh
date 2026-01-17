#!/bin/bash
# Development mode - runs container with volume mounts for live code editing
# Changes to Python files, templates, and static files will auto-reload

# Stop and remove existing container if running
docker stop moha-bot 2>/dev/null || true
docker rm moha-bot 2>/dev/null || true

# Run container with source code mounted as volumes
docker run -d \
  --name moha-bot \
  -p 5000:5000 \
  -e DEV_MODE=1 \
  -v "$(pwd)/app.py:/app/app.py" \
  -v "$(pwd)/database.py:/app/database.py" \
  -v "$(pwd)/bot_runner.py:/app/bot_runner.py" \
  -v "$(pwd)/templates:/app/templates" \
  -v "$(pwd)/static:/app/static" \
  -v "$(pwd)/data:/app/data" \
  moha-bot

echo ""
echo "✅ Development container started!"
echo ""
echo "📝 Edit files locally - Flask will auto-reload on changes"
echo "🌐 Dashboard: http://localhost:5000"
echo "📊 View logs: docker logs -f moha-bot"
echo "🔗 Attach to tmux: docker attach moha-bot"
echo "🛑 Stop container: docker stop moha-bot"
echo ""
