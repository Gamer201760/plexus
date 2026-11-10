from threading import RLock

import numpy as np

from app.domain.errors import DataUnavailable
from app.domain.market_evaluation import point_access, population_mean
from app.domain.market_scenario import MarketCity, ScenarioCatalog, ScenarioModel, ScenarioRegion
from app.repository.clickhouse.client import ClickHouseReader


class ClickHouseScenarioRepository:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        self.lock = RLock()
        self.models: dict[str, ScenarioModel] = {}
        self.metadata: ScenarioCatalog | None = None
        self.normalization = 0.0

    def catalog(self) -> ScenarioCatalog:
        with self.lock:
            if self.metadata is None:
                rows = self.reader.rows(
                    "SELECT model_version,artifact_version,seasons,normalization_base,assumptions FROM plexus_scenario.catalog",
                    {},
                )
                if len(rows) != 1:
                    raise DataUnavailable("Scenario snapshot is not imported")
                row = rows[0]
                cities = self.reader.rows(
                    "SELECT id,region,population,latitude,longitude,is_capital FROM plexus_scenario.cities ORDER BY ordinal",
                    {},
                )
                regions = self.reader.rows(
                    "SELECT region_id,name FROM plexus_scenario.regions ORDER BY ordinal", {}
                )
                self.normalization = float(row["normalization_base"])
                self.metadata = ScenarioCatalog(
                    row["model_version"],
                    row["artifact_version"],
                    tuple(row["seasons"]),
                    tuple(MarketCity(**c) for c in cities),
                    tuple(ScenarioRegion(**r) for r in regions),
                    tuple(row["assumptions"]),
                )
            return self.metadata

    def model(self, season: str) -> ScenarioModel:
        with self.lock:
            if season in self.models:
                return self.models[season]
            catalog = self.catalog()
            if season not in catalog.seasons:
                raise DataUnavailable("Scenario season is not imported")
            points = self.reader.arrow(
                "SELECT population,region_idx FROM plexus_scenario.points WHERE season={season:String} ORDER BY point_idx",
                {"season": season},
            )
            times = self.reader.arrow(
                "SELECT road_h,best_h FROM plexus_scenario.times WHERE season={season:String} ORDER BY point_idx,city_idx",
                {"season": season},
            )
            city_times = self.reader.arrow(
                "SELECT best_h FROM plexus_scenario.city_times WHERE season={season:String} ORDER BY from_idx,to_idx",
                {"season": season},
            )
            n, m = len(points), len(catalog.cities)
            if not n or len(times) != n * m or len(city_times) != m * m:
                raise DataUnavailable("Scenario matrices are inconsistent")
            road = times["road_h"].to_numpy().astype(np.float32).reshape(n, m)
            best = times["best_h"].to_numpy().astype(np.float32).reshape(n, m)
            city_best = city_times["best_h"].to_numpy().astype(np.float64).reshape(m, m)
            population = points["population"].to_numpy().astype(np.float64)
            region_idx = points["region_idx"].to_numpy().astype(np.int32)
            markets = np.array([c.population for c in catalog.cities], dtype=np.float64)
            access = point_access(best, markets)
            count = len(catalog.regions)
            model = ScenarioModel(
                season,
                catalog.model_version,
                catalog.artifact_version,
                self.normalization,
                catalog.cities,
                catalog.regions,
                road,
                best,
                city_best,
                population,
                region_idx,
                {},
                access,
                population_mean(access, population, region_idx, count),
                np.bincount(region_idx, weights=population, minlength=count).astype(np.float64),
            )
            self.models[season] = model
            return model
