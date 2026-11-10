from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PilotPoint:
    id: str
    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class PilotEdge:
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
    editable: bool = True
    bidirectional: bool = True
    headway_intervals_h: tuple[float, ...] = ()


@dataclass(frozen=True, slots=True)
class PilotPair:
    id: str
    from_id: str
    to_id: str


@dataclass(frozen=True, slots=True)
class Pilot:
    id: str
    name: str
    model_version: str
    artifact_version: str
    points: tuple[PilotPoint, ...]
    edges: tuple[PilotEdge, ...]
    pairs: tuple[PilotPair, ...]
    assumptions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EdgeChange:
    edge_id: str
    enabled: bool | None = None
    frequency_per_week: int | None = None


@dataclass(frozen=True, slots=True)
class PilotRoute:
    status: str
    total_h: float | None
    travel_h: float | None
    waiting_h: float | None
    edge_ids: tuple[str, ...]
    point_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    optimality: str = "within_model"


@dataclass(frozen=True, slots=True)
class PairComparison:
    pair_id: str
    baseline: PilotRoute
    changed: PilotRoute
    optimistic_baseline: PilotRoute
    optimistic_changed: PilotRoute
    delta_h: float | None


@dataclass(frozen=True, slots=True)
class WaitingSensitivity:
    edge_id: str
    intervals_h: tuple[float, ...]
    periodic_wait_h: float
    uniform_wait_h: float | None
    difference_h: float | None


@dataclass(frozen=True, slots=True)
class PilotEvaluation:
    pilot_id: str
    season: str
    model_version: str
    artifact_version: str
    changes: tuple[EdgeChange, ...]
    pairs: tuple[PairComparison, ...]
    assumptions: tuple[str, ...]
    waiting_sensitivity: tuple[WaitingSensitivity, ...] = ()
