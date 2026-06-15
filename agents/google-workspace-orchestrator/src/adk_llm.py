"""Run a single-turn LlmAgent via LiteLLM (OpenRouter)."""

from __future__ import annotations

import logging
import os
import uuid

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .config import Settings

logger = logging.getLogger(__name__)

_APP = "metaorcha_workspace_orch"


async def complete_llm(settings: Settings, instruction: str, user_text: str) -> str:
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    os.environ.setdefault("OPENROUTER_API_KEY", settings.openrouter_api_key)

    model_name = settings.openrouter_model.strip()
    if not model_name.startswith("openrouter/"):
        # Ensure LiteLLM routes through OpenRouter when OPENROUTER_* credentials are used.
        model_name = f"openrouter/{model_name}"

    model = LiteLlm(
        model=model_name,
        api_key=settings.openrouter_api_key,
        api_base=str(settings.openrouter_api_base),
    )
    agent = LlmAgent(
        model=model,
        name="workspace_llm",
        instruction=instruction,
    )
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=_APP,
        session_service=session_service,
        auto_create_session=True,
    )
    session_id = str(uuid.uuid4())
    msg = types.Content(role="user", parts=[types.Part(text=user_text)])
    final_text = ""
    async for event in runner.run_async(
        user_id="metaorcha",
        session_id=session_id,
        new_message=msg,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text = part.text
    if not final_text.strip():
        logger.warning("adk_llm: empty final response")
    return final_text.strip()
