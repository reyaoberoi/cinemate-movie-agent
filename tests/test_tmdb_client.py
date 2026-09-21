import pytest
import requests

from cinemate import tmdb_client
from conftest import INCEPTION, FakeResponse, route


def test_successful_search(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, {"results": [INCEPTION]})))
    result = tmdb_client.search_movies("Inception")
    assert result.success and result.status == "ok"
    movie = result.movies[0]
    assert movie.title == "Inception"
    assert movie.year == 2010
    assert movie.rating == 8.4
    assert movie.genre_ids == [28, 878]
    assert movie.genres == ["Action", "Science Fiction"]


def test_no_results(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, {"results": []})))
    result = tmdb_client.search_movies("zzzzqqqq")
    assert not result.success
    assert result.status == "no_results"
    assert result.message == "No movies found for the given query."
    assert result.movies == []


def test_network_failure(monkeypatch):
    def boom(url, **kwargs):
        raise requests.ConnectionError("down")
    monkeypatch.setattr(tmdb_client.requests, "get", boom)
    assert tmdb_client.search_movies("Inception").status == "network_error"


def test_timeout(monkeypatch):
    def slow(url, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(tmdb_client.requests, "get", slow)
    assert tmdb_client.search_movies("Inception").status == "network_error"


@pytest.mark.parametrize("exc, expected", [
    (requests.exceptions.ConnectTimeout(), "Unable to reach the movie database"),
    (requests.exceptions.ReadTimeout(), "took too long"),
    (requests.exceptions.SSLError("bad cert"), "SSL"),
    (requests.exceptions.ProxyError("proxy"), "Unable to reach the movie database"),
])
def test_network_failure_kinds_give_clean_messages(monkeypatch, exc, expected):
    def boom(url, **kwargs):
        raise exc
    monkeypatch.setattr(tmdb_client.requests, "get", boom)
    result = tmdb_client.search_movies("Inception")
    assert result.status == "network_error" and expected in result.message and result.movies == []


def test_request_uses_separate_connect_and_read_timeouts(monkeypatch):
    seen = {}
    def fake_get(url, **kwargs):
        seen.update(kwargs)
        return FakeResponse(200, {"results": []})
    monkeypatch.setattr(tmdb_client.requests, "get", fake_get)
    tmdb_client.search_movies("x")
    connect, read = seen["timeout"]
    assert connect <= 5 and read <= 15


def test_api_http_failure(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(500)))
    assert tmdb_client.search_movies("Inception").status == "api_error"


def test_bad_api_key(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(401)))
    assert tmdb_client.search_movies("Inception").status == "auth_error"


def test_malformed_response_missing_results(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, {"oops": 1})))
    assert tmdb_client.search_movies("Inception").status == "unexpected_response"


def test_malformed_response_not_json(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, bad_json=True)))
    assert tmdb_client.search_movies("Inception").status == "unexpected_response"


def test_malformed_movie_missing_title(monkeypatch):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, {"results": [{"id": 1}]})))
    assert tmdb_client.search_movies("x").status == "unexpected_response"


def test_empty_query_makes_no_request(monkeypatch):
    def fail(url, **kwargs):
        raise AssertionError("should not call TMDB")
    monkeypatch.setattr(tmdb_client.requests, "get", fail)
    assert tmdb_client.search_movies("   ").status == "invalid_request"


def test_missing_genres_still_returns_movies(monkeypatch):
    def fake_get(url, **kwargs):
        if url.endswith("/genre/movie/list"):
            return FakeResponse(500)
        return FakeResponse(200, {"results": [INCEPTION]})
    monkeypatch.setattr(tmdb_client.requests, "get", fake_get)
    result = tmdb_client.search_movies("Inception")
    assert result.success and result.movies[0].genres == []


def test_bearer_token_auth(monkeypatch):
    seen = {}
    def fake_get(url, **kwargs):
        seen.update(kwargs)
        return FakeResponse(200, {"results": []})
    monkeypatch.setenv("TMDB_API_KEY", "eyJfaketoken")
    monkeypatch.setattr(tmdb_client.requests, "get", fake_get)
    tmdb_client.search_movies("x")
    assert seen["headers"]["Authorization"] == "Bearer eyJfaketoken"
    assert "api_key" not in seen["params"]
