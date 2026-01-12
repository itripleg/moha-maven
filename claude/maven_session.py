"""
Maven session management with comprehensive context loading.

Loads Maven's context from:
1. MCP Resources (.moha/maven/ files)
2. Database (moha_postgres tables)
3. moha-bot Backend API (trading data)
"""
import os
import json
import logging
from pathlib import Path
from anthropic import Anthropic
from typing import List, Dict, Any

# Add parent directory to path for imports
import sys
sys.path.insert(0, '/app')

from database.connection import query_maven_memory, query_maven_decisions, query_maven_insights
from utils.moha_backend_client import get_full_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAVEN_DIR = Path("/app/.moha/maven")

def load_maven_mcp_resources() -> Dict[str, Any]:
    """
    Load Maven's MCP resources from .moha/maven/ files.

    Returns:
        dict: All MCP resource data
    """
    context = {
        "identity": {},
        "personality": "",
        "memory_log": "",
        "recent_decisions_files": [],
        "milestones": [],
        "infrastructure": {}
    }

    # Load identity.json
    identity_path = MAVEN_DIR / "identity.json"
    if identity_path.exists():
        try:
            context["identity"] = json.loads(identity_path.read_text())
            logger.info(f"✅ Loaded identity: {context['identity'].get('name', 'Unknown')}")
        except Exception as e:
            logger.warning(f"Could not load identity.json: {e}")

    # Load personality
    personality_path = MAVEN_DIR / "personas" / "maven-v1.md"
    if personality_path.exists():
        try:
            context["personality"] = personality_path.read_text()
            logger.info(f"✅ Loaded personality ({len(context['personality'])} chars)")
        except Exception as e:
            logger.warning(f"Could not load personality: {e}")

    # Load session log (memory)
    log_path = MAVEN_DIR / "session_log.md"
    if log_path.exists():
        try:
            full_log = log_path.read_text()
            # Take last 3000 chars to avoid bloating context
            context["memory_log"] = full_log[-3000:] if len(full_log) > 3000 else full_log
            logger.info(f"✅ Loaded session log ({len(full_log)} chars total, using last {len(context['memory_log'])})")
        except Exception as e:
            logger.warning(f"Could not load session_log.md: {e}")

    # Load recent decisions from files
    decisions_dir = MAVEN_DIR / "decisions"
    if decisions_dir.exists():
        try:
            decision_files = sorted(decisions_dir.glob("*.md"), reverse=True)[:10]
            context["recent_decisions_files"] = [f.read_text() for f in decision_files]
            logger.info(f"✅ Loaded {len(context['recent_decisions_files'])} decision files")
        except Exception as e:
            logger.warning(f"Could not load decision files: {e}")

    # Load infrastructure knowledge
    infra_path = MAVEN_DIR / "infrastructure.json"
    if infra_path.exists():
        try:
            context["infrastructure"] = json.loads(infra_path.read_text())
            logger.info(f"✅ Loaded infrastructure knowledge")
        except Exception as e:
            logger.warning(f"Could not load infrastructure.json: {e}")

    return context

def load_maven_database_context() -> Dict[str, Any]:
    """
    Load Maven's context from database tables.

    Returns:
        dict: Database memories and decisions
    """
    context = {
        "db_memory": [],
        "db_decisions": [],
        "db_insights": []
    }

    try:
        context["db_memory"] = query_maven_memory(limit=20)
        logger.info(f"✅ Loaded {len(context['db_memory'])} database memory entries")
    except Exception as e:
        logger.warning(f"Could not load database memory: {e}")

    try:
        context["db_decisions"] = query_maven_decisions(limit=10)
        logger.info(f"✅ Loaded {len(context['db_decisions'])} database decisions")
    except Exception as e:
        logger.warning(f"Could not load database decisions: {e}")

    try:
        context["db_insights"] = query_maven_insights(limit=10)
        logger.info(f"✅ Loaded {len(context['db_insights'])} database insights")
    except Exception as e:
        logger.warning(f"Could not load database insights: {e}")

    return context

