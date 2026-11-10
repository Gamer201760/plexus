from math import isfinite

from app.domain.errors import DataUnavailable, InvalidQuery, RegionNotFound
from app.domain.road_economics import MoneyAssumptions
from app.usecase.dto.road_graph import GraphLocation, RoadAddition, RoadChange, RoadJob, RoadView
from app.usecase.interface.atlas import AtlasRepository
from app.usecase.interface.road_graph import RoadGraphPort, RoadViewSource


class RoadGraph:
    def __init__(
        self,
        engine: RoadGraphPort | None,
        atlas: AtlasRepository,
        view_source: RoadViewSource | None = None,
    ) -> None:
        self._engine = engine
        self.atlas = atlas
        self.view_source = view_source

    @property
    def engine(self) -> RoadGraphPort:
        if self._engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self._engine

    def locations(self, query: str, region_id: str | None = None) -> list[GraphLocation]:
        if not 2 <= len(query.strip()) <= 100:
            raise InvalidQuery("Place query must contain between 2 and 100 characters")
        return self.engine.locations(query.strip(), region_id)

    def recent(self) -> list[RoadJob]:
        return self.engine.recent()

    def view(self, west: float, south: float, east: float, north: float, zoom: float) -> RoadView:
        if not all(isfinite(v) for v in (west, south, east, north, zoom)):
            raise InvalidQuery()
        if not (-180 <= west < east <= 180 and -85 <= south < north <= 85 and 0 <= zoom <= 22):
            raise InvalidQuery()
        source = self.view_source if self.view_source is not None else self.engine
        return source.view((west, south, east, north), zoom)

    def submit(self, region_id: str, scenario: str, changes: list[RoadChange]) -> RoadJob:
        if scenario not in {"road", "summer", "winter"} or not 1 <= len(changes) <= 50:
            raise InvalidQuery()
        if len({c.way_id for c in changes}) != len(changes):
            raise InvalidQuery("Duplicate road identifiers")
        if any(
            c.way_id < 0 or not isfinite(c.speed_factor) or not 0 <= c.speed_factor <= 3
            for c in changes
        ):
            raise InvalidQuery("Speed factor must be between 0 (closure) and 3")
        region = next((r for r in self.atlas.regions() if r.id == region_id), None)
        if region is None:
            raise RegionNotFound()
        return self.engine.submit(region_id, region.name, scenario, changes)

    def add_connection(
        self, region_id: str, addition: RoadAddition, money: MoneyAssumptions | None = None
    ) -> RoadJob:
        if (
            addition.source_node < 0
            or addition.target_node < 0
            or addition.source_node == addition.target_node
            or not isfinite(addition.travel_hours)
            or not 0 < addition.travel_hours <= 72
        ):
            raise InvalidQuery("Specify two distinct graph nodes and a travel time in (0,72] hours")
        if money and any(
            not isfinite(v) or v < 0
            for v in (
                money.trips_per_year,
                money.rub_per_hour,
                money.capital_cost_rub,
                money.annual_operating_cost_rub,
            )
        ):
            raise InvalidQuery("Economic assumptions must be finite and nonnegative")
        region = next((r for r in self.atlas.regions() if r.id == region_id), None)
        if region is None:
            raise RegionNotFound()
        return self.engine.submit_addition(region_id, region.name, addition, money)

    def job(self, job_id: str) -> RoadJob:
        return self.engine.job(job_id)

    def cancel(self, job_id: str) -> RoadJob:
        return self.engine.cancel(job_id)
