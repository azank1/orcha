"""Unit tests for BYOK (bring-your-own-key) model credentials in the chat LLM factory."""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from superagent.nodes.orchestrator import _make_chat_llm

_BYOK = {
    "base_url": "https://api.groq.com/openai/v1",
    "api_key": "gsk_test_key",
    "model": "llama-3.3-70b-versatile",
}


def test_make_chat_llm_byok_complete_uses_visitor_endpoint():
    llm = _make_chat_llm(byok=_BYOK)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "llama-3.3-70b-versatile"
    assert str(llm.openai_api_base) == "https://api.groq.com/openai/v1"
    assert llm.openai_api_key.get_secret_value() == "gsk_test_key"


def test_make_chat_llm_byok_takes_precedence_over_model_override():
    llm = _make_chat_llm(model_override="some-other-model", byok=_BYOK)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "llama-3.3-70b-versatile"


def test_make_chat_llm_byok_incomplete_falls_back_to_env():
    llm = _make_chat_llm(byok={"base_url": "https://api.groq.com/openai/v1"})
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name  # env-configured model, BYOK ignored (missing api_key/model)


def test_make_chat_llm_byok_gemini_native_endpoint_routes_to_native_client():
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = _make_chat_llm(
        byok={
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "api_key": "goog_test_key",
            "model": "gemini-3-flash-preview",
        }
    )
    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert "gemini-3-flash-preview" in llm.model


def test_make_chat_llm_byok_gemini_openai_compatible_stays_on_chatopenai():
    llm = _make_chat_llm(
        byok={
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "or_test_key",
            "model": "gemini-3-flash-preview",
        }
    )
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gemini-3-flash-preview"
