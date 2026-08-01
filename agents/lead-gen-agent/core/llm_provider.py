"""
core/llm_provider.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unified LLM provider abstraction.
Supports Anthropic, OpenAI, Grok, and OpenRouter with one interface.

Switch provider via LLM_PROVIDER env var:
    LLM_PROVIDER=anthropic    → Claude Haiku (ANTHROPIC_MODEL, default claude-haiku-4-5)
    LLM_PROVIDER=openai       → GPT-4o
    LLM_PROVIDER=grok         → Grok-3
    LLM_PROVIDER=openrouter   → OPENROUTER_MODEL (default anthropic/claude-sonnet-4)

Each provider returns a normalised response:
    {
        "text":       str,           # final text (empty if tool calls pending)
        "tool_calls": [...],         # list of {id, name, input} dicts
        "done":       bool,          # True = no more tool calls, return text
    }

Usage in agent loop:
    provider = get_provider()
    response = await provider.chat(messages, tools, system)
    if response["done"]:
        return parse(response["text"])
    for tc in response["tool_calls"]:
        result = execute(tc["name"], tc["input"])
        messages = provider.append_tool_result(messages, tc["id"], result)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import logging
import os
from abc import ABC, abstractmethod

from core.context import get_key

logger = logging.getLogger(__name__)


# ── Base class ────────────────────────────────────────────────────────────────

class LLMProvider(ABC):
    """Abstract base — all providers implement chat() and append_tool_result()."""

    @abstractmethod
    async def chat(self, messages: list, tools: list, system: str) -> dict:
        """
        Send messages to the LLM.
        Returns normalised dict: {text, tool_calls, done}
        """

    @abstractmethod
    def append_tool_result(self, messages: list, tool_call_id: str, result: any) -> list:
        """
        Append a tool result to the message history in provider-specific format.
        Returns updated messages list.
        """

    @abstractmethod
    def format_tools(self, tool_schemas: list) -> list:
        """Convert unified tool schemas to provider-specific format."""


# ── Anthropic ─────────────────────────────────────────────────────────────────

class AnthropicProvider(LLMProvider):
    """
    Uses: claude-haiku-4-5 by default (ANTHROPIC_MODEL to override).
    Key env var: ANTHROPIC_API_KEY
    """

    def __init__(self):
        self.MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    def _client(self):
        import anthropic
        import certifi
        import httpx
        http_client = httpx.AsyncClient(verify=certifi.where(), timeout=httpx.Timeout(120.0))
        return anthropic.AsyncAnthropic(
            api_key=get_key("ANTHROPIC_API_KEY"),
            http_client=http_client,
        )

    async def chat(self, messages: list, tools: list, system: str) -> dict:
        client = self._client()
        response = await client.messages.create(
            model=self.MODEL,
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages,
        )
        logger.debug(f"Anthropic stop_reason={response.stop_reason}")

        tool_calls = []
        text = ""

        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append({
                    "id":    block.id,
                    "name":  block.name,
                    "input": block.input,
                    "_raw":  block,      # kept for append_tool_result
                })
            elif hasattr(block, "text"):
                text += block.text

        done = response.stop_reason == "end_turn" or not tool_calls
        return {
            "text":       text,
            "tool_calls": tool_calls,
            "done":       done,
            "_raw_content": response.content,  # needed to append to history
        }

    def append_tool_result(self, messages: list, tool_call_id: str, result: any) -> list:
        """
        Anthropic expects tool results as a user message with type=tool_result.
        We accumulate them and add in one batch — call flush_tool_results instead.
        """
        return messages  # batching handled in agent loop

    def make_tool_result_block(self, tool_call_id: str, content: str, is_error: bool = False) -> dict:
        block = {
            "type":        "tool_result",
            "tool_use_id": tool_call_id,
            "content":     content,
        }
        if is_error:
            block["is_error"] = True
        return block

    def format_tools(self, tool_schemas: list) -> list:
        return tool_schemas  # Anthropic format is the canonical format


# ── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAIProvider(LLMProvider):
    """
    Uses: gpt-4o
    Key env var: OPENAI_API_KEY
    Grok reuses this class with a different base_url and model.
    """

    MODEL    = "gpt-4o"
    BASE_URL = None   # default OpenAI

    def _client(self):
        import certifi
        import httpx
        from openai import AsyncOpenAI
        kwargs = {
            "api_key": get_key("OPENAI_API_KEY"),
            "http_client": httpx.AsyncClient(verify=certifi.where(), timeout=httpx.Timeout(240.0)),
        }
        if self.BASE_URL:
            kwargs["base_url"] = self.BASE_URL
        return AsyncOpenAI(**kwargs)

    async def chat(self, messages: list, tools: list, system: str) -> dict:
        client = self._client()

        # OpenAI puts system prompt as first message
        full_messages = [{"role": "system", "content": system}] + messages

        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        response = await client.chat.completions.create(
            model=self.MODEL,
            messages=full_messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=max_tokens,
            temperature=0,
        )

        msg = response.choices[0].message
        finish = response.choices[0].finish_reason
        logger.debug(f"OpenAI finish_reason={finish}")

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id":    tc.id,
                    "name":  tc.function.name,
                    "input": json.loads(tc.function.arguments),
                    "_raw":  tc,
                })

        text = msg.content or ""
        # If the model emitted tool calls, we must process them — never done.
        # Some OpenRouter models send finish_reason="stop" even when tool_calls
        # are present; trust the presence of tool_calls over finish_reason.
        if tool_calls:
            done = False
        elif finish in ("stop", "length"):
            # No tool calls — check whether we got valid final JSON or reasoning prose
            stripped = text.strip()
            if tools and not stripped:
                # OpenRouter models sometimes emit an empty assistant message with finish_reason=stop
                logger.info(
                    "OpenAI-compatible: blank completion while tools registered — continuing loop "
                    "(avoid premature pipeline stop before score/write)"
                )
                done = False
            elif tools and stripped and not stripped.startswith("{"):
                logger.info("OpenAI: reasoning text detected (not final JSON) — continuing loop")
                done = False
            else:
                done = True
        else:
            done = False  # finish_reason="tool_calls" or similar — keep going

        return {
            "text":         text,
            "tool_calls":   tool_calls,
            "done":         done,
            "_raw_message": msg,
        }

    def append_tool_result(self, messages: list, tool_call_id: str, result: any) -> list:
        messages.append({
            "role":         "tool",
            "tool_call_id": tool_call_id,
            "content":      json.dumps(result) if not isinstance(result, str) else result,
        })
        return messages

    def format_tools(self, tool_schemas: list) -> list:
        """Convert Anthropic-format schemas to OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name":        t["name"],
                    "description": t["description"],
                    "parameters":  t["input_schema"],
                },
            }
            for t in tool_schemas
        ]


