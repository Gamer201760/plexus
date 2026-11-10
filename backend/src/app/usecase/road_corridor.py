from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.dto.road_corridor import RoadCorridor
from app.usecase.dto.road_graph import RoadJob
from app.usecase.interface.road_corridor import CorridorPort


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
