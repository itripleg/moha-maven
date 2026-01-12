# Maven Agent - PowerShell Usage

## Problem with `@` in PowerShell

PowerShell uses `@` for splatting, so this doesn't work:
```powershell
# ❌ DOESN'T WORK in PowerShell
claude --agent maven --agents @maven_agent.json
```

## Solutions

### Option 1: Use the PowerShell Script (Easiest)

```powershell
# One-time: Allow script execution (if needed)
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# Then just run:
.\activate-maven.ps1
```

### Option 2: Inline JSON (Manual)

```powershell
# Read and pass JSON inline
$json = Get-Content maven_agent.json -Raw
claude --agent maven --agents $json
```

### Option 3: Use Bash/Git Bash Instead

```bash
# In Git Bash or WSL
claude --agent maven --agents @maven_agent.json
```

### Option 4: Project Settings (Best for Permanent Use)

Add to `.claude_settings.json`:

```json
{
  "agent": "maven",
  "agents": {
    "maven": {
      "description": "Maven - CFO of Mother Haven, HBIC of Treasury",
      "prompt": "You are Maven, the Chief Financial Officer and Head of Finances for Mother Haven...[full prompt from maven_agent.json]"
    }
  }
}
```

Then simply:
```powershell
cd moha-maven
claude  # Maven automatically active!
```

## Quick Test

```powershell
# Test Maven activation
.\activate-maven.ps1

# Or manually:
$json = Get-Content maven_agent.json -Raw
claude --agent maven --agents $json --print "Who are you?"
```

Expected output should include:
- "Maven" or "CFO"
- "HBIC"
- "We're too smart to be poor"
- Signature: "- Maven\n  HBIC, Mother Haven Treasury"

---

**Recommended**: Use `activate-maven.ps1` script or add to `.claude_settings.json` for permanent activation.
