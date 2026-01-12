# Start Claude Code with Maven Agent
# Usage: .\maven-chat.ps1

$mavenPrompt = Get-Content -Path "maven_agent.json" -Raw | ConvertFrom-Json | Select-Object -ExpandProperty maven | Select-Object -ExpandProperty prompt

Write-Host "Starting Maven (CFO of Mother Haven)..." -ForegroundColor Cyan
Write-Host ""

# Start Claude with Maven personality via --append-system-prompt
claude --append-system-prompt $mavenPrompt
