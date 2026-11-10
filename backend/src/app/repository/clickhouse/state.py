from dataclasses import dataclass
from time import time_ns

from app.domain.errors import InvalidQuery
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.records import columns, decode, encode
from app.repository.clickhouse.writer import ClickHouseWriter
from app.usecase.dto import BoundaryShape
from app.usecase.road_analysis import AnalysisDetail, AnalysisJob
from app.usecase.road_graph import RoadJob


@dataclass(frozen=True)
class AnalysisState:
    id: str
    job: AnalysisJob
    boundary: BoundaryShape


@dataclass(frozen=True)
class AnalysisResult:
    analysis_id: str
    way_id: int
    detail: AnalysisDetail


class ClickHouseRoadJobStore:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        self.writer = ClickHouseWriter(reader)

    def load(self) -> dict[str, RoadJob]:
        rows = self.reader.rows(
            "SELECT "
            + columns(RoadJob)
            + " FROM plexus_state.road_jobs FINAL ORDER BY updated DESC LIMIT 100",
            {},
        )
        jobs: list[RoadJob] = [decode(RoadJob, row) for row in reversed(rows)]
        return {job.id: job for job in jobs}

    def save(self, job: RoadJob) -> None:
        self.writer.insert("road_jobs", {**encode(RoadJob, job), "updated": time_ns()})


class ClickHouseAnalysisStore:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        self.writer = ClickHouseWriter(reader)

    def load(self) -> list[tuple[AnalysisJob, BoundaryShape]]:
        rows = self.reader.rows(
            "SELECT "
            + columns(AnalysisState)
            + " FROM plexus_state.analysis_jobs FINAL ORDER BY updated",
            {},
        )
        states: list[AnalysisState] = [decode(AnalysisState, row) for row in rows]
        return [(s.job, s.boundary) for s in states]

    def save(self, job: AnalysisJob, boundary: BoundaryShape) -> None:
        state = AnalysisState(job.id, job, boundary)
        self.writer.insert("analysis_jobs", {**encode(AnalysisState, state), "updated": time_ns()})

    def save_detail(self, analysis_id: str, detail: AnalysisDetail) -> None:
        value = AnalysisResult(analysis_id, detail.result.candidate.way_id, detail)
        self.writer.insert(
            "analysis_details", {**encode(AnalysisResult, value), "updated": time_ns()}
        )

    def detail(self, analysis_id: str, way_id: int) -> AnalysisDetail:
        rows = self.reader.rows(
            "SELECT detail FROM plexus_state.analysis_details FINAL WHERE analysis_id={id:String} AND way_id={way:Int64}",
            {"id": analysis_id, "way": way_id},
        )
        if not rows:
            raise InvalidQuery("Verified result is unavailable")
        value: AnalysisDetail = decode(AnalysisDetail, rows[0]["detail"])
        return value
