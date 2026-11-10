import asyncio
from collections.abc import AsyncGenerator
from dataclasses import replace
from unittest.mock import Mock

import pytest

from app.domain.errors import DataUnavailable
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import Chat, ChatContext, ChatEvent, ChatRequest
from app.usecase.road_analysis import AnalysisJob, Candidate, VerifiedRoad


class RecordingProvider:
    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []

    async def stream(self, request: ChatRequest) -> AsyncGenerator[ChatEvent, None]:
        self.requests.append(request)
        yield ChatEvent("delta", text="Verified commentary")
        yield ChatEvent("done")


def review_request() -> ChatRequest:
    return ChatRequest(
        "Invent a ranking", (), ChatContext(None, Season.WINTER, NetworkMode.ROAD, "hansen"), "job"
    )


def analysis_job() -> AnalysisJob:
    road = Candidate(100, "Road A", 4, 1, 0, False)
    return AnalysisJob(
        "job", "16", "Region", "improvement", 20, "snapshot", status="paused",
        results=[VerifiedRoad(road, 100, 100.2, 0.2, 500, 0, 1)],
    )


def test_review_uses_saved_results_and_discards_client_claims() -> None:
    provider = RecordingProvider()
    analysis = Mock()
    analysis.get.return_value = analysis_job()
    events = asyncio.run(collect(Chat(provider, analysis)))
    assert events[-1].type == "done"
    assert len(provider.requests) == 1
    prompt = provider.requests[0].prompt
    assert '"delta": 0.2' in prompt
    assert '"affected_population": 500' in prompt
    assert "Invent a ranking" not in prompt
    assert provider.requests[0].analysis_id == "job"
    analysis.submit.assert_not_called()
    analysis.resume.assert_not_called()


@pytest.mark.parametrize("status", ["queued", "running", "failed", "cancelled", "interrupted"])
def test_incomplete_analysis_never_calls_model(status: str) -> None:
    provider = RecordingProvider()
    analysis = Mock()
    analysis.get.return_value = replace(analysis_job(), status=status)
    events = asyncio.run(collect(Chat(provider, analysis)))
    assert events[0].code == "chat_analysis_not_ready"
    assert provider.requests == []


def test_missing_analysis_returns_stream_error_without_model_call() -> None:
    provider = RecordingProvider()
    analysis = Mock()
    analysis.get.side_effect = DataUnavailable("Missing analysis")
    events = asyncio.run(collect(Chat(provider, analysis)))
    assert events[0].code == "chat_analysis_unavailable"
    assert provider.requests == []


async def collect(chat: Chat) -> list[ChatEvent]:
    return [event async for event in chat.stream(review_request())]
