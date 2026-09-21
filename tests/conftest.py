import pytest

from cinemate import tmdb_client


@pytest.fixture(autouse=True)
def fake_tmdb_key(monkeypatch):
    """Unit tests never use a real key or the network."""
    monkeypatch.setenv("TMDB_API_KEY", "fake-test-key")
    tmdb_client._fetch_genre_map.cache_clear()
    yield
    tmdb_client._fetch_genre_map.cache_clear()


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, bad_json=False):
        self.status_code = status_code
        self._json = json_data
        self._bad_json = bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("not json")
        return self._json


GENRES = {"genres": [{"id": 878, "name": "Science Fiction"}, {"id": 28, "name": "Action"}]}

INCEPTION = {
    "id": 27205,
    "title": "Inception",
    "release_date": "2010-07-15",
    "vote_average": 8.369,
    "overview": "A thief who steals secrets through dream-sharing technology.",
    "genre_ids": [28, 878],
}


def route(search_response):
    """Build a fake requests.get that serves genres and a given search response."""
    def fake_get(url, **kwargs):
        if url.endswith("/genre/movie/list"):
            return FakeResponse(200, GENRES)
        return search_response
    return fake_get
