"""LLM configuration and the CineMate agent (LangChain 1.x `create_agent`).

Flow: user question -> agent (Gemini) -> search_movies tool -> TMDB -> tool result -> Gemini -> answer.
No memory, structured output or UI yet.
"""

import re
from typing import Optional

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from cinemate.config import get_gemini_api_key, get_model_name
from cinemate.prompts import SYSTEM_PROMPT
from cinemate.tools import search_movies


def get_llm(retries: int = 1) -> ChatGoogleGenerativeAI:
    """Build the Gemini chat model from environment configuration (no hardcoded secrets).

    Temperature is left at the provider default (recommended for Gemini 3 models).
    retries defaults to 1: the library default is 6, which quietly burns free-tier quota on 503/429.
    """
    return ChatGoogleGenerativeAI(model=get_model_name(), api_key=get_gemini_api_key(), retries=retries)


def build_agent(llm=None):
    """Create the CineMate agent: Gemini + the search_movies tool + the CineMate system prompt."""
    return create_agent(
        model=llm or get_llm(),
        tools=[search_movies],
        system_prompt=SYSTEM_PROMPT,
    )


def _count_results(tool_output: str) -> int:
    """The tool lists movies as '1. Title (year) ...'; count those lines."""
    return len(re.findall(r"^\d+\. ", tool_output, flags=re.MULTILINE))


def print_trace(messages) -> None:
    """Print the agent's steps so the agentic workflow is visible (no secrets are in messages)."""
    for m in messages:
        if m.type == "human":
            print(f"[USER]\n{m.text}\n")
        elif m.type == "ai" and m.tool_calls:
            for call in m.tool_calls:
                args = call["args"]
                extra = f" (year={args['year']})" if args.get("year") else ""
                print(f"[AGENT]\nCalling tool: {call['name']}\n")
                print(f"[TOOL]\nQuery: {args.get('query')}{extra}\n")
        elif m.type == "tool":
            print(f"[TMDB]\nRetrieved results: {_count_results(m.text)}")
            print(f"--- data returned to the agent ---\n{m.text}\n----------------------------------\n")
        elif m.type == "ai":
            print("[AGENT]\nGenerating final response\n")
            print(f"[CINEMATE]\n{m.text}\n")


def run(agent, question: str) -> list:
    """Send one question to the agent; return the full message list (user, tool calls, tool results, answer)."""
    return agent.invoke({"messages": [{"role": "user", "content": question}]})["messages"]


def final_answer(messages) -> str:
    final = next((m for m in reversed(messages) if m.type == "ai" and not m.tool_calls), None)
    return final.text if final else ""


def tools_called(messages) -> list[str]:
    return [c["name"] for m in messages if m.type == "ai" for c in m.tool_calls]


def ask(agent, question: str, verbose: bool = True) -> str:
    """Send one question to the agent and return the final answer text."""
    messages = run(agent, question)
    if verbose:
        print_trace(messages)
    return final_answer(messages)
