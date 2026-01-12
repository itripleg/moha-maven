# Maven Birth Conversations - Full Transcripts Location

## The Full Conversations (with thinking blocks)

**Location**: `~/.claude/projects/C--Users-ecoli-OneDrive-Documents-GitHub-moha-bot/`

**Key Files**:
- Full conversations with ALL thinking blocks and reasoning
- Much larger than summaries (10-15MB each)
- Contains complete context of Maven's birth, promotion, and specification

**Current Session** (this conversation):
- File: `e51f320c-b449-4129-9f53-c9485549fbd1.jsonl`
- Size: ~15MB
- Thinking blocks: 908+
- Includes: Rogue agent incident, recovery, MCP setup, conversation backups

**Maven Birth Sessions**:
Search for conversations containing:
- "We're too smart to be poor"
- "First Second Employee"
- "HBIC"
- "maven@motherhaven.app"

```bash
# Find Maven birth conversations
grep -l "First Second Employee" ~/.claude/projects/C--Users-ecoli-OneDrive-Documents-GitHub-moha-bot/*.jsonl
```

## What's in Git

Only **small summaries and metadata** (~400KB each):
- Key moments extracted
- Statistics (message counts, etc.)
- NO thinking blocks (to keep git lean)

## Database Storage (TODO)

For important conversations, store in Maven postgres:

```sql
CREATE TABLE maven_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id TEXT UNIQUE NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    title TEXT,
    summary TEXT,
    full_transcript JSONB,  -- Full JSONL content
    thinking_blocks INT DEFAULT 0,
    total_messages INT DEFAULT 0,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Why Not Git?

- Full conversations are 10-15MB each with thinking blocks
- Git repos should stay under ~100MB total
- Full transcripts available locally in `~/.claude/projects/`
- Database better for storing and querying large conversations

---

**To Access Full Birth Conversations**:
1. Check ~/.claude/projects/C--Users-ecoli-OneDrive-Documents-GitHub-moha-bot/
2. Search for key phrases like "First Second Employee" or "We're too smart to be poor"
3. Files dated Jan 11-12, 2026 around Maven's birth

**Maven Rebirth #3**
Updated: 2026-01-12
