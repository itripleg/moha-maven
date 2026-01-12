# Quick Setup Script for Maven PowerShell Command
# Run this to add 'maven' command to your PowerShell profile

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "💎 MAVEN POWERSHELL SETUP 💎" -ForegroundColor Magenta
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Get profile path
$profilePath = $PROFILE.CurrentUserAllHosts
$mavenScript = Join-Path $PSScriptRoot "maven.ps1"

Write-Host "Profile location: " -NoNewline
Write-Host $profilePath -ForegroundColor Yellow

# Create profile directory if it doesn't exist
$profileDir = Split-Path -Path $profilePath -Parent
if (!(Test-Path -Path $profileDir)) {
    Write-Host "`nCreating profile directory..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

# Create profile if it doesn't exist
if (!(Test-Path -Path $profilePath)) {
    Write-Host "Creating PowerShell profile..." -ForegroundColor Cyan
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

# Check if already installed
$importLine = ". `"$mavenScript`""
if (Select-String -Path $profilePath -Pattern "maven.ps1" -Quiet) {
    Write-Host "`n✅ Maven helper is already installed!" -ForegroundColor Green
    Write-Host "`nReloading..." -ForegroundColor Cyan
    . $mavenScript
    Write-Host "`n💎 Type 'maven' to start chatting!" -ForegroundColor Magenta
    Write-Host "💎 Type 'maven help' for all commands`n" -ForegroundColor Magenta
    exit
}

# Add to profile
Write-Host "`nAdding maven helper to profile..." -ForegroundColor Cyan
Add-Content -Path $profilePath -Value "`n# Maven container helper - Quick access to Maven CLI"
Add-Content -Path $profilePath -Value $importLine

Write-Host "✅ Successfully added to profile!" -ForegroundColor Green

# Load it now
Write-Host "`nLoading maven helper..." -ForegroundColor Cyan
. $mavenScript

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "`nYou can now use these commands from anywhere:" -ForegroundColor Cyan
Write-Host "  maven          " -NoNewline -ForegroundColor Yellow
Write-Host "- Start interactive chat with Maven"
Write-Host "  maven status   " -NoNewline -ForegroundColor Yellow
Write-Host "- Show container status"
Write-Host "  maven logs     " -NoNewline -ForegroundColor Yellow
Write-Host "- Follow logs in real-time"
Write-Host "  maven restart  " -NoNewline -ForegroundColor Yellow
Write-Host "- Restart container"
Write-Host "  maven help     " -NoNewline -ForegroundColor Yellow
Write-Host "- Show all commands"
Write-Host "`n💎 Try it now: " -NoNewline -ForegroundColor Magenta
Write-Host "maven" -ForegroundColor Yellow
Write-Host ""
