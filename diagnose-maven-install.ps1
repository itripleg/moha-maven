# Diagnose Maven Installation Issues
# Run this to see why 'maven' command isn't working

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "MAVEN INSTALLATION DIAGNOSTICS" -ForegroundColor Magenta
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

$installDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"

# Check 1: Installation directory exists
Write-Host "1. Checking installation directory..." -ForegroundColor Cyan
if (Test-Path $installDir) {
    Write-Host "   ✓ Directory exists: $installDir" -ForegroundColor Green
} else {
    Write-Host "   ✗ Directory NOT found: $installDir" -ForegroundColor Red
    exit
}

# Check 2: Files exist
Write-Host "`n2. Checking installed files..." -ForegroundColor Cyan
$mavenPs1 = Join-Path $installDir "maven.ps1"
$mavenCmd = Join-Path $installDir "maven.cmd"

if (Test-Path $mavenPs1) {
    Write-Host "   ✓ maven.ps1 exists" -ForegroundColor Green
    Write-Host "     Location: $mavenPs1" -ForegroundColor Gray
} else {
    Write-Host "   ✗ maven.ps1 NOT found!" -ForegroundColor Red
}

if (Test-Path $mavenCmd) {
    Write-Host "   ✓ maven.cmd exists" -ForegroundColor Green
    Write-Host "     Location: $mavenCmd" -ForegroundColor Gray
} else {
    Write-Host "   ✗ maven.cmd NOT found!" -ForegroundColor Red
}

# Check 3: WindowsApps in PATH
Write-Host "`n3. Checking PATH..." -ForegroundColor Cyan
$pathDirs = $env:Path -split ';'
if ($pathDirs -contains $installDir) {
    Write-Host "   ✓ WindowsApps is in PATH" -ForegroundColor Green
} else {
    Write-Host "   ✗ WindowsApps NOT in PATH!" -ForegroundColor Red
    Write-Host "     PATH should include: $installDir" -ForegroundColor Yellow
}

# Check 4: Try to find maven command
Write-Host "`n4. Checking if 'maven' command is found..." -ForegroundColor Cyan
$mavenCommand = Get-Command maven -ErrorAction SilentlyContinue
if ($mavenCommand) {
    Write-Host "   ✓ 'maven' command found!" -ForegroundColor Green
    Write-Host "     Type: $($mavenCommand.CommandType)" -ForegroundColor Gray
    Write-Host "     Source: $($mavenCommand.Source)" -ForegroundColor Gray
} else {
    Write-Host "   ✗ 'maven' command NOT found!" -ForegroundColor Red
    Write-Host "     Possible fixes:" -ForegroundColor Yellow
    Write-Host "       - Close and reopen PowerShell" -ForegroundColor Yellow
    Write-Host "       - Run: `$env:Path = [System.Environment]::GetEnvironmentVariable('Path','User')" -ForegroundColor Yellow
}

# Check 5: Try direct execution
Write-Host "`n5. Testing direct execution..." -ForegroundColor Cyan
if (Test-Path $mavenPs1) {
    try {
        Write-Host "   Testing: & '$mavenPs1' help" -ForegroundColor Gray
        & $mavenPs1 help
    } catch {
        Write-Host "   ✗ Error running maven.ps1: $_" -ForegroundColor Red
    }
}

# Check 6: Execution policy
Write-Host "`n6. Checking execution policy..." -ForegroundColor Cyan
$policy = Get-ExecutionPolicy
Write-Host "   Current policy: $policy" -ForegroundColor Gray
if ($policy -eq "Restricted") {
    Write-Host "   ✗ Execution policy is too restrictive!" -ForegroundColor Red
    Write-Host "     Run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ Execution policy allows scripts" -ForegroundColor Green
}

Write-Host "`n" -NoNewline
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "RECOMMENDATIONS" -ForegroundColor Magenta
Write-Host "=" * 70 -ForegroundColor Cyan

if (!(Get-Command maven -ErrorAction SilentlyContinue)) {
    Write-Host "`nQuick fix - try these in order:" -ForegroundColor Yellow
    Write-Host "1. Close this PowerShell window and open a NEW one"
    Write-Host "2. If still not working, run:" -ForegroundColor Cyan
    Write-Host "   `$env:Path += ';$installDir'" -ForegroundColor White
    Write-Host "3. Then try: maven help" -ForegroundColor White
}

Write-Host ""
