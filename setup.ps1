# Maven Setup Script
# Automates the setup process for Maven CFO agent

Write-Host "=== Maven CFO Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Copy Claude settings
if (-not (Test-Path ".claude_settings.json")) {
    Write-Host "[1/3] Copying Claude settings..." -ForegroundColor Yellow
    Copy-Item ".claude_settings.json.example" ".claude_settings.json"
    Write-Host "  ✓ Created .claude_settings.json" -ForegroundColor Green
} else {
    Write-Host "[1/3] Claude settings already exist" -ForegroundColor Green
}

# Step 2: Start Docker containers
Write-Host "[2/3] Starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Maven containers running" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to start containers" -ForegroundColor Red
    exit 1
}

# Step 3: Register MCP server
Write-Host "[3/3] Registering Maven MCP server..." -ForegroundColor Yellow

# Check if already registered
$mcpList = claude mcp list 2>&1 | Out-String
if ($mcpList -match "maven") {
    Write-Host "  ✓ Maven MCP already registered" -ForegroundColor Green
} else {
    # Try to register
    $result = claude mcp add maven docker exec -i maven python -m maven_mcp.server 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Maven MCP registered" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Manual MCP registration needed" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Run this command manually:" -ForegroundColor Cyan
        Write-Host '  claude mcp add maven docker exec -i maven python -m maven_mcp.server' -ForegroundColor White
        Write-Host ""
    }
}

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start chatting with Maven:" -ForegroundColor Cyan
Write-Host "  cd moha-maven" -ForegroundColor White
Write-Host "  claude" -ForegroundColor White
Write-Host ""
Write-Host "Maven will greet you as your CFO with full personality! 💎" -ForegroundColor Magenta
Write-Host ""
