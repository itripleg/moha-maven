# Auto-Claude Workflow Quickstart

Quick reference for adding features and triggering builds in the auto-claude system.

## Adding Features to the Roadmap

**Location**: `.auto-claude/roadmap/roadmap.json`

### 1. Add Your Feature

Features go in the `features` array. Follow this structure:

```json
{
  "id": "feature-XX",  // Next sequential number
  "title": "Short, Clear Feature Name",
  "description": "What this feature does and why it matters. 1-2 sentences.",
  "rationale": "Why now? What problem does this solve? What's the user pain point?",
  "priority": "must|should|could|wont",  // MoSCoW prioritization
  "complexity": "low|medium|high",
  "impact": "low|medium|high",
  "phase_id": "phase-1",  // Which phase this belongs to
  "dependencies": ["feature-X", "feature-Y"],  // Other features needed first
  "status": "planned",  // planned|under_review|in_progress|completed
  "acceptance_criteria": [
    "Specific, testable criterion 1",
    "Specific, testable criterion 2",
    "Uses action verbs: includes, shows, allows, supports"
  ],
  "user_stories": [
    "As a [role], I want to [action] so that [benefit]",
    "As a [role], I want to [action] so that [benefit]"
  ],
  "competitor_insight_ids": []  // Leave empty for internal features
}
```

### 2. Add Feature ID to Phase

Find the phase in the `phases` array and add your feature ID:

```json
{
  "id": "phase-1",
  "name": "Foundation & Trust",
  "features": [
    "feature-1",
    "feature-2",
    "feature-23"  // <-- Add here
  ],
  ...
}
```

### 3. Update Metadata

Update the timestamp:

```json
"metadata": {
  "updated_at": "2025-12-27T19:50:00.000Z",
  ...
}
```

### 4. Validate JSON

```bash
python3 -m json.tool .auto-claude/roadmap/roadmap.json > /dev/null
```

If no errors, the JSON is valid.

## Triggering Builds from UI

### Method 1: From Roadmap (Recommended)

1. Open auto-claude UI
2. Navigate to **Plans** or **Roadmap** tab
3. Find your feature in the list (status: "planned")
4. Click **Build** or **Execute**
5. Auto-claude will:
   - Generate detailed spec from your feature
   - Create implementation plan
   - **PAUSE FOR APPROVAL** ⬅️ Review checkpoint
   - Wait for you to approve before building
   - Execute build phases

### Method 2: From Specs Directory

1. Create spec manually in `.auto-claude/specs/NNN-spec-name/spec.md`
2. Auto-claude picks it up automatically
3. Follows same approval workflow

## Build Workflow Phases

When you trigger a build, auto-claude goes through these phases:

### Planning Phase (Pre-Build)
1. **Discovery**: Understands the task from roadmap feature
2. **Requirements**: Gathers detailed requirements
3. **Complexity Assessment**: Determines workflow (quick/standard/comprehensive)
4. **Research**: Explores codebase (if needed)
5. **Context**: Gathers relevant files and patterns
6. **Spec Writing**: Creates detailed spec.md
7. **Planning**: Generates implementation_plan.json
8. **Validation**: Validates all spec files

### Review Checkpoint ⏸️
- **YOU REVIEW HERE** - Check the plan before build starts
- Approve or reject the plan
- This is where you prevent unwanted changes

### Building Phase (Post-Approval)
1. **Subtask Execution**: Works through implementation plan
2. **QA**: Tests the implementation
3. **Merge**: Commits to branch (you merge to main)

## Tips for Good Features

### Priority Guidelines (MoSCoW)
- **Must**: Critical for core functionality or blocking users
- **Should**: Important but system works without it
- **Could**: Nice to have, adds value
- **Won't**: Explicitly out of scope for now

### Complexity Assessment
- **Low**: Single file, < 100 lines, no new dependencies
- **Medium**: Multiple files, moderate logic, existing patterns
- **High**: Architectural changes, new systems, cross-service

### Impact Assessment
- **High**: Affects core user workflows or system stability
- **Medium**: Improves UX or adds secondary features
- **Low**: Internal improvements or edge case fixes

### Good Acceptance Criteria
✅ "CLI --version shows current semantic version"
✅ "API /health endpoint returns 200 with version in JSON"
❌ "Version management works"
❌ "Fix version issues"

### Good User Stories
✅ "As a developer, I want version info in bug reports so that I can reproduce issues"
❌ "Users need version tracking"
❌ "Make versioning better"

## Example: Version Management Feature

```json
{
  "id": "feature-23",
  "title": "Unified Version Management Across CLI and Services",
  "description": "Implement centralized version management that keeps CLI, API, Frontend, and documentation in sync.",
  "rationale": "CLI stuck at 0.1.0 despite major updates makes version meaningless for debugging and support.",
  "priority": "should",
  "complexity": "low",
  "impact": "medium",
  "phase_id": "phase-1",
  "dependencies": [],
  "status": "planned",
  "acceptance_criteria": [
    "Single source of truth for version number (pyproject.toml)",
    "CLI --version shows current version",
    "API /health endpoint returns version",
    "Frontend displays version in footer",
    "Semantic versioning (MAJOR.MINOR.PATCH)"
  ],
  "user_stories": [
    "As a user, I want to check my CLI version so that I know if I need to update",
    "As a developer, I want version info in bug reports so that I can reproduce issues"
  ]
}
```

## Common Patterns

### Adding to Existing Phase
Most features fit into existing phases. Use:
- **phase-1**: Foundation & Trust (docs, security, QoL)
- **phase-2**: Trading Excellence (core trading features)
- **phase-3**: Power User Features (advanced workflows)
- **phase-4**: Ecosystem Growth (community, scaling)

### No Dependencies
Use `"dependencies": []` when feature is standalone

### Internal Feature
Use `"competitor_insight_ids": []` for internal improvements

## Troubleshooting

### UI Doesn't Show Feature
- Check JSON is valid
- Refresh UI
- Check `status: "planned"` (not "completed")
- Verify feature ID added to phase

### Build Starts Without Approval
- This shouldn't happen - review checkpoint is mandatory
- Check auto-claude settings for `auto_approve` flag

### Spec Generation Fails
- Ensure `description` and `rationale` are detailed enough
- Check acceptance criteria are specific and testable
- Verify no circular dependencies

## Files Modified

When you add a feature:
- `.auto-claude/roadmap/roadmap.json` - Add feature definition
- `.auto-claude/specs/NNN-feature-name/` - Created by auto-claude during build

When build completes:
- Source code files (your actual implementation)
- Worktree in `.worktrees/NNN-feature-name/`
- Branch `auto-claude/NNN-feature-name`

## Next Steps After Build

1. **Review the implementation** in the worktree
2. **Test manually** if needed
3. **Merge to main** when satisfied
4. **Clean up worktree** after merge
5. **Update feature status** to "completed" in roadmap

---

**Quick Workflow Summary:**
1. Add feature to `.auto-claude/roadmap/roadmap.json`
2. Trigger build from UI
3. Review plan at checkpoint
4. Approve (build runs automatically)
5. Review implementation
6. Merge to main
