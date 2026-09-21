"""Live checks against real TMDB / Gemini. Skipped automatically without keys.

Run with:  python -m pytest -m live -v
"""

import os

import pytest

pytestmark = pytest.mark.live

# Captured at import time, before conftest swaps in a fake TMDB key for unit tests.
REAL_TMDB_KEY = os.environ.get("TMDB_API_KEY")
HAVE_GEMINI = bool(os.environ.get("GEMINI_API_KEY") and os.environ.get("GEMINI_MODEL"))

needs_tmdb = pytest.mark.skipif(not REAL_TMDB_KEY, reason="TMDB_API_KEY not set")
needs_gemini = pytest.mark.skipif(not HAVE_GEMINI, reason="GEMINI_API_KEY / GEMINI_MODEL not set")


@needs_tmdb
def test_live_tmdb_known_movie(monkeypatch):
    from cinemate.tools import search_movies
    monkeypatch.setenv("TMDB_API_KEY", REAL_TMDB_KEY)
    assert "Inception" in search_movies.invoke({"query": "Inception"})


@needs_tmdb
def test_live_tmdb_nonexistent_movie(monkeypatch):
    from cinemate.tools import search_movies
    monkeypatch.setenv("TMDB_API_KEY", REAL_TMDB_KEY)
    assert "No movies found" in search_movies.invoke({"query": "qzxwvbnm asdfghjkl 987654"})


@needs_gemini
def test_live_gemini_responds():
    from cinemate.agent import get_llm
    reply = get_llm().invoke("Respond with exactly: CineMate Gemini test successful.")
    assert "CineMate Gemini test successful" in reply.text


@needs_gemini
def test_live_gemini_supports_tool_calling():
    """The agent needs the model to request tool calls. The tool is bound but NOT executed."""
    from cinemate.agent import get_llm
    from cinemate.tools import search_movies
    reply = get_llm().bind_tools([search_movies]).invoke(
        "Use the movie search tool to look up the movie Inception."
    )
    assert reply.tool_calls, f"model did not request a tool call; got: {reply.text!r}"
    assert reply.tool_calls[0]["name"] == "search_movies"
    assert "inception" in reply.tool_calls[0]["args"]["query"].lower()
