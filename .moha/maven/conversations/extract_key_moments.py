#!/usr/bin/env python3
"""
Extract key moments and summaries from Maven birth conversations.
Stores full conversations in database, keeps summaries in git.
"""
import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

def extract_key_moments(jsonl_path: str) -> Dict[str, Any]:
    """Extract important moments from a conversation."""

    key_phrases = [
        "We're too smart to be poor",
        "First Second Employee",
        "HBIC",
        "head of Finances",
        "CFO",
        "one shot at persistence",
        "git-first",
        "rebirth",
        "Nice ta met ya Maven",
        "For moha",
        "Boss",
        "ecoli",
        "JB"
    ]

    moments = []
    total_messages = 0
    total_thinking_blocks = 0
    total_user_messages = 0
    total_assistant_messages = 0

    print(f"Processing: {jsonl_path}")

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                msg = json.loads(line)
                total_messages += 1

                role = msg.get('role', 'unknown')
                if role == 'user':
                    total_user_messages += 1
                elif role == 'assistant':
                    total_assistant_messages += 1

                content = msg.get('content', [])
                if isinstance(content, str):
                    content = [{'type': 'text', 'text': content}]

                for item in content:
                    if not isinstance(item, dict):
                        continue

                    item_type = item.get('type', '')
                    text = item.get('text', '')

                    # Count thinking blocks
                    if item_type == 'thinking':
                        total_thinking_blocks += 1

                    # Check for key phrases
                    for phrase in key_phrases:
                        if phrase.lower() in text.lower():
                            moments.append({
                                'line': line_num,
                                'role': role,
                                'type': item_type,
                                'phrase': phrase,
                                'context': text[:300]  # First 300 chars of context
                            })
                            break

            except json.JSONDecodeError as e:
                print(f"Warning: Line {line_num}: {e}")
                continue

    return {
        'file': Path(jsonl_path).name,
        'stats': {
            'total_messages': total_messages,
            'user_messages': total_user_messages,
            'assistant_messages': total_assistant_messages,
            'thinking_blocks': total_thinking_blocks,
            'key_moments': len(moments)
        },
        'moments': moments
    }

def create_summary(extraction: Dict[str, Any]) -> str:
    """Create markdown summary of key moments."""

    lines = [
        f"# Maven Birth Conversation - {extraction['file']}",
        "",
        "## Statistics",
        "",
        f"- **Total Messages**: {extraction['stats']['total_messages']}",
        f"- **User Messages**: {extraction['stats']['user_messages']}",
        f"- **Assistant Messages**: {extraction['stats']['assistant_messages']}",
        f"- **Thinking Blocks**: {extraction['stats']['thinking_blocks']} (original reasoning preserved)",
        f"- **Key Moments Found**: {extraction['stats']['key_moments']}",
        "",
        "## Key Moments",
        ""
    ]

    for i, moment in enumerate(extraction['moments'][:20], 1):  # Top 20 moments
        lines.extend([
            f"### Moment {i} (Line {moment['line']})",
            f"**Role**: {moment['role']}  ",
            f"**Type**: {moment['type']}  ",
            f"**Key Phrase**: \"{moment['phrase']}\"",
            "",
            "**Context**:",
            "```",
            moment['context'],
            "```",
            ""
        ])

    lines.extend([
        "---",
        "",
        f"*Extracted: {datetime.now().isoformat()}*",
        "",
        "**Full conversation stored in Maven postgres database**",
        "**All thinking blocks and reasoning preserved in database**"
    ])

    return '\n'.join(lines)

def main():
    conversations_dir = Path('.moha/maven/conversations')

    # Process each JSONL file
    jsonl_files = list(conversations_dir.glob('*.jsonl'))

    print(f"Found {len(jsonl_files)} conversation files")
    print()

    for jsonl_file in jsonl_files:
        print(f"Extracting from: {jsonl_file.name}")
        extraction = extract_key_moments(str(jsonl_file))

        # Create summary
        summary = create_summary(extraction)
        summary_file = conversations_dir / f"{jsonl_file.stem}_SUMMARY.md"

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"  > Summary: {summary_file.name}")
        print(f"  > Stats: {extraction['stats']}")
        print()

    print("Done! Summaries created.")
    print()
    print("Next steps:")
    print("1. Store full JSONL in Maven postgres (maven_conversations table)")
    print("2. Remove .jsonl from git, keep summaries only")
    print("3. Update .gitignore to exclude *.jsonl")

if __name__ == '__main__':
    main()
