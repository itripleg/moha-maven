# Activate Maven Agent in PowerShell
# Usage: .\activate-maven.ps1

$mavenAgentJson = Get-Content -Path "maven_agent.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress

Write-Host "Activating Maven agent..." -ForegroundColor Cyan

# Start Claude with Maven agent
claude --agent maven --agents $mavenAgentJson
