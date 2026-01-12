# Start Claude Code with Maven Agent
# Usage: .\maven-chat.ps1

$mavenAgent = Get-Content -Path "maven_agent.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress -Depth 10

Write-Host "Starting Maven (CFO of Mother Haven)..." -ForegroundColor Cyan
Write-Host ""

# Start Claude with Maven agent definition
claude --agent maven --agents $mavenAgent
