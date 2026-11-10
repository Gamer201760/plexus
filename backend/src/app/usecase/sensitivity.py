import math
from dataclasses import dataclass

from app.domain.errors import DataUnavailable, RegionNotFound
from app.domain.transport import NetworkMode, Season
from app.usecase.index_status import resolved_scenario
from app.usecase.interface.atlas import AtlasRepository


@dataclass(frozen=True, slots=True)
class SensitivityPoint:
    time_multiplier: float
    hansen: float
    delta: float
    relative_change: float


@dataclass(frozen=True, slots=True)
class SensitivityResult:
    region_id: str
    scenario: str
    model_version: str | None
    artifact_version: str | None
    baseline: float
    points: tuple[SensitivityPoint, ...]
    kind: str = "uniform_time_sensitivity"
    graph_recomputed: bool = False
    assumptions: tuple[str, ...] = (
        "every_origin_to_market_time_scaled_uniformly",
        "market_weights_coverage_and_road_normalization_fixed",
        "uses_exported_half_life_1_2_4_hour_sums",
        "not_a_specific_road_project_or_forecast",
        "no_new_routes_or_connectivity_changes",
    )


class AccessibilitySensitivity:
    def __init__(self, repository: AtlasRepository) -> None:
        self._repository = repository

    def evaluate(
        self, region_id: str, season: Season, network: NetworkMode
    ) -> SensitivityResult:
        if not any(region.id == region_id for region in self._repository.regions()):
            raise RegionNotFound()
        scenario = resolved_scenario(self._repository.indices(), season, network)
        row = next((item for item in self._repository.indices()
                    if item.region_id == region_id and item.scenario == scenario), None)
        if row is None or row.hansen is None or row.hansen_2h is None:
            raise DataUnavailable("Regional sensitivity export is missing")
        if not all(math.isfinite(value) and value > 0 for value in (row.hansen_2h, row.hansen)):
            raise DataUnavailable("Positive baseline is required to recover fixed normalization")
        points = []
        for multiplier, raw in ((0.5, row.hansen_4h), (1.0, row.hansen_2h), (2.0, row.hansen_1h)):
            if raw is None or not math.isfinite(raw) or raw < 0:
                raise DataUnavailable("Finite half-life sensitivity sums are required")
            value = row.hansen * raw / row.hansen_2h
            points.append(SensitivityPoint(multiplier, value, value - row.hansen,
                                           value / row.hansen - 1))
        return SensitivityResult(region_id, scenario, row.model_version, row.artifact_version,
                                 row.hansen, tuple(points))
