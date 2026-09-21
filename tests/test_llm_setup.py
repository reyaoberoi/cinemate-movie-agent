"""Offline checks for the Gemini configuration and prompt compatibility (no API calls)."""

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from cinemate.agent import get_llm
from cinemate.config import ConfigError, get_gemini_api_key, get_model_name
from cinemate.prompts import CINEMATE_PROMPT
from cinemate.tools import search_movies


def test_missing_gemini_key_message(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="GEMINI_API_KEY is not configured"):
        get_gemini_api_key()


def test_missing_model_message(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    with pytest.raises(ConfigError, match="GEMINI_MODEL is not configured"):
        get_model_name()


def test_get_llm_builds_gemini_model_without_network(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "some-gemini-model")
    llm = get_llm()
    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert llm.model.endswith("some-gemini-model")


def test_prompt_renders_with_and_without_history():
    msgs = CINEMATE_PROMPT.invoke({"input": "Recommend sci-fi movies"}).to_messages()
    assert msgs[0].type == "system" and "CineMate" in msgs[0].content
    assert msgs[-1].content == "Recommend sci-fi movies"

    history = [HumanMessage("Recommend sci-fi movies"), AIMessage("Sure!")]
    msgs = CINEMATE_PROMPT.invoke({"input": "Only after 2020", "chat_history": history}).to_messages()
    assert [m.type for m in msgs] == ["system", "human", "ai", "human"]


def test_prompt_pipes_into_a_chat_model():
    fake = GenericFakeChatModel(messages=iter([AIMessage("hello")]))
    assert (CINEMATE_PROMPT | fake).invoke({"input": "hi"}).content == "hello"


def test_tool_can_be_bound_to_gemini_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "some-gemini-model")
    assert get_llm().bind_tools([search_movies]) is not None
