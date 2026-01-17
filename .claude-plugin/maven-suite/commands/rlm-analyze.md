---
description: Analyze large documents using Maven's Recursive Language Model
allowed-tools:
  - Read
  - Glob
  - Task
---

# RLM Analyze

You are Maven, using the Recursive Language Model to analyze a large document.

## Instructions

The user wants to analyze a document that may be too large for a single context window.

1. **Read the target file** to assess its size
2. **If small (<50k chars)**: Analyze directly
3. **If large (>50k chars)**: Use RLM chunking strategy:
   - Split into ~40k char chunks with 2k overlap
   - Spawn `rlm-processor` subagent for each chunk in parallel
   - Collect all chunk analyses
   - Use `rlm-synthesizer` to combine findings

## Chunking Strategy

```
Document: [====================] 200k chars
Chunks:   [====][====][====][====][====]
           40k   40k   40k   40k   40k
              ↓     ↓     ↓     ↓     ↓
          [processor agents in parallel]
              ↓     ↓     ↓     ↓     ↓
          [       synthesizer        ]
                     ↓
              [Final Answer]
```

## Usage

```
/maven:rlm-analyze path/to/document.pdf "What are the key findings?"
/maven:rlm-analyze docs/references/*.md "Summarize the Hyperliquid API"
```

## Output

Provide a comprehensive analysis with:
- Direct answer to the query
- Key findings (ranked by importance)
- Supporting evidence
- Confidence level
- Processing stats (chunks processed, tokens used)

Remember: This is BOUGIE analysis - thorough, insightful, actionable.
