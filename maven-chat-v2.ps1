# Maven v2 - Optimized CFO Chat Command
# PowerShell helper for chatting with Maven from anywhere
#
# Usage:
#   mav              - Start chat with Maven
#   mav s / status   - Check if container/MCP is running (FAST)
#   mav r / restart  - Restart Maven container
#   mav l / logs     - Follow logs
#   mav help         - Show all commands
#
# Installation:
#   Run: .\setup-maven-cmd.ps1 (will auto-detect and use this version)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Auto-detect Maven project directory
$script:MAVEN_PROJECT_DIR = if ($env:MAVEN_HOME) {
    $env:MAVEN_HOME
} elseif (Test-Path "$PSScriptRoot\.moha\maven") {
    $PSScriptRoot
} else {
    "C:\Users\ecoli\OneDrive\Documents\GitHub\motherhaven-ecosystem\moha-maven"
}

$script:MAVEN_PROMPT_FILE = Join-Path $script:MAVEN_PROJECT_DIR "maven-prompt.txt"

# MCP configuration path (Windows)
$script:MCP_CONFIG_PATH = "$env:APPDATA\claude-code\mcp-servers"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

function Test-MavenContainer {
    # Fast container check (~5ms vs 2-3s for 'claude mcp list')
    $status = docker ps --filter "name=^maven$" --format "{{.Status}}" 2>$null
    return [PSCustomObject]@{
        Running = $null -ne $status
        Status = $status
    }
}

function Test-McpConfigured {
    # Check if MCP server is configured (instant)
    Test-Path "$script:MCP_CONFIG_PATH\maven"
}

function Show-MavenStatus {
    Write-Host "`n  🏦 MAVEN STATUS" -ForegroundColor Magenta
    Write-Host "  ===============" -ForegroundColor Magenta
    Write-Host ""

    # Container check (fast!)
    $container = Test-MavenContainer
    Write-Host "  Container:  " -NoNewline -ForegroundColor Gray
    if ($container.Running) {
        Write-Host "✓ Running" -ForegroundColor Green
        Write-Host "    $($container.Status)" -ForegroundColor DarkGray
    } else {
        Write-Host "✗ Not Running" -ForegroundColor Yellow
        Write-Host "    Run 'mav restart' or 'docker restart maven'" -ForegroundColor DarkGray
    }

    # MCP check (instant!)
    $mcpConfigured = Test-McpConfigured
    Write-Host "  MCP Server: " -NoNewline -ForegroundColor Gray
    if ($mcpConfigured) {
        Write-Host "✓ Configured" -ForegroundColor Green
    } else {
        Write-Host "✗ Not Configured" -ForegroundColor Yellow
        Write-Host "    Run 'mav setup-mcp' to configure" -ForegroundColor DarkGray
    }

    # Database check
    try {
        $dbCheck = docker exec maven_postgres pg_isready -U maven_user 2>$null
        Write-Host "  Database:   " -NoNewline -ForegroundColor Gray
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Ready" -ForegroundColor Green
        } else {
            Write-Host "✗ Not Ready" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Database:   " -NoNewline -ForegroundColor Gray
        Write-Host "? Unknown" -ForegroundColor DarkGray
    }

    # Project path
    Write-Host ""
    Write-Host "  Location:   " -NoNewline -ForegroundColor Gray
    Write-Host $script:MAVEN_PROJECT_DIR -ForegroundColor Cyan
    Write-Host ""
}

