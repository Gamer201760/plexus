from dataclasses import dataclass, field
from typing import Any

from app.domain.road_economics import MoneyAssumptions, MoneyEffect


@dataclass(frozen=True)
class RoadSegment:
    way_id: int
    name: str
    highway: str
    speed_kmh: float
    coordinates: list[list[float]]
    source_node: int | None = None
    target_node: int | None = None


@dataclass(frozen=True)
class GraphLocation:
    point_id: str
    name: str
    region: str
    node: int | None
    longitude: float
    latitude: float
    snap_km: float


@dataclass(frozen=True)
class RoadView:
    segments: list[RoadSegment]
    matched: int
    truncated: bool
    version: str
    detail: str = "all"


@dataclass(frozen=True)
class RoadChange:
    way_id: int
    speed_factor: float


@dataclass(frozen=True)
class RoadAddition:
    source_node: int
    target_node: int
    travel_hours: float
    coordinates: list[list[float]] | None = None


@dataclass(frozen=True)
class SettlementEffect:
    point_id: str
    before: float
    after: float
    delta: float


@dataclass(frozen=True)
class RoadResult:
    before: float
    after: float
    delta: float
    relative_percent: float | None
    population: int
    settlements: int
    changed_edges: int
    normalization: float
    elapsed_seconds: float
    affected_settlements: int | None = None
    money: MoneyEffect | None = None
    routing_method: str = "full_graph"
    settlement_effects: list[SettlementEffect] = field(default_factory=list)


@dataclass(frozen=True)
class RoadJob:
    id: str
    region_id: str
    region: str
    scenario: str
    changes: list[RoadChange]
    status: str
    completed: int
    total: int
    version: str
    result: RoadResult | None = None
    error: str | None = None
    addition: RoadAddition | None = None
    money_assumptions: MoneyAssumptions | None = None


@dataclass
class DeltaRegion:
    ids: list[str]
    nodes: Any
    snaps: Any
    population: Any
    roads: Any
    city_roads: Any
    trunk: Any
    market_nodes: Any
    market_snaps: Any
    market_weights: Any
    market_names: list[str]
    normalization: float
    expected: float
    baseline_times: Any = None
    baseline_hansen: Any = None
    baseline_index: float = 0.0


GRAPH_DATA_VERSION = "data-20261107"
