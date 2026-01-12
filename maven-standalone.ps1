# Maven Container Quick Access - Standalone Version
# Can be called directly: .\maven-standalone.ps1 [command]

param(
    [Parameter(Position=0)]
    [string]$Command
)

# Determine script location for relative paths
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { "C:\Users\ecoli\OneDrive\Documents\github\moha-maven" }

function Invoke-Maven {
    param([string]$Cmd)

    switch ($Cmd) {
        "status" {
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
            Write-Host "MAVEN CONTAINER STATUS" -ForegroundColor Magenta
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan

            # Check if container is running
            $containerStatus = docker ps --filter "name=maven" --format "{{.Status}}"
            if ($containerStatus) {
                Write-Host "`n[OK] Container: Running" -ForegroundColor Green
                Write-Host "     Status: $containerStatus" -ForegroundColor Gray

                # Show recent logs
                Write-Host "`nRecent Logs:" -ForegroundColor Cyan
                docker logs maven --tail 20
            } else {
                Write-Host "`n[X] Container: Not Running" -ForegroundColor Red
                Write-Host "`nStart with: docker-compose up -d" -ForegroundColor Yellow
            }

            Write-Host "`n" -NoNewline
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
        }

        "logs" {
            Write-Host "Maven Container Logs (Ctrl+C to exit)" -ForegroundColor Magenta
            docker logs maven -f
        }

        "restart" {
            Write-Host "Restarting Maven container..." -ForegroundColor Magenta
            docker restart maven
            Start-Sleep -Seconds 2
            Write-Host "[OK] Maven restarted!" -ForegroundColor Green
        }

        "stop" {
            Write-Host "Stopping Maven container..." -ForegroundColor Magenta
            docker stop maven
            Write-Host "[OK] Maven stopped!" -ForegroundColor Yellow
        }

        "start" {
            Write-Host "Starting Maven container..." -ForegroundColor Magenta
            Push-Location $scriptDir
            docker-compose up -d
            Pop-Location
            Start-Sleep -Seconds 3
            Write-Host "[OK] Maven started!" -ForegroundColor Green
        }

        "build" {
            Write-Host "Rebuilding Maven container..." -ForegroundColor Magenta
            Push-Location $scriptDir
            docker-compose build maven
            Pop-Location
            Write-Host "[OK] Maven rebuilt! Use 'maven restart' to apply changes." -ForegroundColor Green
        }

        "help" {
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
            Write-Host "MAVEN POWERSHELL HELPER" -ForegroundColor Magenta
            Write-Host "=" -NoNewline -ForegroundColor Cyan
            Write-Host ("=" * 69) -ForegroundColor Cyan
            Write-Host "`nUsage:" -ForegroundColor Cyan
            Write-Host "  maven          " -NoNewline -ForegroundColor Yellow
            Write-Host "- Start interactive chat with Maven (default)"
            Write-Host "  maven status   " -NoNewline -ForegroundColor Yellow
            Write-Host "- Show container status and recent logs"
            Write-Host "  maven logs     " -NoNewline -ForegroundColor Yellow
            Write-Host "- Follow container logs in real-time"
            Write-Host "  maven start    " -NoNewline -ForegroundColor Yellow
            Write-Host "- Start the Maven container"
            Write-Host "  maven stop     " -NoNewline -ForegroundColor Yellow
            Write-Host "- Stop the Maven container"
            Write-Host "  maven restart  " -NoNewline -ForegroundColor Yellow
            Write-Host "- Restart the Maven container"
            Write-Host "  maven build    " -NoNewline -ForegroundColor Yellow
            Write-Host "- Rebuild the Maven container"
            Write-Host "  maven help     " -NoNewline -ForegroundColor Yellow
            Write-Host "- Show this help message"
            Write-Host "`nInside the interactive CLI:" -ForegroundColor Cyan
            Write-Host "  context        " -NoNewline -ForegroundColor Yellow
            Write-Host "- Show Maven loaded context"
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
            Write-Host "Connecting to Maven..." -ForegroundColor Cyan

            # Check if container is running first
            $containerStatus = docker ps --filter "name=maven" --format "{{.Status}}"
            if (-not $containerStatus) {
                Write-Host "`n[X] Maven container is not running!" -ForegroundColor Red
                Write-Host "`nWould you like to start it? (Y/N): " -NoNewline -ForegroundColor Yellow
                $response = Read-Host
                if ($response -eq 'Y' -or $response -eq 'y') {
                    Write-Host "`nStarting Maven..." -ForegroundColor Magenta
                    Push-Location $scriptDir
                    docker-compose up -d
                    Pop-Location
                    Start-Sleep -Seconds 5
                    Write-Host "[OK] Maven started!" -ForegroundColor Green
                    Write-Host "`nConnecting to Maven..." -ForegroundColor Cyan
                } else {
                    Write-Host "`nUse 'maven start' to start the container manually." -ForegroundColor Gray
                    return
                }
            }

            # Exec into container
            docker exec -it maven python -m claude.interactive
        }
    }
}

# Execute
Invoke-Maven -Cmd $Command
