"""Small client for the TMDB v3 API (movie search + genre names).

Never raises for normal problems (bad key, no results, timeout...). Instead it
returns a SearchResult whose `status` says what happened.
"""

from functools import lru_cache
from typing import Optional

import requests

from cinemate.config import get_tmdb_api_key
from cinemate.schemas import Movie, SearchResult

BASE_URL = "https://api.themoviedb.org/3"
# (connect, read) seconds. Connect is short so an unreachable host fails fast; note that
# requests tries each resolved address (IPv6 + IPv4) separately, so worst case is ~2x connect.
TIMEOUT_SECONDS = (4, 10)
UNREACHABLE_MESSAGE = "Unable to reach the movie database right now. Please try again."
MAX_RESULTS = 5


class TMDBError(Exception):
    """Internal error carrying a status; converted to a SearchResult by callers."""

    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _auth(api_key: str) -> tuple[dict, dict]:
    """TMDB accepts either a v3 API key (query param) or a v4 read-access
    token (Bearer header, a JWT starting with 'eyJ'). Support both."""
    if api_key.startswith("eyJ"):
        return {"Authorization": f"Bearer {api_key}", "accept": "application/json"}, {}
    return {"accept": "application/json"}, {"api_key": api_key}


def _get(path: str, params: dict) -> dict:
    """GET a TMDB endpoint and return parsed JSON, or raise TMDBError."""
    headers, auth_params = _auth(get_tmdb_api_key())
    try:
        resp = requests.get(
            f"{BASE_URL}{path}",
            params={**params, **auth_params},
            headers=headers,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.SSLError:
        raise TMDBError("network_error", "A secure connection to TMDB could not be established (SSL problem).")
    except requests.exceptions.ConnectTimeout:
        raise TMDBError("network_error", UNREACHABLE_MESSAGE)
    except requests.exceptions.ReadTimeout:
        raise TMDBError("network_error", "TMDB took too long to respond. Please try again.")
    except requests.RequestException:
        raise TMDBError("network_error", UNREACHABLE_MESSAGE)

    if resp.status_code == 401:
        raise TMDBError("auth_error", "TMDB rejected the API key. Check TMDB_API_KEY.")
    if resp.status_code in (400, 404, 422):
        raise TMDBError("invalid_request", f"TMDB rejected the request (HTTP {resp.status_code}).")
    if resp.status_code != 200:
        raise TMDBError("api_error", f"TMDB returned an error (HTTP {resp.status_code}).")

    try:
        data = resp.json()
    except ValueError:
        raise TMDBError("unexpected_response", "TMDB returned a response that is not valid JSON.")
    if not isinstance(data, dict):
        raise TMDBError("unexpected_response", "TMDB returned an unexpected response format.")
    return data


@lru_cache(maxsize=1)
def _fetch_genre_map() -> dict:
    data = _get("/genre/movie/list", {"language": "en"})
    return {g["id"]: g["name"] for g in data["genres"]}


def get_genre_map() -> dict:
    """Map genre id -> name. Returns {} if unavailable (names are optional)."""
    try:
        return _fetch_genre_map()
    except (TMDBError, KeyError, TypeError):
        return {}


def _normalize(raw: dict, genre_map: dict) -> Movie:
    release = raw.get("release_date") or ""
    year = int(release[:4]) if release[:4].isdigit() else None
    genre_ids = raw.get("genre_ids") or []
    return Movie(
        tmdb_id=raw.get("id"),
        title=raw["title"],  # KeyError => treated as unexpected response
        year=year,
        rating=round(raw["vote_average"], 1) if raw.get("vote_average") else None,
        overview=raw.get("overview") or "",
        genre_ids=genre_ids,
        genres=[genre_map[i] for i in genre_ids if i in genre_map],
    )


def search_movies(query: str, year: Optional[int] = None) -> SearchResult:
    """Search TMDB for movies matching a title/keywords string."""
    if not query or not query.strip():
        return SearchResult(
            success=False, status="invalid_request",
            message="Search query is empty.",
        )

    params = {"query": query.strip(), "include_adult": "false", "language": "en-US", "page": 1}
    if year:
        params["year"] = year

    try:
        data = _get("/search/movie", params)
        results = data["results"]
        if not isinstance(results, list):
            raise TypeError
        if not results:
            return SearchResult(
                success=False, status="no_results",
                message="No movies found for the given query.",
            )
        genre_map = get_genre_map()
        movies = [_normalize(r, genre_map) for r in results[:MAX_RESULTS]]
    except TMDBError as e:
        return SearchResult(success=False, status=e.status, message=e.message)
    except (KeyError, TypeError, ValueError, AttributeError):
        return SearchResult(
            success=False, status="unexpected_response",
            message="TMDB returned data in an unexpected format.",
        )

    return SearchResult(success=True, status="ok", message=f"Found {len(movies)} movies.", movies=movies)
