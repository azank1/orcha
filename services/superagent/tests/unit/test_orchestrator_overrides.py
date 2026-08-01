"""Unit tests for per-session model override and custom instructions."""

from __future__ import annotations

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from superagent.nodes.orchestrator import _build_lc_messages, _make_chat_llm


def test_make_chat_llm_default_uses_env_model():
    llm = _make_chat_llm()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name  # env-configured model, no override


def test_make_chat_llm_override_routes_to_openai_client():
    llm = _make_chat_llm(model_override="llama-3.1-8b-instant")
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "llama-3.1-8b-instant"


def test_make_chat_llm_gemini_override_routes_to_native_client():
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = _make_chat_llm(model_override="gemini-3-flash-preview")
    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert "gemini-3-flash-preview" in llm.model


def test_build_lc_messages_no_custom_instructions():
    msgs = _build_lc_messages({"messages": []})
    assert isinstance(msgs[0], SystemMessage)
    assert "Operator custom instructions" not in msgs[0].content


def test_build_lc_messages_appends_custom_instructions():
    msgs = _build_lc_messages(
        {"messages": [], "custom_instructions": "Always answer in bullet points."}
    )
    assert "## Operator custom instructions" in msgs[0].content
    assert "Always answer in bullet points." in msgs[0].content


def test_build_lc_messages_caps_custom_instructions_at_2000_chars():
    msgs = _build_lc_messages({"messages": [], "custom_instructions": "x" * 5000})
    section = msgs[0].content.split("## Operator custom instructions\n", 1)[1]
    assert len(section) == 2000
