"""Entry point. For now this is a smoke check of the foundation (tool + LLM).

Run:  python -m cinemate.app
The interactive agent app will be added once the agent works.
"""

from cinemate.config import ConfigError
from cinemate.tools import search_movies


def check_tool() -> None:
    print("=== TMDB tool: 'Inception' ===")
    output = search_movies.invoke({"query": "Inception"})
    print(output)
    if "(network_error)" in output:
        print("\nTMDB is unreachable from this network, skipping the remaining TMDB check.")
        return
    print("\n=== TMDB tool: nonexistent movie ===")
    print(search_movies.invoke({"query": "qzxwvbnm asdfghjkl 987654"}))


def check_llm() -> None:
    from cinemate.agent import get_llm
    from cinemate.prompts import CINEMATE_PROMPT

    print("\n=== Gemini: prompt | model ===")
    chain = CINEMATE_PROMPT | get_llm()  # LCEL: prompt template piped into the model
    reply = chain.invoke({"input": "Say hello and introduce yourself in one sentence."})
    print(reply.content)


def main() -> None:
    try:
        check_tool()
    except ConfigError as e:
        print(f"\nConfiguration problem: {e}")
        return
    try:
        check_llm()
    except ConfigError as e:
        print(f"\nConfiguration problem: {e}")
    except Exception as e:  # provider errors (overload, quota, bad model name...): report, don't dump a traceback
        print(f"\nGemini call failed: {type(e).__name__}: {str(e)[:300]}")


if __name__ == "__main__":
    main()
