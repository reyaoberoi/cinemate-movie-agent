# Phase 2 Progress

## Status
**Phase 2 core pipeline working: 9 of 9 live tests passed on Kaggle (21 September 2026).**

User question → Gemini LangChain agent → `search_movies` tool → TMDB API → movie data → Gemini → recommendation.

## Date
21 September 2026

## Environment
| Item | Value |
|---|---|
| Execution environment | Kaggle Notebook (`notebooks/CineMate_Phase2.ipynb`), internet on, run from the Kaggle web UI with Kaggle Secrets |
| Code version tested | GitHub `main` at commit `9e707b0` (the notebook clones the repository; the Kaggle run's clone was verified to be this commit) |
| Python | 3.12 on Kaggle (3.12.13 in the run log of an earlier run) |
| LLM | Google Gemini, model `gemini-3.1-flash-lite` (free tier) |
| LangChain packages | pinned in `requirements.txt`: `langchain` 1.4.2, `langchain-core` 1.6.4, `langchain-google-genai` 4.4.0 (the notebook installs the pins if the preinstalled versions differ; the printed versions from the final run were not re-checked for this report) |
| Secrets | `TMDB_API_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL` from Kaggle Secrets; none are stored in the repository or notebook |

**Why Kaggle:** the development laptop could not reach TMDB. Its Wi-Fi DNS resolver returned an ISP sinkhole address (`49.44.79.236`) for `api.themoviedb.org`, so requests timed out. Google/Cloudflare DNS returned TMDB's real addresses, and a request sent straight to the real address got a normal TMDB `401` reply. TMDB itself was up; only local DNS was affected. Kaggle's network resolves TMDB correctly, so it was used for live testing. Kaggle is not required by the application itself.

## Live Test Results (Kaggle, 9/9)
| # | Test | What it checks | Result |
|---|---|---|---|
| 1 | Configuration | Required secrets are present and readable | PASS |
| 2 | TMDB search "Inception" | Real TMDB response through `tmdb_client`, result includes Inception | PASS |
| 3 | TMDB no-result search | Nonsense query returns `no_results` and an empty movie list | PASS |
| 4 | Gemini response | Model replies to "Respond with exactly: CineMate Gemini test successful." | PASS |
| 5 | LangChain tool → TMDB | `search_movies` tool invoked directly returns real TMDB data | PASS |
| 6 | Gemini tool calling | Gemini, bound to `search_movies`, requests the tool call | PASS |
| 7 | Agent: "Recommend some science-fiction movies." | Agent calls `search_movies` and returns a non-empty answer | PASS |
| 8 | Agent: "I want a thriller movie released after 2020 with a rating above 7." | Agent calls `search_movies` and returns a non-empty answer | PASS |
| 9 | Agent: "Recommend me a movie called XYZABC123456789." | Tool returns zero results; agent must not invent a movie | PASS |

**Passed: 9. Failed: 0. Skipped: 0.**

Note on evidence: results above are as reported from the Kaggle run. The run's printed output could not be downloaded through the Kaggle API for this report, so screenshots must come from the Kaggle notebook page. The notebook's automatic checks for tests 7 and 8 confirm the tool was called and an answer was produced; they do not score answer quality. Test 9's automatic check confirms the tool returned zero results; whether the answer avoided inventing a movie is confirmed by reading the printed answer.

## Integration Summary
**LangChain**
- Agent: LangChain 1.x `create_agent` (no legacy `AgentExecutor`) with Gemini, the `search_movies` tool and the CineMate system prompt.
- Tool: `search_movies` defined with `@tool`; returns readable text (title, year, rating, genres, overview), not raw JSON.
- Prompt: system prompt in `prompts.py` (also available as a `ChatPromptTemplate` with a chat-history placeholder for later memory). It tells the model not to invent facts, to use the tool for movie data, to say honestly when nothing is found, and to keep TMDB facts separate from its own judgement.
- LLM: `ChatGoogleGenerativeAI` via `langchain-google-genai`, built by `get_llm()` from environment variables (`retries=1` to protect free-tier quota).

**TMDB**
- `tmdb_client.search_movies(query, year=None)` calls TMDB v3 `/search/movie`, plus `/genre/movie/list` for genre names; supports API-key and Bearer-token authentication.
- Returns a `SearchResult` (`success`, `status`, `message`, `movies`) instead of raising. Statuses: `ok`, `no_results`, `invalid_request`, `auth_error`, `api_error`, `network_error`, `unexpected_response`.
- Separate connect (4 s) and read (10 s) timeouts, so it fails quickly instead of hanging.

**Tool-calling behaviour observed**
- Gemini decides on its own to call `search_movies`. In one local check (TMDB unreachable from the laptop) it issued three tool calls for specific titles it chose (Blade Runner 2049, Arrival, The Matrix), received the tool result, and wrote a final answer.
- When the tool returned only a network error, the model said it could not reach the movie database and asked a clarifying question; it named no movies and invented no ratings.
- Gemini can return several tool calls in one step, so one user question may produce several TMDB requests.

## Offline Tests
29 offline tests pass (`python -m pytest -m "not live"`): mocked TMDB client and tool behaviour, error statuses, configuration errors, prompt rendering, Gemini model construction, and the agent loop with a scripted fake model. 4 live tests skip unless real keys and network access are available.

## Limitations
- **TMDB search is by title, not by genre or filter.** `/search/movie` matches text in movie titles. The agent therefore searches for specific titles it proposes and judges the returned data itself. Preferences such as "after 2020" or "rating above 7" are applied by the LLM to retrieved data, not by TMDB. The system prompt states this. TMDB `/discover/movie` (genre, year, rating, runtime filters) is the better fit for refinement and follow-ups and is a candidate for the next phase.
- **Gemini free tier is limited.** `gemini-3.5-flash` returned `429 RESOURCE_EXHAUSTED` (20 requests/day/model, free tier). `gemini-2.5-flash` was not found. `gemini-3.1-flash-lite` works, but returned a temporary `503 UNAVAILABLE` ("high demand") once and then succeeded on retry. One full notebook run uses roughly 8 Gemini requests, so repeated runs can exhaust the daily quota.
- **Kaggle Secrets do not load in runs started through the Kaggle API** (`ConnectionError` from the secrets service). The notebook works when run from the Kaggle web UI.
- **Checks are lightweight.** The evaluation so far is 9 scenario tests. Answer quality, recommendation relevance and repeatability have not been measured.
- Not implemented yet: conversational memory, structured output, UI, movie comparison.

## Pending
- Conversational memory and follow-up handling ("only after 2020", "under 2 hours").
- Structured output / OutputParser.
- Decide whether to add a TMDB discover-based tool for genre/year/rating/runtime filtering.
- Evaluation, UI, demo, final report.

## Technical Decisions
- LangChain 1.x current APIs only (`create_agent`, `@tool`, `ChatPromptTemplate`); no deprecated agent classes.
- The TMDB client never raises for normal problems; the agent always receives a safe, readable message.
- Only the top 5 TMDB results are passed to the LLM to keep context small.
- Secrets come only from environment variables / `.env` (git-ignored) or Kaggle Secrets; `.env.example` holds placeholders only.
- The project has its own git repository (the home directory is also a git repo, so commits from here would otherwise have gone there).

## Problems Encountered and Solutions
| Problem | Cause | Solution |
|---|---|---|
| Live TMDB requests timed out locally | ISP DNS returns a sinkhole address for TMDB | Live testing on Kaggle; client timeouts and clear error messages |
| Gemini `429` on `gemini-3.5-flash` | Free-tier daily quota used up (library default of 6 retries also consumed requests) | Switched to `gemini-3.1-flash-lite`; `get_llm(retries=1)` |
| Gemini `503` "high demand" | Temporary provider capacity | Single retry succeeded; no retry loops |
| Kaggle run failed at first | GitHub repository was still empty | Pushed the code to GitHub |
| Kaggle Secrets not readable in API-triggered runs | Secrets service unreachable from API runs | Run from the Kaggle web UI |
