# Setup Maven command for PowerShell
# Adds 'mav' command to your profile so you can use it from anywhere
# (Using 'mav' to avoid conflict with Apache Maven)

Write-Host ""
Write-Host "  MAV COMMAND SETUP" -ForegroundColor Magenta
Write-Host "  ==================" -ForegroundColor Magenta
Write-Host ""

$profilePath = $PROFILE.CurrentUserAllHosts

# Auto-detect v2 if available, fallback to v1
$mavenScriptV2 = Join-Path $PSScriptRoot "maven-chat-v2.ps1"
$mavenScriptV1 = Join-Path $PSScriptRoot "maven-chat.ps1"

if (Test-Path $mavenScriptV2) {
    $mavenScript = $mavenScriptV2
    $version = "v2 (Optimized)"
} else {
    $mavenScript = $mavenScriptV1
    $version = "v1"
}

Write-Host "  Profile:  " -NoNewline -ForegroundColor Gray
Write-Host $profilePath -ForegroundColor White
Write-Host "  Version:  " -NoNewline -ForegroundColor Gray
Write-Host $version -ForegroundColor Cyan

# Create profile directory if needed
$profileDir = Split-Path -Path $profilePath -Parent
if (!(Test-Path -Path $profileDir)) {
    Write-Host "  Creating profile directory..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

# Create profile if needed
if (!(Test-Path -Path $profilePath)) {
    Write-Host "  Creating PowerShell profile..." -ForegroundColor Cyan
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

# Remove old maven-chat reference if exists (v1 or v2)
$profileContent = Get-Content -Path $profilePath -Raw -ErrorAction SilentlyContinue
if ($profileContent -match "maven-chat(-v2)?\.ps1") {
    Write-Host "  Updating existing installation..." -ForegroundColor Cyan
    $profileContent = $profileContent -replace "# Maven(-| - CFO of Mother Haven)\r?\n", ""
    $profileContent = $profileContent -replace '\. ".*maven-chat(-v2)?\.ps1"\r?\n', ""
    $profileContent = $profileContent.Trim()
    Set-Content -Path $profilePath -Value $profileContent
}

# Add to profile
Write-Host "  Adding to profile..." -ForegroundColor Cyan
Add-Content -Path $profilePath -Value "`n# Maven - CFO of Mother Haven"
Add-Content -Path $profilePath -Value ". `"$mavenScript`""

Write-Host ""
Write-Host "  Done!" -ForegroundColor Green
Write-Host ""

# Load it now
. $mavenScript

Write-Host "  Commands available:" -ForegroundColor Cyan
Write-Host "    mav             " -NoNewline -ForegroundColor Yellow
Write-Host "Start chat with Maven"
Write-Host "    mav s           " -NoNewline -ForegroundColor Yellow
Write-Host "Status (fast!)"
Write-Host "    mav r           " -NoNewline -ForegroundColor Yellow
Write-Host "Restart container"
Write-Host "    mav l           " -NoNewline -ForegroundColor Yellow
Write-Host "Follow logs"
Write-Host "    mav help        " -NoNewline -ForegroundColor Yellow
Write-Host "All commands"
Write-Host ""
Write-Host "  Try it: " -NoNewline -ForegroundColor Gray
Write-Host "mav s" -ForegroundColor Yellow
Write-Host ""
