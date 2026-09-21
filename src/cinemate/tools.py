"""LangChain tool wrapping the TMDB client, so an agent can call it."""

from typing import Optional

from langchain_core.tools import tool

from cinemate.tmdb_client import search_movies as tmdb_search_movies


def format_movies(result) -> str:
    """Turn a SearchResult into compact, LLM-readable text (not raw JSON)."""
    if not result.success:
        return f"No data retrieved ({result.status}): {result.message}"
    lines = []
    for i, m in enumerate(result.movies, 1):
        lines.append(
            f"{i}. {m.title} ({m.year or 'year unknown'}) | "
            f"rating: {m.rating if m.rating is not None else 'n/a'}/10 | "
            f"genres: {', '.join(m.genres) or 'n/a'}\n"
            f"   Overview: {m.overview or 'n/a'}"
        )
    return "\n".join(lines)


@tool
def search_movies(query: str, year: Optional[int] = None) -> str:
    """Search the TMDB movie database for real movie data (title, release year,
    rating, genres, overview). Use it whenever factual movie information is
    needed, e.g. a title, keywords or theme like "space survival". Do not use
    it for unrelated, non-movie questions. Optional `year` filters by release year."""
    return format_movies(tmdb_search_movies(query, year))
