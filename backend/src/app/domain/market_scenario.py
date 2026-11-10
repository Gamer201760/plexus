from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

BETA_PER_H = float(np.log(2.0) / 2.0)
TRUNK_OVERHEAD_H = {"air": 2.5, "rail": 1.0, "road": 0.0}
SCHEDULED_TRUNK_MODES = frozenset({"air", "rail"})
WEEKLY_WAIT_H = 84.0
ASSUMED_FREQUENCY_PER_WEEK = 1
MAX_PAIR_CHANGES = 30
SETTLEMENT_LINK_NOTE = "settlement_links_serve_named_endpoints_only"


@dataclass(frozen=True, slots=True)
class MarketCity:
    id: str
    region: str
    population: float
    latitude: float
    longitude: float
    is_capital: bool


@dataclass(frozen=True, slots=True)
class ScenarioRegion:
    region_id: str
    name: str


@dataclass(frozen=True, slots=True)
class ScenarioCatalog:
    model_version: str
    artifact_version: str
    seasons: tuple[str, ...]
    cities: tuple[MarketCity, ...]
    regions: tuple[ScenarioRegion, ...]
    assumptions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScenarioModel:
    season: str
    model_version: str
    artifact_version: str
    normalization_base: float
    cities: tuple[MarketCity, ...]
    regions: tuple[ScenarioRegion, ...]
    road_h: NDArray[np.float32]
    best_h: NDArray[np.float32]
    city_best_h: NDArray[np.float64]
    population: NDArray[np.float64]
    region_idx: NDArray[np.int32]
    point_index: dict[str, int]
    point_access: NDArray[np.float64]
    region_access: NDArray[np.float64]
    region_population: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class NewTrunkLink:
    from_id: str
    to_id: str
    mode: str
    travel_h: float
    frequency_per_week: int | None = None


@dataclass(frozen=True, slots=True)
class CityPairChange:
    from_city: str
    to_city: str
    baseline_h: float | None
    changed_h: float


@dataclass(frozen=True, slots=True)
class SettlementImpact:
    point_id: str
    baseline_index: float
    changed_index: float
    delta_index: float


@dataclass(frozen=True, slots=True)
class RegionImpact:
    region_id: str
    name: str
    population: float
    baseline_index: float
    changed_index: float
    delta_index: float


@dataclass(frozen=True, slots=True)
class ScenarioEvaluation:
    season: str
    model_version: str
    artifact_version: str
    links: tuple[NewTrunkLink, ...]
    assumptions: tuple[str, ...]
    national_baseline_index: float
    national_changed_index: float
    improved_city_pairs: int
    city_pairs: tuple[CityPairChange, ...]
    regions: tuple[RegionImpact, ...]
    settlements: tuple[SettlementImpact, ...]
