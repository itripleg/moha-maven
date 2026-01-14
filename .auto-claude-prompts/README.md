# Auto-Claude Prompts for Maven

This directory contains comprehensive prompts for auto-claude (AC) to autonomously implement large features for Maven, the CFO AI agent for MoHa.

## How to Use

1. Copy the full content of a prompt file
2. Paste into auto-claude with repo access
3. Let AC work autonomously with the harness
4. Review and test the implementation

## Prompts

### 01_complete_maven_infrastructure.md
**Status:** Ready
**Priority:** High
**Estimated Complexity:** Large (5 priorities, 6 scripts, 3 MCP resources)

Complete operational infrastructure for Maven to track money flowing through MoHa:
- Trade sync pipeline (MoHa → Maven)
- Portfolio snapshot automation (Hyperliquid API)
- Missing MCP resources (decisions/recent, performance/summary, portfolio/current)
- Recovery scripts (sync_from_git.py, verify_consistency.py)
- Performance analytics calculator

**Prerequisites:**
- maven_postgres running with 7 tables (✓ done)
- MCP server operational (✓ done)
- Git-first dual persistence working (✓ done)
- Access to moha_postgres (READ ONLY)
- Hyperliquid API address (env var)

**Success Criteria:**
- Can sync trades from MoHa bots
- Can take hourly portfolio snapshots
- Can rebuild DB from git after wipes
- Can calculate win rate, P&L, performance metrics

---

## Adding New Prompts

When adding new auto-claude prompts:

1. **Naming Convention:** `NN_descriptive_name.md`
   - NN = sequential number (01, 02, 03...)
   - Use underscores, lowercase
   - Be descriptive but concise

2. **Prompt Structure:**
   ```markdown
   # Auto-Claude Task: [Feature Name]

   ## Context
   [Current state, what exists, what's missing]

   ## Objective
   [What we're building]

   ## Tasks
   [Detailed requirements]

   ## Success Criteria
   [How to verify it works]
   ```

3. **Include:**
   - Full context (project structure, existing code)
   - Clear requirements with schemas/examples
   - Error handling expectations
   - Testing verification commands
   - Dependencies and environment variables

4. **Update this README** with prompt metadata

---

## Notes

- All prompts assume git-first architecture (git = source of truth)
- Maven postgres schema: see `database/schemas/maven_financial.sql`
- MCP server: see `maven_mcp/` directory
- Docker setup: see `docker-compose.yml`

For MoHa. 💎
