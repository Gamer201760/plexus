from app.domain.errors import DataUnavailable, InvalidQuery, RegionNotFound
from app.usecase.dto.road_analysis import AnalysisDetail, AnalysisJob, AnalysisMode
from app.usecase.interface.atlas import AtlasRepository
from app.usecase.interface.road_analysis import AnalysisPort


class RoadAnalysis:
    def __init__(self, engine: AnalysisPort | None, atlas: AtlasRepository) -> None:
        self._engine = engine
        self.atlas = atlas

    @property
    def engine(self) -> AnalysisPort:
        if self._engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self._engine

    def submit(self, region_id: str, mode: AnalysisMode, percent: int = 20) -> AnalysisJob:
        if (
            mode not in {"criticality", "improvement"}
            or type(percent) is not int
            or not 1 <= percent <= 200
        ):
            raise InvalidQuery("Invalid analysis mode or improvement percentage")
        if not any(r.id == region_id for r in self.atlas.regions()):
            raise RegionNotFound()
        boundary = next((b for b in self.atlas.boundaries() if b.id == region_id), None)
        if boundary is None:
            raise DataUnavailable("Region boundary is missing")
        return self.engine.submit(boundary, mode, percent if mode == "improvement" else 0)

    def recent(self) -> list[AnalysisJob]:
        return self.engine.recent()

    def get(self, analysis_id: str) -> AnalysisJob:
        return self.engine.get(analysis_id)

    def resume(self, analysis_id: str) -> AnalysisJob:
        return self.engine.resume(analysis_id)

    def cancel(self, analysis_id: str) -> AnalysisJob:
        return self.engine.cancel(analysis_id)

    def detail(self, analysis_id: str, way_id: int) -> AnalysisDetail:
        return self.engine.detail(analysis_id, way_id)


