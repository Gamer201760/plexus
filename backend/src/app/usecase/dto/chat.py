from dataclasses import dataclass
from typing import Literal

from app.domain.transport import NetworkMode, Season
from app.usecase.chat_artifacts import ChatChart, ChatTable
from app.usecase.chat_map import ChatMapCommand
from app.usecase.dto.road_analysis import (
    AnalysisJob,
)
from app.usecase.dto.road_corridor import CorridorCalculation


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class ChatContext:
    region_id: str | None
    season: Season
    network_mode: NetworkMode
    metric: str


@dataclass(frozen=True, slots=True)
class ChatRequest:
    prompt: str
    history: tuple[ChatMessage, ...]
    context: ChatContext
    analysis_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChatEvent:
    type: Literal[
        "status", "delta", "done", "error", "table", "chart", "map", "calculation", "analysis"
    ]
    text: str = ""
    code: str = ""
    table: ChatTable | None = None
    chart: ChatChart | None = None
    map: ChatMapCommand | None = None
    calculation: CorridorCalculation | None = None
    analysis: AnalysisJob | None = None
