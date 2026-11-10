from dataclasses import dataclass


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
