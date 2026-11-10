from dataclasses import dataclass, field
from typing import Literal, Protocol

from app.domain.errors import DataUnavailable, InvalidQuery, RegionNotFound
from app.domain.road_analysis import SettlementImpact
from app.usecase.dto import BoundaryShape
from app.usecase.interface import AtlasRepository

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


class AnalysisPort(Protocol):
    def submit(self, boundary: BoundaryShape, mode: AnalysisMode, percent: int) -> AnalysisJob: ...
    def recent(self) -> list[AnalysisJob]: ...
    def get(self, analysis_id: str) -> AnalysisJob: ...
    def resume(self, analysis_id: str) -> AnalysisJob: ...
    def cancel(self, analysis_id: str) -> AnalysisJob: ...
    def detail(self, analysis_id: str, way_id: int) -> AnalysisDetail: ...


class RoadAnalysis:
    def __init__(self, engine: AnalysisPort | None, atlas: AtlasRepository) -> None:
        self._engine = engine
        self.atlas = atlas

    @property
    def engine(self) -> AnalysisPort:
        if self._engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self._engine

    def submit(self, region_id: str, mode: AnalysisMode, percent: int = 20) -> AnalysisJob:
        if (
            mode not in {"criticality", "improvement"}
            or type(percent) is not int
            or not 1 <= percent <= 200
        ):
            raise InvalidQuery("Invalid analysis mode or improvement percentage")
        if not any(r.id == region_id for r in self.atlas.regions()):
            raise RegionNotFound()
        boundary = next((b for b in self.atlas.boundaries() if b.id == region_id), None)
        if boundary is None:
            raise DataUnavailable("Region boundary is missing")
        return self.engine.submit(boundary, mode, percent if mode == "improvement" else 0)

    def recent(self) -> list[AnalysisJob]:
        return self.engine.recent()

    def get(self, analysis_id: str) -> AnalysisJob:
        return self.engine.get(analysis_id)

    def resume(self, analysis_id: str) -> AnalysisJob:
        return self.engine.resume(analysis_id)

    def cancel(self, analysis_id: str) -> AnalysisJob:
        return self.engine.cancel(analysis_id)

    def detail(self, analysis_id: str, way_id: int) -> AnalysisDetail:
        return self.engine.detail(analysis_id, way_id)


class AnalysisStore(Protocol):
    def load(self) -> list[tuple[AnalysisJob, BoundaryShape]]: ...
    def save(self, job: AnalysisJob, boundary: BoundaryShape) -> None: ...
    def save_detail(self, analysis_id: str, detail: AnalysisDetail) -> None: ...
    def detail(self, analysis_id: str, way_id: int) -> AnalysisDetail: ...
