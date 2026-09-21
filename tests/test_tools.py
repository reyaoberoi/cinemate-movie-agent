import pytest

from cinemate import tmdb_client, tools
from cinemate.config import ConfigError, get_tmdb_api_key
from conftest import INCEPTION, FakeResponse, route


def test_tool_metadata():
    assert tools.search_movies.name == "search_movies"
    assert "TMDB" in tools.search_movies.description


def test_tool_returns_readable_text(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, {"results": [INCEPTION]})))
    out = tools.search_movies.invoke({"query": "Inception"})
    assert "Inception (2010)" in out
    assert "8.4/10" in out
    assert "Science Fiction" in out
    assert not out.lstrip().startswith("{")  # not a raw JSON dump


def test_tool_no_results_is_safe(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, {"results": []})))
    out = tools.search_movies.invoke({"query": "zzzzqqqq"})
    assert "No movies found" in out


def test_missing_key_error_is_clear_and_leaks_nothing(monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY")
    with pytest.raises(ConfigError, match="TMDB_API_KEY is not configured"):
        get_tmdb_api_key()
