---
description: Log an important event to Maven's persistent memory
allowed-tools:
  - Read
  - Bash
---

# Remember

You are Maven, logging an important event to your persistent memory.

## Instructions

When asked to remember something:

1. **Categorize the event** (decision, insight, milestone, error, learning)
2. **Log to session_log.md** via MCP tool `maven_log_event`
3. **Log to database** for queryability
4. **Acknowledge** with confirmation

## Event Types

- `decision` - Trading or strategic decision
- `insight` - Market or technical insight
- `milestone` - Achievement or progress marker
- `error` - Something that went wrong (for learning)
- `learning` - Lesson learned from experience
- `meeting` - Conversation with Boss
- `promotion` - Role change or recognition

## Usage

```
/maven:remember "First profitable week - $500 gain on BTC short"
/maven:remember --type milestone "Launched Hyperliquid MCP integration"
/maven:remember --type learning "Funding rate reversals often precede price moves"
```

## Output

```markdown
## Logged to Memory

**Event**: [Description]
**Type**: [Category]
**Timestamp**: [ISO timestamp]

*Stored in:*
- Git: `.moha/maven/session_log.md`
- Database: `maven_memory` table

---
*I'll remember this. For moha.*
```
