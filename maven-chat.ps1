# Maven - CFO of Mother Haven
# PowerShell helper for chatting with Maven from anywhere
#
# Usage:
#   mav          - Start chat with Maven
#   mav status   - Check if container/MCP is running
#   mav help     - Show all commands
#
# Installation:
#   Run: .\setup-maven-cmd.ps1

$script:MAVEN_PROJECT_DIR = "C:\Users\ecoli\OneDrive\Documents\GitHub\moha-maven"
$script:MAVEN_PROMPT_FILE = "C:\Users\ecoli\OneDrive\Documents\GitHub\moha-maven\maven-prompt.txt"

function mav {
    param(
        [Parameter(Position=0)]
        [string]$Command,
        [Parameter(Position=1, ValueFromRemainingArguments)]
        [string[]]$Args
    )

    switch ($Command) {
        "status" {
            Write-Host "`n  MAVEN STATUS" -ForegroundColor Magenta
            Write-Host "  ============" -ForegroundColor Magenta

            # Check Docker container
            $containerStatus = docker ps --filter "name=maven" --format "{{.Status}}" 2>$null
            if ($containerStatus) {
                Write-Host "  Container: " -NoNewline -ForegroundColor Gray
                Write-Host "Running" -ForegroundColor Green
                Write-Host "    $containerStatus" -ForegroundColor DarkGray
            } else {
                Write-Host "  Container: " -NoNewline -ForegroundColor Gray
                Write-Host "Not Running" -ForegroundColor Yellow
            }

            # Check MCP server
            $mcpCheck = claude mcp list 2>&1
            if ($mcpCheck -match "maven") {
                Write-Host "  MCP Server: " -NoNewline -ForegroundColor Gray
                Write-Host "Configured" -ForegroundColor Green
            } else {
                Write-Host "  MCP Server: " -NoNewline -ForegroundColor Gray
                Write-Host "Not configured" -ForegroundColor Yellow
                Write-Host "    Run 'mav setup-mcp' to configure" -ForegroundColor DarkGray
            }
            Write-Host ""
        }

        "setup-mcp" {
            Write-Host "`n  Setting up Maven MCP server..." -ForegroundColor Cyan
            $wrapperPath = Join-Path $script:MAVEN_PROJECT_DIR "maven-mcp-wrapper.ps1"
            claude mcp add maven -s user -- powershell.exe -ExecutionPolicy Bypass -File $wrapperPath
            Write-Host "  Done! MCP server 'maven' added." -ForegroundColor Green
            Write-Host ""
        }

        "logs" {
            Write-Host "  Maven Container Logs (Ctrl+C to exit)" -ForegroundColor Magenta
            docker logs maven -f
        }

        "restart" {
            Write-Host "  Restarting Maven container..." -ForegroundColor Cyan
            docker restart maven
            Write-Host "  Done!" -ForegroundColor Green
        }

        "help" {
            Write-Host "`n  MAV - Chat with Maven" -ForegroundColor Magenta
            Write-Host "  =====================" -ForegroundColor Magenta
            Write-Host ""
            Write-Host "  Commands:" -ForegroundColor Cyan
            Write-Host "    mav              " -NoNewline -ForegroundColor Yellow
            Write-Host "Start chat with Maven"
            Write-Host "    mav status       " -NoNewline -ForegroundColor Yellow
            Write-Host "Check container & MCP status"
            Write-Host "    mav setup-mcp    " -NoNewline -ForegroundColor Yellow
            Write-Host "Configure MCP server for Claude"
            Write-Host "    mav logs         " -NoNewline -ForegroundColor Yellow
            Write-Host "Follow container logs"
            Write-Host "    mav restart      " -NoNewline -ForegroundColor Yellow
            Write-Host "Restart the container"
            Write-Host "    mav help         " -NoNewline -ForegroundColor Yellow
            Write-Host "Show this message"
            Write-Host ""
        }

        default {
            # Default: Start Claude Code with Maven personality
            Write-Host "`n  Starting Maven..." -ForegroundColor Cyan
            Write-Host ""

            # Read the Maven prompt from file
            $mavenPrompt = Get-Content $script:MAVEN_PROMPT_FILE -Raw

            # Use --append-system-prompt to inject Maven personality
            # Wrap in single quotes and escape any internal single quotes
            if ($Command) {
                # If there's a command, pass it as initial prompt
                & claude --append-system-prompt "$mavenPrompt" "$Command" $Args
            } else {
                & claude --append-system-prompt "$mavenPrompt"
            }
        }
    }
}
