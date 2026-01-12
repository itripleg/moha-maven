"""
LLM Client for Claude-powered bot decisions.

Supports two authentication methods:
1. OAuth Token (CLAUDE_CODE_OAUTH_TOKEN) - Uses Claude Max subscription
2. API Key (ANTHROPIC_API_KEY) - Uses Anthropic API with pay-per-token billing

OAuth is preferred when available as it uses your Claude Max subscription.
"""

import asyncio
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import anthropic

# Try to import claude-agent-sdk for OAuth support
try:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


def _get_oauth_token_from_credentials() -> Optional[str]:
    """Try to read OAuth token from Claude Code credentials file."""
    try:
        credentials_path = os.path.expanduser("~/.claude/.credentials.json")
        if os.path.exists(credentials_path):
            with open(credentials_path, 'r') as f:
                data = json.load(f)
            token = data.get("claudeAiOauth", {}).get("accessToken")
            if token and token.startswith("sk-ant-oat"):
                return token
    except Exception as e:
        logger.debug(f"Could not read OAuth token: {e}")
    return None


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    api_key: Optional[str]
    oauth_token: Optional[str] = None
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    temperature: float = 0.7
    auth_method: str = "none"


class LLMConfigError(Exception):
    """Raised when LLM is not properly configured."""
    pass