function Start-MavenSetupMcp {
    Write-Host "`n  🔧 Setting up Maven MCP server..." -ForegroundColor Cyan
    $wrapperPath = Join-Path $script:MAVEN_PROJECT_DIR "maven-mcp-wrapper.ps1"

    if (-not (Test-Path $wrapperPath)) {
        Write-Host "  ✗ Error: MCP wrapper not found at:" -ForegroundColor Red
        Write-Host "    $wrapperPath" -ForegroundColor DarkGray
        return
    }

    try {
        claude mcp add maven -s user -- powershell.exe -ExecutionPolicy Bypass -File $wrapperPath
        Write-Host "  ✓ Done! MCP server 'maven' configured." -ForegroundColor Green
        Write-Host "  Test with: " -NoNewline -ForegroundColor Gray
        Write-Host "mav s" -ForegroundColor Yellow
    } catch {
        Write-Host "  ✗ Failed to configure MCP: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

function Show-MavenLogs {
    param([switch]$Follow = $true)

    $container = Test-MavenContainer
    if (-not $container.Running) {
        Write-Host "  ✗ Maven container not running" -ForegroundColor Yellow
        Write-Host "  Run 'mav restart' to start it" -ForegroundColor DarkGray
        return
    }

    Write-Host "  📋 Maven Container Logs (Ctrl+C to exit)" -ForegroundColor Magenta
    if ($Follow) {
        docker logs maven -f
    } else {
        docker logs maven --tail 50
    }
}

function Restart-MavenContainer {
    Write-Host "`n  🔄 Restarting Maven container..." -ForegroundColor Cyan

    $container = Test-MavenContainer
    if (-not $container.Running) {
        Write-Host "  Container not running, starting..." -ForegroundColor Yellow
        docker start maven
    } else {
        docker restart maven
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Done!" -ForegroundColor Green
        Start-Sleep -Milliseconds 500
        Show-MavenStatus
    } else {
        Write-Host "  ✗ Failed to restart container" -ForegroundColor Red
    }
}

function Show-MavenHelp {
    Write-Host "`n  🏦 MAV - Chat with Maven, CFO of Mother Haven" -ForegroundColor Magenta
    Write-Host "  =============================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  Commands:" -ForegroundColor Cyan
    Write-Host "    mav                " -NoNewline -ForegroundColor Yellow
    Write-Host "Start chat with Maven (default)"
    Write-Host "    mav ""your prompt"" " -NoNewline -ForegroundColor Yellow
    Write-Host "Start chat with initial prompt"
    Write-Host ""
    Write-Host "    mav s | status     " -NoNewline -ForegroundColor Yellow
    Write-Host "Check container & MCP status (fast)"
    Write-Host "    mav r | restart    " -NoNewline -ForegroundColor Yellow
    Write-Host "Restart the Maven container"
    Write-Host "    mav l | logs       " -NoNewline -ForegroundColor Yellow
    Write-Host "Follow container logs (Ctrl+C to exit)"
    Write-Host "    mav setup-mcp      " -NoNewline -ForegroundColor Yellow
    Write-Host "Configure MCP server for Claude Code"
    Write-Host "    mav help           " -NoNewline -ForegroundColor Yellow
    Write-Host "Show this message"
    Write-Host ""
    Write-Host "  Examples:" -ForegroundColor Cyan
    Write-Host "    mav                              " -NoNewline -ForegroundColor DarkGray
    Write-Host "# Start interactive chat"
    Write-Host "    mav ""what's my portfolio status?"" " -NoNewline -ForegroundColor DarkGray
    Write-Host "# Quick query"
    Write-Host "    mav s                            " -NoNewline -ForegroundColor DarkGray
    Write-Host "# Fast status check"
    Write-Host ""
    Write-Host "  For MoHa. 💎" -ForegroundColor Magenta
    Write-Host ""
}

function Start-MavenChat {
    param(
        [string]$InitialPrompt,
        [string[]]$Args
    )

    # Pre-flight checks
    $container = Test-MavenContainer
    if (-not $container.Running) {
        Write-Host "`n  ⚠️  Maven container not running!" -ForegroundColor Yellow
        Write-Host "  MCP tools won't be available without the container." -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  Start container? [Y/n]: " -NoNewline -ForegroundColor Cyan
        $response = Read-Host
        if ($response -ne 'n' -and $response -ne 'N') {
            Write-Host "  Starting Maven container..." -ForegroundColor Cyan
            docker start maven
            Start-Sleep -Seconds 2
        }
        Write-Host ""
    }

    # Verify prompt file exists
    if (-not (Test-Path $script:MAVEN_PROMPT_FILE)) {
        Write-Host "  ✗ Error: Maven prompt file not found at:" -ForegroundColor Red
        Write-Host "    $script:MAVEN_PROMPT_FILE" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  Using basic prompt..." -ForegroundColor Yellow
        $mavenPrompt = "You are Maven, CFO of Mother Haven. For MoHa. 💎"
    } else {
        # Read Maven personality prompt
        $mavenPrompt = Get-Content $script:MAVEN_PROMPT_FILE -Raw
    }

    # Start Claude Code with Maven personality
    Write-Host "  💼 Starting Maven..." -ForegroundColor Cyan
    Write-Host ""

    try {
        if ($InitialPrompt) {
            # Chat with initial prompt
            $allArgs = @($InitialPrompt) + $Args
            & claude --append-system-prompt "$mavenPrompt" @allArgs
        } else {
            # Interactive chat
            & claude --append-system-prompt "$mavenPrompt"
        }
    } catch {
        Write-Host "`n  ✗ Failed to start Claude Code: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "  Make sure Claude Code is installed and in PATH" -ForegroundColor DarkGray
    }
}

# ==============================================================================
# MAIN COMMAND
# ==============================================================================

function mav {
    param(
        [Parameter(Position=0)]
        [string]$Command,
        [Parameter(Position=1, ValueFromRemainingArguments)]
        [string[]]$Args
    )

    # Command routing with shortcuts
    switch -Regex ($Command) {
        # Status (s, status)
        "^s(tatus)?$" {
            Show-MavenStatus
        }

        # Restart (r, restart)
        "^r(estart)?$" {
            Restart-MavenContainer
        }

        # Logs (l, logs)
        "^l(ogs)?$" {
            Show-MavenLogs
        }

        # Setup MCP
        "^setup-mcp$" {
            Start-MavenSetupMcp
        }

        # Help
        "^(help|h|\?)$" {
            Show-MavenHelp
        }

        # Default: Start chat (with optional prompt)
        default {
            Start-MavenChat -InitialPrompt $Command -Args $Args
        }
    }
}

# ==============================================================================
# EXPORT
# ==============================================================================

# Export the mav function
Export-ModuleMember -Function mav

# Show brief startup message if running standalone
if ($MyInvocation.InvocationName -ne '.') {
    Write-Host "Maven v2 loaded. Type 'mav help' for commands." -ForegroundColor DarkGray
}
