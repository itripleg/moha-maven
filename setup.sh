#!/bin/bash
# Maven Setup Script
# Automates the setup process for Maven CFO agent

echo "=== Maven CFO Setup ==="
echo ""

# Step 1: Copy Claude settings
if [ ! -f ".claude_settings.json" ]; then
    echo "[1/3] Copying Claude settings..."
    cp .claude_settings.json.example .claude_settings.json
    echo "  ✓ Created .claude_settings.json"
else
    echo "[1/3] Claude settings already exist"
fi

# Step 2: Start Docker containers
echo "[2/3] Starting Docker containers..."
docker-compose up -d
if [ $? -eq 0 ]; then
    echo "  ✓ Maven containers running"
else
    echo "  ✗ Failed to start containers"
    exit 1
fi

# Step 3: Register MCP server
echo "[3/3] Registering Maven MCP server..."

# Check if already registered
if claude mcp list 2>&1 | grep -q "maven"; then
    echo "  ✓ Maven MCP already registered"
else
    # Try to register
    if claude mcp add maven docker exec -i maven python -m maven_mcp.server; then
        echo "  ✓ Maven MCP registered"
    else
        echo "  ⚠ Manual MCP registration needed"
        echo ""
        echo "Run this command manually:"
        echo "  claude mcp add maven docker exec -i maven python -m maven_mcp.server"
        echo ""
    fi
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To start chatting with Maven:"
echo "  cd moha-maven"
echo "  claude"
echo ""
echo "Maven will greet you as your CFO with full personality! 💎"
echo ""
