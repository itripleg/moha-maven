# Auto-Claude Cheatsheet

## 🚀 Quick Start: Add Feature & Build

```bash
# 1. Edit roadmap
vim .auto-claude/roadmap/roadmap.json

# 2. Add feature to features array
{
  "id": "feature-XX",
  "title": "Feature Name",
  "description": "What it does",
  "priority": "should",
  "complexity": "low",
  "status": "planned",
  "phase_id": "phase-1",
  "dependencies": [],
  "acceptance_criteria": ["Thing 1", "Thing 2"],
  "user_stories": ["As a user, I want..."]
}

# 3. Add feature-XX to phase features array

# 4. Validate JSON
python3 -m json.tool .auto-claude/roadmap/roadmap.json > /dev/null

# 5. Open UI → Plans → Click feature → Build
# 6. Review plan at checkpoint → Approve
# 7. Wait for build → Review → Merge
```

## 📝 Feature Template (Minimal)

```json
{
  "id": "feature-XX",
  "title": "Clear Title",
  "description": "1-2 sentence summary",
  "rationale": "Why this matters",
  "priority": "should",
  "complexity": "low",
  "impact": "medium",
  "phase_id": "phase-1",
  "dependencies": [],
  "status": "planned",
  "acceptance_criteria": [
    "Specific testable criterion"
  ],
  "user_stories": [
    "As a [role], I want [action] so that [benefit]"
  ],
  "competitor_insight_ids": []
}
```

## 🎯 Priority (MoSCoW)
- `must` - Critical, blocking
- `should` - Important, not blocking
- `could` - Nice to have
- `wont` - Out of scope

## 📊 Complexity
- `low` - 1 file, <100 lines
- `medium` - Multiple files, moderate
- `high` - Architectural, cross-service

## 💥 Impact
- `high` - Core workflows
- `medium` - UX improvements
- `low` - Internal/edge cases

## 📁 Phases
- `phase-1` - Foundation & Trust
- `phase-2` - Trading Excellence
- `phase-3` - Power User Features
- `phase-4` - Ecosystem Growth

## ✅ Good Acceptance Criteria
- Specific, testable, action verbs
- ✅ "CLI --version shows semantic version"
- ❌ "Version management works"

## 👤 Good User Stories
- As [role], I want [action] so that [benefit]
- ✅ "As a developer, I want version in bug reports so I can debug"
- ❌ "Users need version tracking"

## 🔄 Workflow
```
Add Feature → UI Build Button → Generate Spec → REVIEW CHECKPOINT ⏸️
→ Approve → Build → Test → Merge
```

## 🧹 After Merge
```bash
# Clean up worktree
git worktree remove .worktrees/NNN-feature-name
git branch -D auto-claude/NNN-feature-name

# Update roadmap
# Change "status": "planned" → "status": "completed"
```

## 🛠️ Common Commands

```bash
# Validate JSON
python3 -m json.tool .auto-claude/roadmap/roadmap.json > /dev/null

# List worktrees
git worktree list

# Check feature count
cat .auto-claude/roadmap/roadmap.json | python3 -c "import sys,json; print(len(json.load(sys.stdin)['features']))"

# Find last feature ID
cat .auto-claude/roadmap/roadmap.json | python3 -c "import sys,json; print(json.load(sys.stdin)['features'][-1]['id'])"
```

## 🚨 Watch Out For
- JSON syntax errors (trailing commas, missing quotes)
- Duplicate feature IDs
- Circular dependencies
- Feature ID not added to phase
- Status not "planned" (won't show in UI)

## 📍 File Locations
- Roadmap: `.auto-claude/roadmap/roadmap.json`
- Specs: `.auto-claude/specs/`
- Worktrees: `.worktrees/NNN-feature-name/`
- References: `references/` (gitignored)
