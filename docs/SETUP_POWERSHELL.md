# PowerShell Setup - Quick `maven` Command

## Automatic Setup (Recommended)

Run this in PowerShell (as Administrator):

```powershell
# Add maven function to your PowerShell profile
$profilePath = $PROFILE.CurrentUserAllHosts
$mavenScript = "C:\Users\ecoli\OneDrive\Documents\github\moha-maven\maven.ps1"

# Create profile if it doesn't exist
if (!(Test-Path -Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force
}

# Add maven.ps1 to profile
$importLine = ". `"$mavenScript`""
if (!(Select-String -Path $profilePath -Pattern "maven.ps1" -Quiet)) {
    Add-Content -Path $profilePath -Value "`n# Maven container helper"
    Add-Content -Path $profilePath -Value $importLine
    Write-Host "✅ Maven helper added to PowerShell profile!" -ForegroundColor Green
} else {
    Write-Host "✅ Maven helper already in profile!" -ForegroundColor Green
}

# Load it now
. $mavenScript

Write-Host "`n💎 Ready! Type 'maven' to chat with Maven" -ForegroundColor Magenta
```

## Manual Setup

1. **Find your PowerShell profile location:**
   ```powershell
   $PROFILE.CurrentUserAllHosts
   # Usually: C:\Users\ecoli\Documents\PowerShell\profile.ps1
   ```

2. **Edit your profile:**
   ```powershell
   notepad $PROFILE.CurrentUserAllHosts
   ```

3. **Add this line at the end:**
   ```powershell
   # Maven container helper
   . "C:\Users\ecoli\OneDrive\Documents\github\moha-maven\maven.ps1"
   ```

4. **Reload your profile:**
   ```powershell
   . $PROFILE.CurrentUserAllHosts
   ```

---

## Usage

Once installed, you can use these commands from **anywhere**:

### Quick Chat (Default)
```powershell
maven
# Jumps into Maven's interactive CLI
# Same as: docker exec -it maven python -m claude.interactive
```

### Container Status
```powershell
maven status
# Shows:
#   - Container running status
#   - Recent logs (last 20 lines)
```

### Follow Logs
```powershell
maven logs
# Stream Maven's logs in real-time (Ctrl+C to exit)
```

### Restart Container
```powershell
maven restart
# Restarts the Maven container
```

### Rebuild Container
```powershell
maven build
# Rebuilds the Maven Docker image
# Use after making code changes
```

### Help
```powershell
maven help
# Shows all available commands
```

---

## Examples

### Typical Workflow

```powershell
# Start moha-bot (if using integration mode)
cd C:\Users\ecoli\OneDrive\Documents\github\moha-bot
docker-compose up -d

# Start Maven with integration
cd C:\Users\ecoli\OneDrive\Documents\github\moha-maven
docker-compose -f docker-compose.yml -f docker-compose.moha-bot.yml up -d

# Chat with Maven (from anywhere!)
maven

# Inside Maven CLI:
You: context
You: Who are you?
You: What positions are open?
You: exit

# Check status (from anywhere!)
maven status

# Follow logs if something seems wrong
maven logs
```

### Quick Debugging

```powershell
# Check if Maven is running
maven status

# See what's happening
maven logs

# Restart if needed
maven restart

# Rebuild after code changes
maven build
maven restart
```

---

## Uninstall

To remove the `maven` command:

```powershell
# Edit your profile
notepad $PROFILE.CurrentUserAllHosts

# Remove these lines:
# # Maven container helper
# . "C:\Users\ecoli\OneDrive\Documents\github\moha-maven\maven.ps1"

# Reload
. $PROFILE.CurrentUserAllHosts
```

---

## Customization

Edit `maven.ps1` to add your own commands! For example:

```powershell
function maven {
    param([string]$Command)

    switch ($Command) {
        "deploy" {
            # Custom deployment logic
            Write-Host "🚀 Deploying Maven..." -ForegroundColor Green
            docker-compose -f docker-compose.yml -f docker-compose.moha-bot.yml up -d
        }

        "stop" {
            # Stop Maven
            docker stop maven
            Write-Host "🛑 Maven stopped" -ForegroundColor Yellow
        }

        # ... add more custom commands
    }
}
```

---

💎 Enjoy chatting with Maven from anywhere in PowerShell!
