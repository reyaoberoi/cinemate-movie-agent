# CineMate – Agentic Movie Recommendation Assistant

## Project Overview

Choosing a movie is hard: catalogues are huge, and a plain chatbot can only guess from its
training data, so it may invent ratings, release dates or even movies that do not exist.

CineMate is an agentic LLM application built with LangChain. The user describes what they
want in natural language ("some science-fiction movies"). An LLM agent decides when it needs
facts, calls a TMDB tool to retrieve real movie data, and then explains personalised
recommendations grounded in that data. Follow-ups such as "only after 2020" or
"under 2 hours" will refine the results through conversational memory

## Phase 2 Objective

Get the core end-to-end pipeline working with LangChain and TMDB:
natural-language request → LangChain agent → TMDB tool → TMDB API → real movie data → LLM → recommendation.
Memory, structured output, error-handling polish, evaluation and UI are added incrementally afterwards.

## Planned Architecture

```
User
 ↓
PromptTemplate
 ↓
LLM Agent
 ↓
TMDB Tool
 ↓
TMDB API
 ↓
Movie Data
 ↓
LLM
 ↓
Recommendation
```

Conversational memory and structured output (OutputParser) will be added in subsequent steps.

## Technology Stack

- Python 3.13
- LangChain (`langchain`, `langchain-core`, `langchain-google-genai`)
- LLM: Google Gemini (via the Gemini API)
- TMDB API (v3)

## Current Status

| Component | Status |
|---|---|
| Project structure | completed |
| Configuration (`config.py`) | completed |
| TMDB client | completed – unit-tested with mocks; **not yet verified against the live API** |
| LangChain tool | completed – unit-tested with mocks; **not yet verified against the live API** |
| Prompt template | basic version completed |
| LLM configuration (Gemini) | written and unit-tested offline; **not yet run against the live Gemini API** |
| Agent (`create_agent`, Gemini + `search_movies`) | implemented; loop verified offline with a scripted model; **live run pending (Kaggle notebook)** |
| Memory | not yet implemented |
| Structured output | not yet implemented |
| UI | not yet implemented |

## LLM Provider

CineMate uses Google Gemini through the official LangChain integration
(`langchain-google-genai`, class `ChatGoogleGenerativeAI`). The model is chosen with the
`GEMINI_MODEL` environment variable, so it can be changed without touching code. The model must
support tool/function calling, because the agent uses it to call the TMDB tool.

For development and testing we use the Gemini API free tier, where available. Free-tier models,
rate limits and quotas are set by Google and may change, so heavy use can be rate-limited.
API keys are read from environment variables / `.env` and are never committed.

## Kaggle Notebook

`notebooks/CineMate_Phase2.ipynb` is the live execution environment for Phase 2. Our development
machine's network cannot resolve the TMDB API correctly (a local DNS problem), and Kaggle provides an
environment that can reach the external APIs. The notebook clones this repository and runs the real
code in `src/cinemate`; it does not contain a copy of the application. Kaggle is **not** required for
the final application, which runs anywhere with a working network.

To run it: open the notebook in Kaggle, turn **Internet: On**, add the Kaggle Secrets `TMDB_API_KEY`,
`GEMINI_API_KEY` and `GEMINI_MODEL` (attach them to the notebook), then Run All. Keys are never
typed into cells and never printed. The notebook tests TMDB, Gemini, the LangChain tool, Gemini tool
calling, the agent and the no-result case, and prints the agent's steps (tool call, TMDB results, final answer).

Known limitation: TMDB's search endpoint matches movie *titles*, not genres or ratings, so the agent
searches for specific titles it suggests and judges the returned data itself.

## Setup

```bash
# 1. clone
git clone https://github.com/Malik8122/cinemate-movie-agent.git
cd cinemate-movie-agent

# 2. create and activate an environment
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)

# 3. install requirements
pip install -r requirements.txt

# 4. configure secrets: copy the template, then edit .env with your own keys
copy .env.example .env          # macOS/Linux: cp .env.example .env

# 5. run the tests (no keys needed for unit tests)
python -m pytest
```

Optional, with real keys in `.env`:

```bash
python -m pytest -m live -v     # live TMDB + Gemini checks (incl. tool calling)
set PYTHONPATH=src              # Windows cmd (PowerShell: $env:PYTHONPATH="src"; macOS/Linux: export PYTHONPATH=src)
python -m cinemate.app          # smoke check: TMDB tool + Gemini
```

`.env` is git-ignored; never commit real keys.
