from dataclasses import dataclass, field
from typing import Literal

from app.domain.road_analysis import SettlementImpact

AnalysisMode = Literal["criticality", "improvement"]


@dataclass(frozen=True)
class Candidate:
    way_id: int
    name: str
    length_km: float
    score: float
    isolation_score: float
    crosses_boundary: bool


@dataclass(frozen=True)
class VerifiedRoad:
    candidate: Candidate
    before: float
    after: float
    delta: float
    affected_population: int
    isolated_population: int
    elapsed_seconds: float


@dataclass(frozen=True)
class AnalysisFailure:
    way_id: int
    code: str


@dataclass(frozen=True)
class ImpactLocation:
    impact: SettlementImpact
    name: str
    longitude: float
    latitude: float


@dataclass(frozen=True)
class AnalysisDetail:
    result: VerifiedRoad
    lines: list[list[list[float]]]
    settlements: list[ImpactLocation]


@dataclass(frozen=True)
class AnalysisJob:
    id: str
    region_id: str
    region: str
    mode: AnalysisMode
    percent: int
    fingerprint: str
    status: str = "queued"
    stage: str = "preparing"
    candidates: list[Candidate] = field(default_factory=list)
    results: list[VerifiedRoad] = field(default_factory=list)
    failures: list[AnalysisFailure] = field(default_factory=list)
    candidate_count: int = 0
    batch_target: int = 10
    current_way_id: int | None = None
    completed: int = 0
    total: int = 0
    elapsed_seconds: float = 0
    error: str | None = None
    compatible: bool = True
