# Maven Container Quick Access
# PowerShell function to quickly jump into Maven's interactive CLI

function maven {
    <#
    .SYNOPSIS
    Jump into Maven's interactive CLI inside the container

    .DESCRIPTION
    Convenience function to exec into the Maven container and start
    the interactive chat interface. Equivalent to:
    docker exec -it maven python -m claude.interactive

    .EXAMPLE
    maven
    # Starts interactive chat with Maven

    .EXAMPLE
    maven status
    # Shows Maven's container status and logs
    #>

    param(
        [Parameter(Position=0)]
        [string]$Command
    )

    switch ($Command) {
        "status" {
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
            Write-Host "💎 MAVEN CONTAINER STATUS 💎" -ForegroundColor Magenta
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan

            # Check if container is running
            $containerStatus = docker ps --filter "name=maven" --format "{{.Status}}"
            if ($containerStatus) {
                Write-Host "`n✅ Container: " -NoNewline -ForegroundColor Green
                Write-Host "Running" -ForegroundColor White
                Write-Host "   Status: $containerStatus" -ForegroundColor Gray

                # Show recent logs
                Write-Host "`n📋 Recent Logs:" -ForegroundColor Cyan
                docker logs maven --tail 20
            } else {
                Write-Host "`n❌ Container: " -NoNewline -ForegroundColor Red
                Write-Host "Not Running" -ForegroundColor White
                Write-Host "`nStart with: docker-compose up -d" -ForegroundColor Yellow
            }

            Write-Host "`n" -NoNewline
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
        }

        "logs" {
            Write-Host "💎 Maven Container Logs (Ctrl+C to exit)" -ForegroundColor Magenta
            docker logs maven -f
        }

        "restart" {
            Write-Host "💎 Restarting Maven container..." -ForegroundColor Magenta
            docker restart maven
            Write-Host "✅ Maven restarted!" -ForegroundColor Green
        }

        "build" {
            Write-Host "💎 Rebuilding Maven container..." -ForegroundColor Magenta
            $currentDir = Get-Location
            Set-Location "$PSScriptRoot"
            docker-compose build maven
            Set-Location $currentDir
            Write-Host "✅ Maven rebuilt! Use 'maven restart' to apply changes." -ForegroundColor Green
        }

        "help" {
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
            Write-Host "💎 MAVEN POWERSHELL HELPER 💎" -ForegroundColor Magenta
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
            Write-Host "`nUsage:" -ForegroundColor Cyan
            Write-Host "  maven          " -NoNewline -ForegroundColor Yellow
            Write-Host "- Start interactive chat with Maven (default)"
            Write-Host "  maven status   " -NoNewline -ForegroundColor Yellow
            Write-Host "- Show container status and recent logs"
            Write-Host "  maven logs     " -NoNewline -ForegroundColor Yellow
            Write-Host "- Follow container logs in real-time"
            Write-Host "  maven restart  " -NoNewline -ForegroundColor Yellow
            Write-Host "- Restart the Maven container"
            Write-Host "  maven build    " -NoNewline -ForegroundColor Yellow
            Write-Host "- Rebuild the Maven container"
            Write-Host "  maven help     " -NoNewline -ForegroundColor Yellow
            Write-Host "- Show this help message"
            Write-Host "`nInside the interactive CLI:" -ForegroundColor Cyan
            Write-Host "  context        " -NoNewline -ForegroundColor Yellow
            Write-Host "- Show Maven's loaded context"
            Write-Host "  help           " -NoNewline -ForegroundColor Yellow
            Write-Host "- Show CLI commands"
            Write-Host "  clear          " -NoNewline -ForegroundColor Yellow
            Write-Host "- Clear conversation history"
            Write-Host "  exit           " -NoNewline -ForegroundColor Yellow
            Write-Host "- Leave the session"
            Write-Host "`n" -NoNewline
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
        }

        default {
            # Default action: Jump into interactive CLI
            Write-Host "💎 " -NoNewline -ForegroundColor Magenta
            Write-Host "Connecting to Maven..." -ForegroundColor Cyan

            # Check if container is running first
            $containerStatus = docker ps --filter "name=maven" --format "{{.Status}}"
            if (-not $containerStatus) {
                Write-Host "`n❌ Maven container is not running!" -ForegroundColor Red
                Write-Host "   Start with: docker-compose up -d" -ForegroundColor Yellow
                return
            }

            # Exec into container
            docker exec -it maven python -m claude.interactive
        }
    }
}

# Show help on import
Write-Host "`n💎 " -NoNewline -ForegroundColor Magenta
Write-Host "Maven PowerShell helper loaded!" -ForegroundColor Cyan
Write-Host "   Type 'maven' to chat with Maven" -ForegroundColor Gray
Write-Host "   Type 'maven help' for all commands`n" -ForegroundColor Gray
