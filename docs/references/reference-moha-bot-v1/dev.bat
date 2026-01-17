@echo off
REM Development mode - runs container with volume mounts for live code editing
REM Changes to Python files, templates, and static files will auto-reload

echo Stopping existing container...
docker stop moha-bot 2>nul
docker rm moha-bot 2>nul

echo.
echo Starting development container...
docker run -d ^
  --name moha-bot ^
  -p 5000:5000 ^
  -e DEV_MODE=1 ^
  -v "%cd%/app.py:/app/app.py" ^
  -v "%cd%/database.py:/app/database.py" ^
  -v "%cd%/bot_runner.py:/app/bot_runner.py" ^
  -v "%cd%/templates:/app/templates" ^
  -v "%cd%/static:/app/static" ^
  -v "%cd%/data:/app/data" ^
  moha-bot

echo.
echo ✅ Development container started!
echo.
echo 📝 Edit files locally - Flask will auto-reload on changes
echo 🌐 Dashboard: http://localhost:5000
echo 📊 View logs: docker logs -f moha-bot
echo 🔗 Attach to tmux: docker attach moha-bot
echo 🛑 Stop container: docker stop moha-bot
echo.
