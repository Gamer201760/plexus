from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EdgeChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    edge_id: str = Field(min_length=1, max_length=120)
    enabled: bool | None = Field(default=None, strict=True)
    frequency_per_week: int | None = Field(default=None, ge=1, le=28, strict=True)


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    season: Literal["summer", "winter"]
    model_version: str = Field(min_length=1, max_length=120)
    artifact_version: str = Field(min_length=1, max_length=120)
    changes: tuple[EdgeChangeRequest, ...] = Field(default=(), max_length=50)


class PointResponse(Response):
    id: str
    name: str
    latitude: float
    longitude: float


class EdgeResponse(Response):
    id: str
    from_id: str
    to_id: str
    mode: str
    seasons: tuple[str, ...]
    travel_h: float
    frequency_per_week: float | None
    assumed_frequency_per_week: float | None
    source_url: str
    source_period: str | None
    assumptions: tuple[str, ...]
    editable: bool
    bidirectional: bool
    headway_intervals_h: tuple[float, ...]
    frequency_editable: bool
    edit_disabled_reason: str | None


class PairResponse(Response):
    id: str
    from_id: str
    to_id: str


class PilotSummaryResponse(Response):
    id: str
    name: str
    model_version: str
    artifact_version: str
    point_count: int
    edge_count: int
    pair_count: int
    unknown_frequency_links: int


class PilotResponse(Response):
    id: str
    name: str
    model_version: str
    artifact_version: str
    points: tuple[PointResponse, ...]
    edges: tuple[EdgeResponse, ...]
    pairs: tuple[PairResponse, ...]
    assumptions: tuple[str, ...]


class PilotRouteResponse(Response):
    status: Literal["found", "no_route", "insufficient_data"]
    total_h: float | None
    travel_h: float | None
    waiting_h: float | None
    edge_ids: tuple[str, ...]
    point_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    optimality: Literal["within_model", "incomplete_alternatives"]


class PairComparisonResponse(Response):
    pair_id: str
    baseline: PilotRouteResponse
    changed: PilotRouteResponse
    optimistic_baseline: PilotRouteResponse
    optimistic_changed: PilotRouteResponse
    delta_h: float | None


class WaitingSensitivityResponse(Response):
    edge_id: str
    intervals_h: tuple[float, ...]
    periodic_wait_h: float
    uniform_wait_h: float | None
    difference_h: float | None


class EvaluationResponse(Response):
    pilot_id: str
    season: str
    model_version: str
    artifact_version: str
    changes: tuple[EdgeChangeRequest, ...]
    pairs: tuple[PairComparisonResponse, ...]
    assumptions: tuple[str, ...]
    waiting_sensitivity: tuple[WaitingSensitivityResponse, ...]
