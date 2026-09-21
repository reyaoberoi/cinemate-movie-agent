"""Data structures shared across the app.

The TMDB client normalises raw API JSON into these models so the rest of the
application never handles raw TMDB responses.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Status = Literal[
    "ok",
    "no_results",
    "invalid_request",
    "auth_error",
    "api_error",
    "network_error",
    "unexpected_response",
]


class Movie(BaseModel):
    tmdb_id: Optional[int] = None
    title: str
    year: Optional[int] = None
    rating: Optional[float] = None  # TMDB vote_average (0-10)
    overview: str = ""
    genre_ids: list[int] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)  # names, when the genre list was available


class SearchResult(BaseModel):
    success: bool
    status: Status
    message: str
    movies: list[Movie] = Field(default_factory=list)
