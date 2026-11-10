from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Event, Lock
from time import monotonic
from uuid import uuid4

from app.adapter.log.stdlib import StdlibLogger
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta import DeltaCalculation
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.routing import GraphRouting
from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.road_economics import MoneyAssumptions
from app.usecase.dto.road_graph import (
    GraphLocation,
    RoadAddition,
    RoadChange,
    RoadJob,
    RoadResult,
    RoadView,
)
from app.usecase.interface.graph_snapshot import GraphSnapshot
from app.usecase.interface.road_graph import (
    BaselineStore,
    DeltaRegionStore,
    GraphMatrixStore,
    RoadJobStore,
)


class RoadJobs:
    def __init__(
        self,
        snapshot: GraphSnapshot,
        store: RoadJobStore,
        baselines: BaselineStore,
        deltas: DeltaRegionStore,
        matrix: GraphMatrixStore,
    ) -> None:
        self.data = GraphData(snapshot)
        self.routing = GraphRouting(self.data)
        self.cache = baselines
        self.delta = DeltaCalculation(DeltaBase(self.data, deltas, matrix))
        self.delta.base.prepare()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="road-calculation")
        self.lock = Lock()
        self.store = store
        self.jobs = {
            key: replace(job, status="cancelled") if job.status in {"queued", "running"} else job
            for key, job in store.load().items()
        }
        self.stops = {key: Event() for key in self.jobs}
        self.baselines: dict[tuple[str, str], float] = {}

    def locations(self, query: str, region_id: str | None) -> list[GraphLocation]:
        return self.data.locations(query, region_id)

    def view(self, bounds: tuple[float, float, float, float], zoom: float) -> RoadView:
        return self.data.view(bounds, zoom)

    def submit(
        self,
        region_id: str,
        region: str,
        scenario: str,
        changes: list[RoadChange],
        *,
        queue: bool = False,
    ) -> RoadJob:
        self.data.region_name(region_id)
        self.data.indices_for([c.way_id for c in changes])
        with self.lock:
            for job in self.jobs.values():
                if job.status in {"queued", "running"}:
                    if (job.region_id, job.scenario, job.changes) == (region_id, scenario, changes):
                        return job
                    if not queue:
                        raise InvalidQuery("A calculation is already running; wait or cancel it")
            job = RoadJob(
                uuid4().hex, region_id, region, scenario, changes, "queued", 0, 360, self.data.version
            )
            self.store.save(job)
            self.jobs[job.id] = job
            self.stops[job.id] = Event()
        self.pool.submit(self.run, job)
        return job

    def submit_addition(
        self, region_id: str, region: str, addition: RoadAddition, money: MoneyAssumptions | None
    ) -> RoadJob:
        self.data.region_name(region_id)
        self.data.load()
        nodes = (addition.source_node, addition.target_node)
        if any(node >= len(self.data.nodes["lat"]) for node in nodes):
            raise InvalidQuery("Unknown graph node")
        addition = replace(
            addition,
            coordinates=[
                [float(self.data.nodes["lon"][node]), float(self.data.nodes["lat"][node])]
                for node in nodes
            ],
        )
        with self.lock:
            for existing in self.jobs.values():
                if existing.status in {"queued", "running"}:
                    if (existing.region_id, existing.addition, existing.money_assumptions) == (
                        region_id,
                        addition,
                        money,
                    ):
                        return existing
                    raise InvalidQuery("A calculation is already running; wait or cancel it")
            job = RoadJob(
                uuid4().hex,
                region_id,
                region,
                "road",
                [],
                "queued",
                0,
                5,
                self.data.version,
                addition=addition,
                money_assumptions=money,
            )
            self.store.save(job)
            self.jobs[job.id] = job
            self.stops[job.id] = Event()
        self.pool.submit(self.run, job)
        return job

    def recent(self) -> list[RoadJob]:
        with self.lock:
            return list(reversed(list(self.jobs.values())))[:20]

    def job(self, job_id: str) -> RoadJob:
        with self.lock:
            if job_id not in self.jobs:
                raise InvalidQuery("Unknown calculation")
            return self.jobs[job_id]

    def cancel(self, job_id: str) -> RoadJob:
        self.job(job_id)
        self.stops[job_id].set()
        return self.job(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: str,
        completed: int,
        result: RoadResult | None = None,
        error: str | None = None,
    ) -> None:
        with self.lock:
            self.jobs[job_id] = replace(
                self.jobs[job_id], status=status, completed=completed, result=result, error=error
            )
            if status in {"completed", "cancelled", "failed"}:
                try:
                    self.store.save(self.jobs[job_id])
                except DataUnavailable as storage_error:
                    self.jobs[job_id] = replace(self.jobs[job_id], error=error or "storage_pending")
                    StdlibLogger("road_graph").error(
                        "calculation_storage_failed", exc=storage_error, job_id=job_id
                    )

    def run(self, job: RoadJob) -> None:
        started = monotonic()
        offset = 0

        def progress(value: int) -> None:
            if self.stops[job.id].is_set():
                raise InterruptedError()
            self.update(job.id, status="running", completed=offset + value)

        try:
            progress(0)
            region = self.data.region_name(job.region_id)
            if job.addition:
                result = self.delta.calculate(region, job.addition, job.money_assumptions, progress)
                self.update(job.id, status="completed", completed=5, result=result)
                return
            key = (region, job.scenario)
            cached = self.cache.read(*key)
            if cached is not None:
                self.baselines[key] = cached
            if key not in self.baselines:
                before, _, _, _, _ = self.routing.calculate(region, job.scenario, [], progress)
                rows = self.data.read("expected", {"region": region, "season": job.scenario})
                if not rows:
                    raise InvalidQuery("Region is missing from the calculation snapshot")
                expected = float(rows[0][0])
                if abs(before - expected) > max(0.0001, abs(expected) * 0.00001):
                    self.update(job.id, status="failed", completed=180, error="baseline_mismatch")
                    return
                self.baselines[key] = before
                self.cache.write(*key, before)
            offset = 180
            progress(0)
            before = self.baselines[key]
            after, population, settlements, changed, norm = self.routing.calculate(
                region, job.scenario, job.changes, progress
            )
            result = RoadResult(
                before,
                after,
                after - before,
                (after / before - 1) * 100 if before else None,
                population,
                settlements,
                changed,
                norm,
                monotonic() - started,
            )
            self.update(job.id, status="completed", completed=360, result=result)
        except InterruptedError:
            self.update(job.id, status="cancelled", completed=self.job(job.id).completed)
        except Exception as error:  # noqa: BLE001 - worker boundary records failure and logs the cause
            StdlibLogger("road_graph").error("calculation_failed", exc=error, job_id=job.id)
            self.update(
                job.id,
                status="failed",
                completed=self.job(job.id).completed,
                error="baseline_mismatch"
                if str(error) == "baseline_mismatch"
                else "calculation_failed",
            )

    def close(self) -> None:
        for stop in self.stops.values():
            stop.set()
        self.pool.shutdown(wait=False, cancel_futures=True)