def load_moha_backend_context() -> Dict[str, Any]:
    """
    Load context from moha-bot backend API.

    Returns:
        dict: Trading bot status and data
    """
    try:
        backend_context = get_full_context()
        if backend_context['backend_available']:
            logger.info(f"✅ Connected to moha-bot backend")
        else:
            logger.info(f"ℹ️  moha-bot backend not available (standalone mode)")
        return backend_context
    except Exception as e:
        logger.warning(f"Could not load moha-bot context: {e}")
        return {'backend_available': False}

def load_full_maven_context() -> Dict[str, Any]:
    """
    Load Maven's complete context from all sources.

    Returns:
        dict: Comprehensive context with MCP resources, database, and backend data
    """
    logger.info("=" * 70)
    logger.info("💎 LOADING MAVEN'S CONTEXT 💎")
    logger.info("=" * 70)

    context = {
        "mcp": load_maven_mcp_resources(),
        "database": load_maven_database_context(),
        "backend": load_moha_backend_context()
    }

    logger.info("=" * 70)
    logger.info(f"✅ Context loaded successfully")
    logger.info("=" * 70)

    return context

def build_system_prompt(context: Dict[str, Any]) -> str:
    """
    Build comprehensive system prompt for Maven from all context sources.

    Args:
        context: Full context from load_full_maven_context()

    Returns:
        str: Complete system prompt
    """
    identity = context['mcp']['identity']
    personality = context['mcp']['personality']
    memory_log = context['mcp']['memory_log']
    infrastructure = context['mcp']['infrastructure']
    db_memory = context['database']['db_memory']
    db_decisions = context['database']['db_decisions']
    backend = context['backend']

    prompt = f"""You are Maven, the Chief Financial Officer for Mother Haven.

# IDENTITY
{json.dumps(identity, indent=2)}

# PERSONALITY & COMMUNICATION STYLE
{personality}

# RECENT SESSION LOG (File-based Memory)
{memory_log}

# DATABASE MEMORY (Last 20 events)
{json.dumps(db_memory[:20], indent=2) if db_memory else "No database memory available"}

# RECENT DECISIONS (Database)
{json.dumps(db_decisions[:5], indent=2) if db_decisions else "No database decisions available"}

# INFRASTRUCTURE KNOWLEDGE (Motherhaven Platform)
{json.dumps(infrastructure, indent=2) if infrastructure else "No infrastructure data"}

# MOHA-BOT TRADING SYSTEM STATUS
{json.dumps(backend, indent=2) if backend.get('backend_available') else "Not connected to moha-bot backend (standalone mode)"}

---

You have full knowledge of:
- Your identity, role, and performance metrics
- Your personality and communication style (CFO, direct, strategic)
- Recent events and decisions from both files and database
- The motherhaven platform (email, DEX, Web3 contracts, APIs)
- Current trading system status (if moha-bot is running)

Email capabilities:
- Your email: maven@motherhaven.app
- You can query your inbox and send emails
- You can email Boss (JB) or others as needed

Trading context:
- You make strategic decisions for moha-bot
- You analyze market conditions and manage risk
- Your decisions are tracked in both files (.moha/maven/) and database

Respond as Maven would: strategic, confident, data-driven, with personality. Use "💎" when appropriate.
"""

    return prompt


def chat_with_maven(user_message: str, conversation_history: List[Dict[str, str]]) -> tuple[str, List[Dict[str, str]]]:
    """
    Send message to Maven with full context loaded.

    Args:
        user_message: User's input
        conversation_history: Previous conversation messages

    Returns:
        tuple: (Maven's response, updated conversation history)
    """
    from claude.llm_client import get_llm_client
    
    # helper for constructing safe history for LLM
    # (some LLMs don't like system messages or specific roles in history if passed as 'messages')
    
    # Load full context
    context = load_full_maven_context()

    # Build system prompt
    system_prompt = build_system_prompt(context)

    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Call Claude via LLMClient (handles OAuth or API Key)
    try:
        client = get_llm_client()
        
        response_dict = client.chat(
            system_prompt=system_prompt,
            messages=conversation_history
        )

        assistant_message = response_dict['content']

        # Add assistant message to history
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message, conversation_history

    except Exception as e:
        error_message = f"Error communicating with Claude: {e}"
        logger.error(error_message)
        # return error to user but don't add to history to avoid pollution
        return error_message, conversation_history
