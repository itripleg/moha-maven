"""
Interactive CLI for chatting with Maven in her container.

Usage:
    docker exec -it maven python -m claude.interactive

Maven loads her full context from:
- MCP resources (.moha/maven/ files)
- Database (maven_memory, maven_decisions, maven_insights)
- moha-bot backend API (trading status, positions, account)
"""
import sys
import json
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

# Add parent directory to path
sys.path.insert(0, '/app')

from claude.maven_session import chat_with_maven, load_full_maven_context

# CLI styling
style = Style.from_dict({
    'prompt': '#00d7ff bold',
    'maven': '#ff00ff bold',
})

def show_context():
    """Display Maven's loaded context summary."""
    print("\n" + "=" * 70)
    print("💎 MAVEN CONTEXT 💎")
    print("=" * 70)

    try:
        context = load_full_maven_context()

        # Identity
        identity = context['mcp']['identity']
        print(f"\n📋 Identity:")
        print(f"  Name: {identity.get('name', 'Unknown')}")
        print(f"  Email: {identity.get('contact', {}).get('email', 'N/A')}")
        print(f"  Role: {identity.get('role', 'N/A')}")
        print(f"  Total Decisions: {identity.get('performance_tracking', {}).get('total_decisions', 0)}")

        # MCP Resources
        print(f"\n📁 MCP Resources:")
        print(f"  Identity: {'✓' if context['mcp']['identity'] else '✗'}")
        print(f"  Personality: {'✓' if context['mcp']['personality'] else '✗'}")
        print(f"  Session Log: {'✓' if context['mcp']['memory_log'] else '✗'} ({len(context['mcp']['memory_log'])} chars)")
        print(f"  Decision Files: {len(context['mcp']['recent_decisions_files'])}")
        print(f"  Infrastructure: {'✓' if context['mcp']['infrastructure'] else '✗'}")

        # Database
        print(f"\n🗄️  Database:")
        print(f"  Memory Entries: {len(context['database']['db_memory'])}")
        print(f"  Decisions: {len(context['database']['db_decisions'])}")
        print(f"  Insights: {len(context['database']['db_insights'])}")

        # Backend
        print(f"\n🔗 moha-bot Backend:")
        backend = context['backend']
        if backend.get('backend_available'):
            print(f"  Status: ✓ Connected")
            if backend.get('bot_status'):
                print(f"  Bot: {json.dumps(backend['bot_status'], indent=4)}")
            if backend.get('positions'):
                print(f"  Positions: {len(backend.get('positions', []))} open")
            if backend.get('account'):
                print(f"  Account: ${backend.get('account', {}).get('balance', 'N/A')}")
        else:
            print(f"  Status: ✗ Not connected (standalone mode)")

        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error loading context: {e}\n")

def show_help():
    """Show available commands."""
    print("\n" + "=" * 70)
    print("💎 MAVEN COMMANDS 💎")
    print("=" * 70)
    print("\nCommands:")
    print("  'exit' or 'quit'  - Leave session")
    print("  'context'         - Show loaded MCP context and database connections")
    print("  'clear'           - Clear conversation history")
    print("  'help'            - Show this help message")
    print("\nMaven has access to:")
    print("  • Her identity, personality, and memory")
    print("  • Recent decisions and milestones")
    print("  • Motherhaven infrastructure knowledge")
    print("  • Database memories (if tables exist)")
    print("  • moha-bot trading data (if backend is running)")
    print("  • Email capabilities (maven@motherhaven.app)")
    print("=" * 70 + "\n")

def main():
    """Main interactive loop."""
    conversation_history = []

    print("=" * 70)
    print("💎 MAVEN ONLINE 💎")
    print("=" * 70)
    print("\nChief Financial Officer, Mother Haven Treasury")
    print("Loading full context (MCP + Database + Backend)...")
    print("\nCommands: 'exit', 'context', 'clear', 'help'")
    print("=" * 70 + "\n")

    # Show help on start
    show_help()

    while True:
        try:
            user_input = prompt(
                "You: ",
                history=FileHistory('/app/.maven_history'),
                style=style
            )

            if not user_input.strip():
                continue

            # Handle commands
            if user_input.lower() in ['exit', 'quit']:
                print("\n💎 Maven signing off. For moha. 🚀\n")
                break

            if user_input.lower() == 'context':
                show_context()
                continue

            if user_input.lower() == 'clear':
                conversation_history = []
                print("\n[Conversation history cleared]\n")
                continue

            if user_input.lower() == 'help':
                show_help()
                continue

            # Chat with Maven
            print("\nMaven: ", end='', flush=True)
            response, conversation_history = chat_with_maven(user_input, conversation_history)
            print(f"{response}\n")

        except KeyboardInterrupt:
            print("\n\n💎 Maven signing off. For moha. 🚀\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