class LLMClient:
    """Client for interacting with Claude LLM. Supports OAuth and API key auth."""

    def __init__(self):
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> LLMConfig:
        """Load LLM configuration from environment."""
        # Check for OAuth token first (uses Max subscription)
        oauth_token = os.environ.get('CLAUDE_CODE_OAUTH_TOKEN')
        if not oauth_token:
            oauth_token = _get_oauth_token_from_credentials()

        api_key = os.environ.get('ANTHROPIC_API_KEY')

        # Determine auth method
        if oauth_token and CLAUDE_SDK_AVAILABLE:
            auth_method = "oauth"
        elif api_key:
            auth_method = "api_key"
        else:
            auth_method = "none"

        return LLMConfig(
            api_key=api_key,
            oauth_token=oauth_token,
            model=os.environ.get('LLM_MODEL', 'claude-sonnet-4-20250514'),
            max_tokens=int(os.environ.get('LLM_MAX_TOKENS', 1024)),
            temperature=float(os.environ.get('LLM_TEMPERATURE', 0.7)),
            auth_method=auth_method
        )

    def _validate_config(self) -> None:
        """Validate that LLM is properly configured."""
        if self.config.auth_method == "none":
            raise LLMConfigError(
                "\n+====================================================================+\n"
                "|              NO CLAUDE AUTHENTICATION FOUND                        |\n"
                "+====================================================================+\n\n"
                "OPTION 1: Use Claude Max Subscription (OAuth) - RECOMMENDED\n"
                "---------------------------------------------------------------------\n"
                "OAuth token auto-detected from ~/.claude/.credentials.json\n"
                "Or set: export CLAUDE_CODE_OAUTH_TOKEN='sk-ant-oat01-...'\n\n"
                "OPTION 2: Use Anthropic API Key (Pay-per-token)\n"
                "---------------------------------------------------------------------\n"
                "Set: export ANTHROPIC_API_KEY='sk-ant-api03-...'\n"
            )
        logger.info(f"LLM auth: {self.config.auth_method} (oauth={bool(self.config.oauth_token)}, api_key={bool(self.config.api_key)})")

    def _run_async(self, coro):
        """Run an async coroutine synchronously."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    return executor.submit(asyncio.run, coro).result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    async def _oauth_chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        enable_tools: bool = False,
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """Chat using OAuth authentication via claude-agent-sdk.

        When enable_tools=True, allows the SDK's built-in Bash tool for CLI commands.
        The SDK handles tool execution internally.
        """
        # Build the prompt from messages
        prompt_parts = []
        for m in messages:
            role = m.get('role', 'user')
            content = m.get('content', '')
            if role == 'user':
                prompt_parts.append(content)
            elif role == 'assistant':
                prompt_parts.append(f"[Previous assistant response: {content}]")

        full_prompt = "\n\n".join(prompt_parts)

        # Configure tools - allow Bash for CLI commands if tools are enabled
        allowed_tools = ['Bash'] if enable_tools else []

        os.environ['CLAUDE_CODE_OAUTH_TOKEN'] = self.config.oauth_token

        client = ClaudeSDKClient(options=ClaudeAgentOptions(
            model=self.config.model,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            max_turns=max_turns if enable_tools else 1
        ))

        response_text = ""
        tool_calls = []
        total_input_tokens = 0
        total_output_tokens = 0

        async with client:
            await client.query(full_prompt)
            async for msg in client.receive_response():
                # Track tool usage from assistant messages
                if hasattr(msg, 'content'):
                    for c in msg.content:
                        if hasattr(c, 'text'):
                            response_text = c.text  # Keep last text response
                        if hasattr(c, 'type') and c.type == 'tool_use':
                            tool_calls.append(getattr(c, 'name', 'unknown'))
                # Extract usage from result message
                if hasattr(msg, 'usage') and msg.usage:
                    usage = msg.usage
                    total_input_tokens = usage.get('input_tokens', 0)
                    total_output_tokens = usage.get('output_tokens', 0)

        result = {
            'content': response_text,
            'model': self.config.model,
            'usage': {
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens
            },
            'stop_reason': 'end_turn',
            'auth_method': 'oauth'
        }
        if tool_calls:
            result['tool_calls'] = tool_calls
        return result

    def get_trading_decision(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Dict[str, Any]:
        """
        Get trading decision from Claude.

        Args:
            system_prompt: System prompt setting context and instructions
            user_prompt: User prompt with market data and question

        Returns:
            Decision dict with 'content', 'model', 'usage' keys

        Raises:
            LLMConfigError: If LLM not configured
            LLMAPIError: If API call fails
        """
        # Use OAuth if available (no tools needed for trading decisions)
        if self.config.auth_method == "oauth":
            logger.info(f"Sending trading decision to {self.config.model} (using oauth)")
            return self._run_async(self._oauth_chat(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                enable_tools=False
            ))

        # Fall back to API key if available
        if not self.config.api_key:
            raise LLMConfigError("No authentication configured")

        try:
            client = anthropic.Anthropic(api_key=self.config.api_key)

            logger.info(f"Sending prompt to {self.config.model} (using api_key)")

            message = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response_text = message.content[0].text

            return {
                'content': response_text,
                'model': message.model,
                'usage': {
                    'input_tokens': message.usage.input_tokens,
                    'output_tokens': message.usage.output_tokens
                },
                'stop_reason': message.stop_reason,
                'auth_method': 'api_key'
            }

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMAPIError(f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise LLMAPIError(f"Failed to get trading decision: {str(e)}")

    def chat(
        self,
        system_prompt: str,
        messages: list,
        tools: list = None,
        tool_executor: callable = None,
        enable_thinking: bool = True,
        thinking_budget: int = 4000
    ) -> Dict[str, Any]:
        """
        Multi-turn chat with Claude, with optional tool support and thinking.

        Args:
            system_prompt: System prompt setting context and instructions
            messages: List of message dicts with 'role' and 'content' keys
            tools: Optional list of tool definitions for Claude
            tool_executor: Optional function to execute tools, called with (tool_name, tool_input)
            enable_thinking: Whether to request extended thinking (default True)
            thinking_budget: Token budget for thinking (default 4000)

        Returns:
            Response dict with 'content', 'model', 'usage', and optionally 'thinking' keys

        Raises:
            LLMConfigError: If LLM not configured
            LLMAPIError: If API call fails
        """
        # Support both tools=True (enable SDK tools) and tools=[...] (custom tool list)
        if tools is True:
            has_tools = True
        elif tools is not None and hasattr(tools, '__len__'):
            has_tools = len(tools) > 0
        else:
            has_tools = False

        # Use OAuth via SDK when available - SDK handles tools via built-in Bash
        if self.config.auth_method == "oauth":
            logger.info(f"Sending {len(messages)} messages to {self.config.model} (using oauth, tools={has_tools})")
            try:
                return self._run_async(self._oauth_chat(
                    system_prompt=system_prompt,
                    messages=messages,
                    enable_tools=has_tools,
                    max_turns=10 if has_tools else 1
                ))
            except Exception as e:
                logger.error(f"OAuth chat error: {e}")
                raise LLMAPIError(f"Chat failed: {str(e)}")

        # Fall back to API key if OAuth not available
        if not self.config.api_key:
            raise LLMConfigError("No authentication configured for chat")

        try:
            # Use API key with the Anthropic client
            client = anthropic.Anthropic(api_key=self.config.api_key)

            logger.info(f"Sending {len(messages)} messages to {self.config.model} (using api_key)")

            # Build request kwargs
            request_kwargs = {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "system": system_prompt,
                "messages": messages
            }

            if tools:
                request_kwargs["tools"] = tools

            # Enable extended thinking if supported and requested
            # NOTE: Extended thinking is NOT compatible with tools - disable if tools present
            has_tools = tools is not None and len(tools) > 0
            if enable_thinking and not has_tools:
                # max_tokens must be > thinking.budget_tokens
                thinking_max_tokens = max(self.config.max_tokens, thinking_budget + 1024)
                request_kwargs["max_tokens"] = thinking_max_tokens
                request_kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                }
                # Extended thinking requires temperature=1
                request_kwargs["temperature"] = 1
                logger.info(f"Extended thinking enabled with budget={thinking_budget}, max_tokens={thinking_max_tokens}")
            else:
                # Use configured temperature for non-thinking calls (including tool use)
                request_kwargs["temperature"] = self.config.temperature
                if enable_thinking and has_tools:
                    logger.info("Extended thinking disabled - incompatible with tools")

            try:
                message = client.messages.create(**request_kwargs)
            except anthropic.BadRequestError as e:
                # If thinking not supported, retry without it
                if "thinking" in str(e).lower() or "temperature" in str(e).lower():
                    logger.warning("Extended thinking not supported, retrying without it")
                    request_kwargs.pop("thinking", None)
                    request_kwargs.pop("temperature", None)
                    message = client.messages.create(**request_kwargs)
                else:
                    raise

            # Helper function to extract content and thinking from response
            def extract_response(msg):
                response_text = ""
                thinking_text = ""
                for block in msg.content:
                    if hasattr(block, 'type'):
                        if block.type == "thinking" and hasattr(block, 'thinking'):
                            thinking_text += block.thinking
                        elif block.type == "text" and hasattr(block, 'text'):
                            response_text += block.text
                    elif hasattr(block, 'text'):
                        response_text += block.text
                return response_text, thinking_text

            # Handle tool use with multi-turn loop for complex operations
            # This allows the LLM to execute multiple tools in sequence (e.g., create bot, then start it)
            MAX_TOOL_ITERATIONS = 10  # Safety limit to prevent infinite loops
            current_messages = messages.copy()
            total_input_tokens = message.usage.input_tokens
            total_output_tokens = message.usage.output_tokens
            all_tool_calls = []
            all_thinking = ""
            iteration = 0

            while message.stop_reason == "tool_use" and tool_executor and iteration < MAX_TOOL_ITERATIONS:
                iteration += 1
                logger.info(f"Tool use iteration {iteration}")

                # Process tool calls from current response
                tool_results = []
                assistant_content = []

                for block in message.content:
                    if hasattr(block, 'type') and block.type == "thinking":
                        thinking = block.thinking if hasattr(block, 'thinking') else ""
                        assistant_content.append({"type": "thinking", "thinking": thinking})
                        if all_thinking:
                            all_thinking += "\n\n---\n\n" + thinking
                        else:
                            all_thinking = thinking
                    elif block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })
                        all_tool_calls.append(block.name)
                        # Execute the tool
                        logger.info(f"Executing tool: {block.name}")
                        try:
                            result = tool_executor(block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result)
                            })
                        except Exception as e:
                            logger.error(f"Tool execution failed: {e}")
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error: {str(e)}",
                                "is_error": True
                            })

                # Add this turn to messages
                current_messages.append({"role": "assistant", "content": assistant_content})
                current_messages.append({"role": "user", "content": tool_results})

                # Continue conversation with tool results
                # NOTE: Don't enable thinking here - tools are present and incompatible
                # Use configured temperature for tool use calls (not temperature=1 which is for thinking)
                next_kwargs = {
                    "model": self.config.model,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "system": system_prompt,
                    "tools": tools,
                    "messages": current_messages
                }

                # Get next response (may request more tools or give final answer)
                message = client.messages.create(**next_kwargs)
                total_input_tokens += message.usage.input_tokens
                total_output_tokens += message.usage.output_tokens

            # Extract final response
            response_text, thinking_text = extract_response(message)
            if thinking_text:
                if all_thinking:
                    all_thinking += "\n\n---\n\n" + thinking_text
                else:
                    all_thinking = thinking_text

            if iteration > 0:
                # We went through tool use loop
                logger.info(f"Completed {iteration} tool iterations, tools used: {all_tool_calls}")
                result = {
                    'content': response_text,
                    'model': message.model,
                    'usage': {
                        'input_tokens': total_input_tokens,
                        'output_tokens': total_output_tokens
                    },
                    'stop_reason': message.stop_reason,
                    'tool_calls': all_tool_calls,
                    'tool_iterations': iteration
                }
                if all_thinking:
                    result['thinking'] = all_thinking
                return result

            # No tool use, extract text and thinking from response
            response_text, thinking_text = extract_response(message)

            logger.info(f"Got response: {response_text[:100]}...")

            result = {
                'content': response_text,
                'model': message.model,
                'usage': {
                    'input_tokens': message.usage.input_tokens,
                    'output_tokens': message.usage.output_tokens
                },
                'stop_reason': message.stop_reason
            }
            if thinking_text:
                result['thinking'] = thinking_text
            return result

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMAPIError(f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise LLMAPIError(f"Chat failed: {str(e)}")

    def is_configured(self) -> bool:
        """Check if LLM is properly configured."""
        try:
            self._validate_config()
            return True
        except LLMConfigError:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get LLM configuration status."""
        return {
            'configured': self.is_configured(),
            'model': self.config.model,
            'api_key_set': bool(self.config.api_key),
            'api_key_preview': f"{self.config.api_key[:20]}..." if self.config.api_key else None,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature
        }


class LLMAPIError(Exception):
    """Raised when LLM API call fails."""
    pass


# Global client instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client instance."""
    global _client
    if _client is None:
        try:
            _client = LLMClient()
        except LLMConfigError as e:
            logger.error(str(e))
            raise
    return _client


def is_llm_configured() -> bool:
    """Check if LLM is configured without raising errors."""
    try:
        client = LLMClient()
        return client.is_configured()
    except LLMConfigError:
        return False


def get_llm_config_error_message() -> str:
    """Get human-readable error message for missing LLM config."""
    try:
        get_llm_client()
        return ""
    except LLMConfigError as e:
        return str(e)
