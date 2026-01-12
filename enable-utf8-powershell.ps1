# Enable UTF-8 Encoding in PowerShell for Emoji Support
# Run this once to add UTF-8 support to your PowerShell profile

Write-Host "Enabling UTF-8 encoding for PowerShell..." -ForegroundColor Cyan

$profilePath = $PROFILE.CurrentUserAllHosts

# Create profile if it doesn't exist
if (!(Test-Path -Path $profilePath)) {
    $profileDir = Split-Path -Path $profilePath -Parent
    if (!(Test-Path -Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

# UTF-8 encoding lines
$utf8Lines = @"

# UTF-8 Encoding Support (for emojis and unicode)
`$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
"@

# Check if already added
if (!(Select-String -Path $profilePath -Pattern "UTF-8 Encoding Support" -Quiet)) {
    Add-Content -Path $profilePath -Value $utf8Lines
    Write-Host "✅ UTF-8 encoding added to profile!" -ForegroundColor Green
} else {
    Write-Host "✅ UTF-8 encoding already configured!" -ForegroundColor Green
}

# Apply to current session
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n✅ UTF-8 enabled for current session!" -ForegroundColor Green
Write-Host "   Restart PowerShell for permanent effect.`n" -ForegroundColor Yellow

Write-Host "Test: 💎 🚀 ✅ 📋 🔗" -ForegroundColor Magenta