# ── Grok ──────────────────────────────────────────────────────────────────────

class GrokProvider(OpenAIProvider):
    """
    Uses: grok-3 (xAI)
    Key env var: GROK_API_KEY
    Identical to OpenAI — just different base_url, model, and key name.
    """

    MODEL    = "grok-3"
    BASE_URL = "https://api.x.ai/v1"

    def _client(self):
        import certifi
        import httpx
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=get_key("GROK_API_KEY"),
            base_url=self.BASE_URL,
            http_client=httpx.AsyncClient(verify=certifi.where(), timeout=httpx.Timeout(120.0)),
        )


# ── OpenRouter ─────────────────────────────────────────────────────────────────

class OpenRouterProvider(OpenAIProvider):
    """
    Uses OpenRouter (openrouter.ai) — model is configurable via OPENROUTER_MODEL.
    Default: anthropic/claude-sonnet-4 (Claude Sonnet on OpenRouter).
    Override OPENROUTER_MODEL for other routers (e.g. z-ai/glm-4.6, meta-llama/…).
    Key env var: OPENROUTER_API_KEY
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self):
        self.MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")

    def _client(self):
        import certifi
        import httpx
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key=get_key("OPENROUTER_API_KEY"),
            base_url=self.BASE_URL,
            http_client=httpx.AsyncClient(verify=certifi.where(), timeout=httpx.Timeout(240.0)),
        )


# ── Factory ───────────────────────────────────────────────────────────────────

def get_provider() -> LLMProvider:
    """
    Returns the right provider based on LLM_PROVIDER.
    Checks per-request context first, then env var. Defaults to anthropic (direct API).

    Set in your .env or pass llm_provider in the credentials payload:
        LLM_PROVIDER=anthropic
        LLM_PROVIDER=openai
        LLM_PROVIDER=grok
        LLM_PROVIDER=openrouter   ← uses OPENROUTER_MODEL (default: anthropic/claude-sonnet-4)
    """
    provider = (get_key("LLM_PROVIDER") or os.getenv("LLM_PROVIDER", "anthropic")).lower().strip()

    if provider == "openai":
        logger.info("LLM provider: OpenAI (gpt-4o)")
        return OpenAIProvider()
    elif provider == "grok":
        logger.info("LLM provider: Grok (grok-3)")
        return GrokProvider()
    elif provider == "openrouter":
        model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
        logger.info("LLM provider: OpenRouter (%s)", model)
        return OpenRouterProvider()
    else:
        if provider != "anthropic":
            logger.warning(f"Unknown LLM_PROVIDER='{provider}' — defaulting to Anthropic")
        ap = AnthropicProvider()
        logger.info("LLM provider: Anthropic direct API (%s)", ap.MODEL)
        return ap


def get_api_key_name() -> str:
    """Returns the env var name for the current provider's API key."""
    provider = (get_key("LLM_PROVIDER") or os.getenv("LLM_PROVIDER", "anthropic")).lower()
    return {
        "openai":      "OPENAI_API_KEY",
        "grok":        "GROK_API_KEY",
        "anthropic":   "ANTHROPIC_API_KEY",
        "openrouter":  "OPENROUTER_API_KEY",
    }.get(provider, "ANTHROPIC_API_KEY")
