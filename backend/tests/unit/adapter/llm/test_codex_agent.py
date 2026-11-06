from types import TracebackType
from typing import Any, Self

import pytest
from openai_codex import ApprovalMode, CodexConfig, Sandbox, TransportClosedError, TurnResult
from openai_codex.types import ReasoningEffort, ThreadTokenUsage, TurnError, TurnStatus

from app.adapter.llm import codex_agent
from app.adapter.llm.codex_agent import CodexAgentModel
from app.domain.errors import ModelFailure
from app.domain.inference import Effort, StructuredRequest, Tier

SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}}}
REQUEST = StructuredRequest(
    system="Answer briefly", prompt="Ping", schema=SCHEMA, tier=Tier.SMART, effort=Effort.LOW
)
TOKENS = {
    "cachedInputTokens": 0,
    "inputTokens": 10,
    "outputTokens": 5,
    "reasoningOutputTokens": 2,
    "totalTokens": 15,
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def result(**overrides: Any) -> TurnResult:
    fields: dict[str, Any] = {
        "id": "turn",
        "status": TurnStatus.completed,
        "error": None,
        "started_at": 1,
        "completed_at": 2,
        "duration_ms": 120,
        "final_response": '{"answer": "pong"}',
        "items": [],
        "usage": ThreadTokenUsage.model_validate({"last": TOKENS, "total": TOKENS}),
    }
    return TurnResult(**(fields | overrides))


class FakeThread:
    def __init__(self, outcome: TurnResult | Exception, calls: dict[str, Any]) -> None:
        self._outcome = outcome
        self._calls = calls

    async def run(self, prompt: str, **options: Any) -> TurnResult:
        self._calls["run"] = {"prompt": prompt, **options}
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


def fake_codex(outcome: TurnResult | Exception, calls: dict[str, Any] | None = None) -> Any:
    seen = calls if calls is not None else {}

    class FakeCodex:
        def __init__(self, config: CodexConfig) -> None:
            seen["config"] = config

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            return None

        async def thread_start(self, **options: Any) -> FakeThread:
            seen["thread_start"] = options
            return FakeThread(outcome, seen)

    return FakeCodex


@pytest.mark.anyio
async def test_returns_structured_output_and_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, Any] = {}
    monkeypatch.setattr(codex_agent, "AsyncCodex", fake_codex(result(), calls))

    completion = await CodexAgentModel().complete(REQUEST)

    assert completion.output == {"answer": "pong"}
    assert completion.usage.model == "gpt-6.1-sol"
    assert completion.usage.duration_ms == 120
    assert completion.usage.input_tokens == 10
    assert completion.usage.output_tokens == 5
    assert completion.usage.cost_usd is None
    assert "features.shell_tool=false" in calls["config"].config_overrides
    assert "project_doc_max_bytes=0" in calls["config"].config_overrides
    start = calls["thread_start"]
    assert start["approval_mode"] == ApprovalMode.deny_all
    assert start["sandbox"] == Sandbox.read_only
    assert start["ephemeral"] is True
    assert start["base_instructions"] == "Answer briefly"
    assert start["cwd"] == calls["config"].cwd
    assert calls["run"] == {
        "prompt": "Ping",
        "effort": ReasoningEffort.low,
        "output_schema": SCHEMA,
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "outcome",
    [
        result(status=TurnStatus.interrupted),
        result(status=TurnStatus.failed, error=TurnError(message="overloaded")),
        result(final_response=None),
        result(final_response="plain text"),
        result(final_response='["not", "object"]'),
        RuntimeError("turn failed"),
        TransportClosedError("cli exited"),
    ],
    ids=["interrupted", "failed", "no-response", "unstructured", "not-object", "turn-error", "sdk"],
)
async def test_failures_become_model_failure(
    monkeypatch: pytest.MonkeyPatch, outcome: TurnResult | Exception
) -> None:
    monkeypatch.setattr(codex_agent, "AsyncCodex", fake_codex(outcome))

    with pytest.raises(ModelFailure):
        await CodexAgentModel().complete(REQUEST)
