from typing import Protocol

from app.usecase.dto.road_corridor import RoadCorridor
from app.usecase.dto.road_graph import RoadJob


class CorridorPort(Protocol):
    def get(self, corridor_id: str) -> RoadCorridor: ...
    def resolve(self, road_name: str, origin: str, destination: str) -> RoadCorridor: ...
    def close(self, corridor_id: str) -> list[RoadJob]: ...
