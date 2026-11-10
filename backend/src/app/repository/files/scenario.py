import json
import math
from pathlib import Path
from threading import RLock

import numpy as np

from app.domain.errors import DataUnavailable
from app.domain.market_scenario import (
    MarketCity,
    ScenarioCatalog,
    ScenarioModel,
    ScenarioRegion,
    point_access,
    population_mean,
)

FILES = (
    "road_h.npy",
    "best_h.npy",
    "city_best_h.npy",
    "population.npy",
    "region_idx.npy",
    "point_id.npy",
)


def city_record(row: dict[str, object]) -> MarketCity:
    name, region = row.get("city"), row.get("region")
    population, lat, lon = row.get("population"), row.get("lat"), row.get("lon")
    capital = row.get("is_capital")
    if not isinstance(name, str) or not name or not isinstance(region, str):
        raise ValueError("invalid city")
    if not isinstance(capital, bool):
        raise TypeError("invalid capital flag")
    values = []
    for value in (population, lat, lon):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("invalid city number")
        values.append(float(value))
    if not all(math.isfinite(value) for value in values) or values[0] < 0:
        raise ValueError("invalid city number")
    return MarketCity(name, region, values[0], values[1], values[2], capital)


def region_record(row: dict[str, object]) -> ScenarioRegion:
    region_id, name = row.get("region_id"), row.get("name")
    if not isinstance(region_id, str) or not region_id or not isinstance(name, str) or not name:
        raise ValueError("invalid region")
    return ScenarioRegion(region_id, name)


class FilesScenarioRepository:
    def __init__(self, scenario_dir: Path) -> None:
        self._dir = scenario_dir
        self._lock = RLock()
        self._catalog: ScenarioCatalog | None = None
        self._models: dict[str, ScenarioModel] = {}

    def _manifest(self) -> dict[str, object]:
        try:
            manifest = json.loads((self._dir / "manifest.json").read_text())
        except (OSError, ValueError) as error:
            raise DataUnavailable("Scenario artifacts are missing") from error
        if not isinstance(manifest, dict):
            raise DataUnavailable("Invalid scenario manifest")
        return manifest

    def catalog(self) -> ScenarioCatalog:
        with self._lock:
            if self._catalog is None:
                manifest = self._manifest()
                try:
                    seasons = manifest["seasons"]
                    cities = manifest["cities"]
                    regions = manifest["regions"]
                    version = manifest["artifact_version"]
                    model = manifest["model_version"]
                    base = manifest["normalization_base"]
                    assumptions = manifest.get("assumptions", [])
                    if (
                        not isinstance(seasons, dict)
                        or not isinstance(cities, list)
                        or not isinstance(regions, list)
                        or not isinstance(version, str)
                        or not isinstance(model, str)
                        or not isinstance(base, float)
                        or not math.isfinite(base)
                        or base <= 0
                        or not isinstance(assumptions, list)
                        or not all(isinstance(item, str) for item in assumptions)
                    ):
                        raise ValueError("invalid manifest")
                    self._catalog = ScenarioCatalog(
                        model,
                        version,
                        tuple(sorted(seasons)),
                        tuple(city_record(row) for row in cities),
                        tuple(region_record(row) for row in regions),
                        tuple(assumptions),
                    )
                except (KeyError, TypeError, ValueError) as error:
                    raise DataUnavailable("Invalid scenario manifest") from error
            return self._catalog

    def model(self, season: str) -> ScenarioModel:
        with self._lock:
            if season not in self._models:
                catalog = self.catalog()
                if season not in catalog.seasons:
                    raise DataUnavailable("Scenario season is not exported")
                manifest = self._manifest()
                base = manifest["normalization_base"]
                assert isinstance(base, float)
                try:
                    road, best, city_best, population, region_idx = (
                        np.load(self._dir / season / name, mmap_mode="r") for name in FILES[:-1]
                    )
                    point_id = np.load(self._dir / season / FILES[-1])
                except (OSError, ValueError) as error:
                    raise DataUnavailable("Scenario matrices are missing") from error
                if not np.issubdtype(point_id.dtype, np.str_):
                    raise DataUnavailable("Scenario matrices are inconsistent")
                points, markets = road.shape
                if (
                    best.shape != (points, markets)
                    or city_best.shape != (markets, markets)
                    or population.shape != (points,)
                    or region_idx.shape != (points,)
                    or point_id.shape != (points,)
                    or markets != len(catalog.cities)
                ):
                    raise DataUnavailable("Scenario matrices are inconsistent")
                point_index = {str(value): row for row, value in enumerate(point_id)}
                if len(point_index) != points:
                    raise DataUnavailable("Scenario matrices are inconsistent")
                region_ids = region_idx.astype(np.int32)
                if (
                    len(catalog.regions) == 0
                    or region_ids.min() < 0
                    or region_ids.max() >= len(catalog.regions)
                ):
                    raise DataUnavailable("Scenario matrices are inconsistent")
                market_population = np.array(
                    [city.population for city in catalog.cities], dtype=np.float64
                )
                access = point_access(best, market_population)
                weights = population.astype(np.float64)
                self._models[season] = ScenarioModel(
                    season,
                    catalog.model_version,
                    catalog.artifact_version,
                    base,
                    catalog.cities,
                    catalog.regions,
                    road,
                    best,
                    city_best.astype(np.float64),
                    weights,
                    region_ids,
                    point_index,
                    access,
                    population_mean(access, weights, region_ids, len(catalog.regions)),
                    np.bincount(region_ids, weights=weights, minlength=len(catalog.regions)).astype(
                        np.float64
                    ),
                )
            return self._models[season]
