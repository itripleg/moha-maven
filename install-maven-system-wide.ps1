# System-Wide Maven Command Installation
# Installs 'maven' command to your PATH (requires admin)
# After installation, 'maven' will work from any PowerShell or CMD window

#Requires -RunAsAdministrator

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "💎 MAVEN SYSTEM-WIDE INSTALLATION 💎" -ForegroundColor Magenta
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Installation directory (user's local bin - already in PATH)
$installDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
$mavenScriptSource = Join-Path $PSScriptRoot "maven-standalone.ps1"
$mavenScriptDest = Join-Path $installDir "maven.ps1"
$mavenBatchDest = Join-Path $installDir "maven.cmd"

Write-Host "Installation directory: " -NoNewline
Write-Host $installDir -ForegroundColor Yellow
Write-Host ""

# Check if WindowsApps directory exists (it should)
if (!(Test-Path $installDir)) {
    Write-Host "Creating installation directory..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# Copy the maven-standalone.ps1 script
Write-Host "Copying Maven PowerShell script..." -ForegroundColor Cyan
Copy-Item -Path $mavenScriptSource -Destination $mavenScriptDest -Force

# Create a batch wrapper for CMD compatibility
Write-Host "Creating batch wrapper for CMD..." -ForegroundColor Cyan
$batchContent = @"
@echo off
REM Maven Container Quick Access - CMD Wrapper
REM Calls the PowerShell script with arguments

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$mavenScriptDest" %*
"@
Set-Content -Path $mavenBatchDest -Value $batchContent -Force

Write-Host "✅ Installation complete!" -ForegroundColor Green

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "✅ MAVEN INSTALLED TO SYSTEM PATH!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan

Write-Host "`nInstalled files:" -ForegroundColor Cyan
Write-Host "  📄 $mavenScriptDest" -ForegroundColor Gray
Write-Host "  📄 $mavenBatchDest" -ForegroundColor Gray

Write-Host "`nYou can now use 'maven' from:" -ForegroundColor Cyan
Write-Host "  ✓ PowerShell (anywhere)" -ForegroundColor Green
Write-Host "  ✓ CMD (anywhere)" -ForegroundColor Green
Write-Host "  ✓ Windows Terminal (anywhere)" -ForegroundColor Green

Write-Host "`n💎 Try it now: " -NoNewline -ForegroundColor Magenta
Write-Host "maven" -ForegroundColor Yellow

Write-Host "`nAvailable commands:" -ForegroundColor Cyan
Write-Host "  maven          " -NoNewline -ForegroundColor Yellow
Write-Host "- Start interactive chat with Maven"
Write-Host "  maven status   " -NoNewline -ForegroundColor Yellow
Write-Host "- Show container status"
Write-Host "  maven logs     " -NoNewline -ForegroundColor Yellow
Write-Host "- Follow logs in real-time"
Write-Host "  maven start    " -NoNewline -ForegroundColor Yellow
Write-Host "- Start container"
Write-Host "  maven stop     " -NoNewline -ForegroundColor Yellow
Write-Host "- Stop container"
Write-Host "  maven restart  " -NoNewline -ForegroundColor Yellow
Write-Host "- Restart container"
Write-Host "  maven build    " -NoNewline -ForegroundColor Yellow
Write-Host "- Rebuild container"
Write-Host "  maven help     " -NoNewline -ForegroundColor Yellow
Write-Host "- Show all commands"
Write-Host ""

Write-Host "Note: " -NoNewline -ForegroundColor Yellow
Write-Host "Close and reopen your terminal if 'maven' doesn't work immediately." -ForegroundColor Gray
Write-Host ""
