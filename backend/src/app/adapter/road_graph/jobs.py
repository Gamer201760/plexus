from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event, Lock
from time import monotonic
from uuid import uuid4

from app.adapter.log.stdlib import StdlibLogger
from app.adapter.road_graph.baselines import BaselineCache
from app.adapter.road_graph.data import VERSION, GraphData
from app.adapter.road_graph.delta import DeltaCalculation
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.job_store import restore_jobs, save_job
from app.adapter.road_graph.routing import GraphRouting
from app.domain.errors import InvalidQuery
from app.domain.road_economics import MoneyAssumptions
from app.usecase.road_graph import (
    GraphLocation,
    RoadAddition,
    RoadChange,
    RoadJob,
    RoadResult,
    RoadView,
)


class RoadJobs:
    def __init__(self, root: Path) -> None:
        self.data = GraphData(root)
        self.routing = GraphRouting(self.data)
        self.cache = BaselineCache(root)
        self.delta = DeltaCalculation(DeltaBase(self.data))
        self.delta.base.prepare()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="road-calculation")
        self.lock = Lock()
        self.jobs = restore_jobs(root)
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
                uuid4().hex, region_id, region, scenario, changes, "queued", 0, 360, VERSION
            )
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
                VERSION,
                addition=addition,
                money_assumptions=money,
            )
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
                save_job(self.data.root, self.job(job.id))
                return
            key = (region, job.scenario)
            cached = self.cache.read(*key)
            if cached is not None:
                self.baselines[key] = cached
            if key not in self.baselines:
                before, _, _, _, _ = self.routing.calculate(region, job.scenario, [], progress)
                with self.data.connect() as con:
                    expected_row = con.execute(
                        "select hansen_idx from idx_region where region=? and season=?", list(key)
                    ).fetchone()
                    if expected_row is None:
                        raise InvalidQuery("Region is missing from the calculation snapshot")
                    expected = float(expected_row[0])
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
            save_job(self.data.root, self.job(job.id))
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
