"""Configuration: load API keys and model name from the environment / .env file.

Secrets are only ever read here and are never printed or put in error messages.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if present; real env vars still win


class ConfigError(Exception):
    """Raised when a required setting is missing."""


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(
            f"{name} is not configured. "
            "Add it to your environment before running the application."
        )
    return value


def get_tmdb_api_key() -> str:
    return _require("TMDB_API_KEY")


def get_gemini_api_key() -> str:
    return _require("GEMINI_API_KEY")


def get_model_name() -> str:
    return _require("GEMINI_MODEL")
