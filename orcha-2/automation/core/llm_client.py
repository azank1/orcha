import os
import json
import time
import asyncio
from typing import Optional, Dict, Any
import httpx


# Configuration via environment variables
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 15))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", 3))

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "logs")
LOG_FILE = os.path.normpath(os.path.join(LOGS_DIR, "llm_usage.jsonl"))
os.makedirs(LOGS_DIR, exist_ok=True)


def _log_usage(record: Dict[str, Any]) -> None:
    try:
        record.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        # Logging must never break runtime
        pass


class LLMClient:
    """Hybrid LLM client: Ollama → OpenAI → Heuristic fallback.

    Use classify_intent(text) to obtain {type: search|order|unknown, source: ..., raw: ...}
    parse_intent(text) is kept as an alias for backward compatibility.
    """

    def __init__(self):
        self.ollama_available = USE_OLLAMA
        self.openai_available = USE_OPENAI and bool(OPENAI_API_KEY)

    async def generate(self, prompt: str) -> Dict[str, Any]:
        start = time.time()
        last_error = None
        for attempt in range(1, LLM_MAX_RETRIES + 1):
            # Try Ollama first
            if self.ollama_available:
                try:
                    text = await self._try_ollama(prompt)
                    if text:
                        latency = int((time.time() - start) * 1000)
                        _log_usage({"model": f"ollama:{OLLAMA_MODEL}", "latency_ms": latency, "status": "ok"})
                        return {"source": "ollama", "text": text}
                except Exception as e:
                    last_error = e
                    self.ollama_available = False

            # Then try OpenAI
            if self.openai_available:
                try:
                    text = await self._try_openai(prompt)
                    if text:
                        latency = int((time.time() - start) * 1000)
                        _log_usage({"model": f"openai:{OPENAI_MODEL}", "latency_ms": latency, "status": "ok"})
                        return {"source": "openai", "text": text}
                except Exception as e:
                    last_error = e

            # Backoff then retry if possible
            if attempt < LLM_MAX_RETRIES:
                await asyncio.sleep(min(2 ** attempt, 10))

        # Fallback
        latency = int((time.time() - start) * 1000)
        _log_usage({"model": "fallback", "latency_ms": latency, "status": "fallback", "error": str(last_error) if last_error else None})
        return {"source": "fallback", "text": self._heuristic_text(prompt)}

    async def classify_intent(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Classify the user intent as one of: search, order, unknown.\n"
            "Respond with only the single word label.\n"
            f"User: {text}\n"
            "Intent:"
        )
        result = await self.generate(prompt)
        source = result.get("source", "fallback")
        # If we fell back, analyze the original user text (not the composed prompt)
        if source == "fallback":
            label = self._heuristic_intent(text)
        else:
            label = result.get("text", "").strip().lower()
        intent_type = "unknown"
        if "search" in label:
            intent_type = "search"
        elif "order" in label:
            intent_type = "order"

        # Return structured result with source and raw label
        out = {"type": intent_type, "source": source, "raw": label}
        if intent_type == "search":
            out["query"] = text
        return out

    # Backward-compat alias used by orchestrator
    async def parse_intent(self, text: str) -> Dict[str, Any]:
        return await self.classify_intent(text)

    async def _try_ollama(self, prompt: str) -> Optional[str]:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                data = resp.json()
                # Ollama responses may use "response" or "text"
                return data.get("response") or data.get("text")
            # Non-200 makes Ollama unavailable for this session
            self.ollama_available = False
            return None

    async def _try_openai(self, prompt: str) -> Optional[str]:
        if not OPENAI_API_KEY:
            return None
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 16,
            "temperature": 0.0,
        }
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            # Simple retry loop for OpenAI 429/5xx
            backoff = 0.5
            for attempt in range(LLM_MAX_RETRIES):
                resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < LLM_MAX_RETRIES - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                if resp.status_code != 200:
                    # Consider OpenAI unavailable for this run but don't disable permanently
                    return None
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        return None

    def _heuristic_text(self, prompt: str) -> str:
        # Very simple local fallback response that encodes a label
        tl = prompt.lower()
        if any(w in tl for w in ["order", "buy", "checkout", "submit"]):
            return "order"
        if any(w in tl for w in ["search", "find", "show", "pizza", "burger", "salad", "menu", "available"]):
            return "search"
        return "unknown"

    def _heuristic_intent(self, user_text: str) -> str:
        tl = user_text.lower()
        if any(w in tl for w in ["order", "buy", "checkout", "submit", "place an order"]):
            return "order"
        if any(w in tl for w in ["search", "find", "show", "look for", "menu", "available", "pizza", "burger", "salad"]):
            return "search"
        return "unknown"
