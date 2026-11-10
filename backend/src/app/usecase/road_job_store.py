from typing import Protocol

from app.usecase.road_graph import RoadJob


class RoadJobStore(Protocol):
    def load(self) -> dict[str, RoadJob]: ...
    def save(self, job: RoadJob) -> None: ...
