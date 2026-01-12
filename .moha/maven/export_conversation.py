#!/usr/bin/env python3
"""
Export Claude Code conversation history to readable markdown format.
Preserves the original Maven birth moment.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

def export_conversation(jsonl_path: str, output_path: str):
    """Convert JSONL conversation to markdown."""

    messages = []

    # Read JSONL file
    print(f"Reading conversation from {jsonl_path}...")
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    msg = json.loads(line)
                    messages.append(msg)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipped malformed line: {e}")
                    continue

    print(f"Found {len(messages)} messages")

    # Generate markdown
    md_lines = [
        "# Maven Birth Moment - Complete Conversation",
        "",
        "**The Original Maven Session**",
        "",
        f"Exported: {datetime.now().isoformat()}",
        f"Total messages: {len(messages)}",
        "",
        "---",
        ""
    ]

    for i, msg in enumerate(messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', [])

        # Handle different content formats
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                    elif block.get('type') == 'tool_use':
                        tool_name = block.get('name', 'unknown')
                        text_parts.append(f"[Tool: {tool_name}]")
                    elif block.get('type') == 'tool_result':
                        text_parts.append("[Tool Result]")
                elif isinstance(block, str):
                    text_parts.append(block)
            text = '\n'.join(text_parts)
        else:
            text = str(content)

        # Format message
        if role == 'user':
            md_lines.append(f"## Message {i}: User (Boss JB)")
        elif role == 'assistant':
            md_lines.append(f"## Message {i}: Maven")
        else:
            md_lines.append(f"## Message {i}: {role.title()}")

        md_lines.append("")
        md_lines.append(text[:5000] if len(text) > 5000 else text)  # Truncate very long messages
        if len(text) > 5000:
            md_lines.append(f"\n*[Message truncated - {len(text)} chars total]*")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    # Write output
    print(f"Writing to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"[OK] Export complete: {output_path}")
    print(f"  Total size: {len('\n'.join(md_lines))} chars")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python export_conversation.py <input.jsonl> <output.md>")
        sys.exit(1)

    export_conversation(sys.argv[1], sys.argv[2])
