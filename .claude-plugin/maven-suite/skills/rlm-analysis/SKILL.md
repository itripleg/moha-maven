# RLM Analysis Skill

Analyze arbitrarily large documents using Maven's Recursive Language Model implementation.

## Capability

This skill enables processing documents that exceed normal context limits by:
- Chunking large documents intelligently
- Processing chunks in parallel via subagents
- Synthesizing findings into coherent answers

## When to Use

- Analyzing documents over 50k characters
- Comparing multiple large files
- Extracting insights from extensive codebases
- Processing research papers and reports

## How It Works

```
Input Document (Any Size)
         │
    ┌────┴────┐
    │ Chunker │ Split into ~40k segments
    └────┬────┘
         │
    ┌────┴────┬────┬────┐
    ▼         ▼    ▼    ▼
[Processor][Proc][Proc][Proc]  Parallel analysis
    │         │    │    │
    └────┬────┴────┴────┘
         │
    ┌────┴────┐
    │Synthesize│  Combine findings
    └────┬────┘
         │
    Final Answer
```

## Commands

- `/maven:rlm-analyze <path> <query>` - Analyze a document
- `/maven:rlm-compare <paths...> <query>` - Compare multiple documents

## Agents Used

- `rlm-processor` (haiku) - Chunk analysis
- `rlm-synthesizer` (sonnet) - Result synthesis
