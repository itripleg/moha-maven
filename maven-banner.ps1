#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Maven Banner - The Treasury's Grand Entrance
.DESCRIPTION
    Displays Maven's animated ASCII banner with gold wave effects,
    diamond sparkles, and optional stats integration.
.PARAMETER Quick
    Skip animation, show static banner
.PARAMETER Stats
    Include stats display (attempts to fetch from MCP)
.EXAMPLE
    .\maven-banner.ps1
    .\maven-banner.ps1 -Quick
    .\maven-banner.ps1 -Stats
#>

param(
    [switch]$Quick,
    [switch]$Stats
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ScriptDir

try {
    $args = @()

    if ($Quick) {
        $args += "--quick"
    }

    if ($Stats) {
        # Try to fetch stats from MCP or identity file
        $identityPath = ".\.moha\maven\identity.json"
        if (Test-Path $identityPath) {
            $identity = Get-Content $identityPath | ConvertFrom-Json
            $rebirth = $identity.rebirth_count
            $decisions = $identity.decision_count

            if ($rebirth) {
                $args += "--rebirth"
                $args += $rebirth
            }
            if ($decisions) {
                $args += "--decisions"
                $args += $decisions
            }
        }
        $args += "--stats"
    }

    python -m cli.banner @args
}
finally {
    Pop-Location
}
