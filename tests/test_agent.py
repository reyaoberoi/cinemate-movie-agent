"""Offline test of the agent loop: real create_agent + real tool, fake model, mocked TMDB HTTP."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from cinemate import tmdb_client
from cinemate.agent import ask, build_agent
from conftest import INCEPTION, FakeResponse, route


class ScriptedToolModel(BaseChatModel):
    """Requests one search_movies call, then answers using whatever the tool returned."""

    query: str = "Inception"

    @property
    def _llm_type(self) -> str:
        return "scripted-tool-model"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        last = messages[-1]
        if last.type == "tool":
            msg = AIMessage(content=f"Based on the retrieved data: {last.content[:60]}")
        else:
            msg = AIMessage(content="", tool_calls=[
                {"name": "search_movies", "args": {"query": self.query}, "id": "call-1"}])
        return ChatResult(generations=[ChatGeneration(message=msg)])


def test_agent_calls_tool_then_answers_from_tmdb_data(monkeypatch, capsys):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, {"results": [INCEPTION]})))
    answer = ask(build_agent(llm=ScriptedToolModel()), "Tell me about Inception")
    out = capsys.readouterr().out
    assert "Calling tool: search_movies" in out
    assert "Query: Inception" in out
    assert "Retrieved results: 1" in out
    assert "Inception (2010)" in answer  # the answer was built from the tool output


def test_agent_no_results_is_visible_and_not_invented(monkeypatch, capsys):
    monkeypatch.setattr(tmdb_client.requests, "get", route(FakeResponse(200, {"results": []})))
    answer = ask(build_agent(llm=ScriptedToolModel(query="XYZABC123456789")), "Recommend XYZABC123456789")
    out = capsys.readouterr().out
    assert "Retrieved results: 0" in out
    assert "No movies found" in answer
