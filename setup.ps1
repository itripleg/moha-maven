# Maven Setup Script
# Automates the setup process for Maven CFO agent

Write-Host "=== Maven CFO Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Start Docker containers
Write-Host "[1/2] Starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Success: Maven containers running" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "  Error: Failed to start containers" -ForegroundColor Red
    exit 1
}

# Step 2: Register MCP server
Write-Host "[2/2] Registering Maven MCP server..." -ForegroundColor Yellow

# Check if already registered
$mcpList = claude mcp list 2>&1 | Out-String
if ($mcpList -match "maven") {
    Write-Host "  Success: Maven MCP already registered" -ForegroundColor Green
} else {
    Write-Host "  Running: claude mcp add maven -- powershell -File maven-mcp-wrapper.ps1" -ForegroundColor Gray
    claude mcp add maven -- powershell -File maven-mcp-wrapper.ps1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Success: Maven MCP registered" -ForegroundColor Green
    } else {
        Write-Host "  Warning: Automatic registration failed" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Please run manually:" -ForegroundColor Cyan
        Write-Host "  claude mcp add maven -- powershell -File maven-mcp-wrapper.ps1" -ForegroundColor White
        Write-Host ""
    }
}

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start chatting with Maven:" -ForegroundColor Cyan
Write-Host "  .\maven-chat.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  (Loads full CFO personality + MCP memory access)" -ForegroundColor Gray
Write-Host ""
