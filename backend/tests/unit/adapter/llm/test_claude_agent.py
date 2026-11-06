from collections.abc import AsyncIterator
from typing import Any

import pytest
from claude_agent_sdk import ClaudeAgentOptions, CLIConnectionError, ResultMessage

from app.adapter.llm import claude_agent
from app.adapter.llm.claude_agent import ClaudeAgentModel
from app.domain.errors import ModelFailure
from app.domain.inference import Effort, StructuredRequest, Tier

SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}}}
REQUEST = StructuredRequest(
    system="Answer briefly", prompt="Ping", schema=SCHEMA, tier=Tier.SMART, effort=Effort.LOW
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def result(**overrides: Any) -> ResultMessage:
    fields: dict[str, Any] = {
        "subtype": "success",
        "duration_ms": 120,
        "duration_api_ms": 100,
        "is_error": False,
        "num_turns": 1,
        "session_id": "session",
        "usage": {"input_tokens": 10, "output_tokens": 5},
        "total_cost_usd": 0.001,
        "structured_output": {"answer": "pong"},
    }
    return ResultMessage(**(fields | overrides))


def fake_query(messages: list[Any], seen: list[ClaudeAgentOptions] | None = None) -> Any:
    async def run(*, prompt: str, options: ClaudeAgentOptions) -> AsyncIterator[Any]:
        if seen is not None:
            seen.append(options)
        for message in messages:
            if isinstance(message, Exception):
                raise message
            yield message

    return run


@pytest.mark.anyio
async def test_returns_structured_output_and_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[ClaudeAgentOptions] = []
    monkeypatch.setattr(claude_agent, "query", fake_query([result()], seen))

    completion = await ClaudeAgentModel().complete(REQUEST)

    assert completion.output == {"answer": "pong"}
    assert completion.usage.model == "sonnet"
    assert completion.usage.input_tokens == 10
    assert completion.usage.output_tokens == 5
    assert completion.usage.cost_usd == 0.001
    options = seen[0]
    assert options.tools == []
    assert options.setting_sources == []
    assert options.effort == "low"
    assert options.output_format == {"type": "json_schema", "schema": SCHEMA}


@pytest.mark.anyio
@pytest.mark.parametrize(
    "messages",
    [
        [],
        [result(is_error=True, errors=["overloaded"])],
        [result(structured_output=None, result="plain text")],
        [CLIConnectionError("cli missing")],
    ],
    ids=["no-result", "error-result", "unstructured", "sdk-error"],
)
async def test_failures_become_model_failure(
    monkeypatch: pytest.MonkeyPatch, messages: list[Any]
) -> None:
    monkeypatch.setattr(claude_agent, "query", fake_query(messages))

    with pytest.raises(ModelFailure):
        await ClaudeAgentModel().complete(REQUEST)
