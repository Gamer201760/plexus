from dataclasses import dataclass
from typing import Protocol

from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.road_graph import RoadJob


@dataclass(frozen=True)
class CorridorRegion:
    id: str
    name: str


@dataclass(frozen=True)
class RoadCorridor:
    id: str
    road_ref: str
    origin: str
    destination: str
    way_ids: list[int]
    length_km: float
    origin_attachment_km: float
    destination_attachment_km: float
    regions: list[CorridorRegion]
    lines: list[list[list[float]]]
    scope: str = "whole_osm_ways_on_named_road_corridor_both_directions"


@dataclass(frozen=True)
class CorridorCalculation:
    corridor: RoadCorridor
    job_ids: list[str]


class CorridorPort(Protocol):
    def get(self, corridor_id: str) -> RoadCorridor: ...
    def resolve(self, road_name: str, origin: str, destination: str) -> RoadCorridor: ...
    def close(self, corridor_id: str) -> list[RoadJob]: ...


class RoadCorridors:
    def __init__(self, engine: CorridorPort | None) -> None:
        self.engine = engine

    def resolve(self, road_name: str, origin: str, destination: str) -> RoadCorridor:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        if any(not 2 <= len(s.strip()) <= 100 for s in (road_name, origin, destination)):
            raise InvalidQuery("Specify road name and two settlements")
        return self.engine.resolve(road_name.strip(), origin.strip(), destination.strip())

    def get(self, corridor_id: str) -> RoadCorridor:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self.engine.get(corridor_id)

    def close(self, corridor_id: str) -> list[RoadJob]:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self.engine.close(corridor_id)
