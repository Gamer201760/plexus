import hashlib
import json
from concurrent.futures import Future
from dataclasses import asdict, replace
from threading import Event, RLock
from time import monotonic
from uuid import uuid4

from app.adapter.log.stdlib import StdlibLogger
from app.adapter.road_analysis.evaluation import RoadEvaluation
from app.adapter.road_analysis.screening import CandidateScreening
from app.adapter.road_graph.jobs import RoadJobs
from app.domain.errors import InvalidQuery
from app.usecase.dto.atlas import BoundaryShape
from app.usecase.dto.road_analysis import AnalysisDetail, AnalysisFailure, AnalysisJob, AnalysisMode
from app.usecase.interface.road_analysis import AnalysisStore


class AnalysisJobs:
    def __init__(self, roads: RoadJobs, store: AnalysisStore) -> None:
        self.roads, self.store = roads, store
        self.screening = CandidateScreening(roads.delta.base)
        self.evaluation = RoadEvaluation(roads)
        self.lock = RLock()
        self.jobs: dict[str, AnalysisJob] = {}
        self.boundaries: dict[str, BoundaryShape] = {}
        self.stops: dict[str, Event] = {}
        self.futures: dict[str, Future[None]] = {}
        for job, boundary in store.load():
            compatible = job.fingerprint == self.fingerprint(boundary)
            status = (
                "interrupted" if job.status in {"queued", "running", "cancelling"} else job.status
            )
            self.jobs[job.id] = replace(job, status=status, compatible=compatible)
            self.boundaries[job.id] = boundary
            self.stops[job.id] = Event()

    def fingerprint(self, boundary: BoundaryShape) -> str:
        source = self.roads.cache.key(boundary.id, "analysis-v1")
        return hashlib.sha256(
            (source + json.dumps(asdict(boundary), sort_keys=True)).encode()
        ).hexdigest()

    def view(self, job: AnalysisJob) -> AnalysisJob:
        checked = len(job.results) + len(job.failures)
        return replace(job, candidates=job.candidates[checked : job.batch_target])

    def get(self, analysis_id: str) -> AnalysisJob:
        with self.lock:
            if analysis_id not in self.jobs:
                raise InvalidQuery("Unknown analysis")
            return self.view(self.jobs[analysis_id])

    def recent(self) -> list[AnalysisJob]:
        with self.lock:
            return [self.view(j) for j in reversed(list(self.jobs.values()))][:100]

    def submit(self, boundary: BoundaryShape, mode: AnalysisMode, percent: int) -> AnalysisJob:
        fingerprint = self.fingerprint(boundary)
        with self.lock:
            for job in self.jobs.values():
                if (job.region_id, job.mode, job.percent, job.fingerprint) == (
                    boundary.id,
                    mode,
                    percent,
                    fingerprint,
                ):
                    return self.view(job)
            job = AnalysisJob(uuid4().hex, boundary.id, boundary.name, mode, percent, fingerprint)
            self.jobs[job.id], self.boundaries[job.id], self.stops[job.id] = job, boundary, Event()
            self.store.save(job, boundary)
            self.futures[job.id] = self.roads.pool.submit(self.run, job.id)
            return self.view(job)

    def resume(self, analysis_id: str) -> AnalysisJob:
        with self.lock:
            self.get(analysis_id)
            job = self.jobs[analysis_id]
            if not job.compatible or job.fingerprint != self.fingerprint(
                self.boundaries[analysis_id]
            ):
                raise InvalidQuery("Analysis sources have changed")
            if job.status in {"queued", "running", "cancelling"}:
                return self.view(job)
            if job.error == "baseline_mismatch":
                raise InvalidQuery("Baseline mismatch requires correction")
            checked = len(job.results) + len(job.failures)
            if job.stage == "complete" and checked >= job.candidate_count:
                return self.view(job)
            target = job.batch_target if checked < job.batch_target else checked + 10
            job = replace(job, status="queued", batch_target=target, error=None)
            self.jobs[analysis_id] = job
            self.stops[analysis_id].clear()
            self.store.save(job, self.boundaries[analysis_id])
            self.futures[analysis_id] = self.roads.pool.submit(self.run, analysis_id)
            return self.view(job)

    def cancel(self, analysis_id: str) -> AnalysisJob:
        with self.lock:
            job = self.get(analysis_id)
            if job.status in {"queued", "running"}:
                self.stops[analysis_id].set()
                future = self.futures.get(analysis_id)
                if future is not None and future.cancel():
                    self.checkpoint(replace(self.jobs[analysis_id], status="cancelled"))
                    return self.get(analysis_id)
                self.jobs[analysis_id] = replace(self.jobs[analysis_id], status="cancelling")
                self.store.save(self.jobs[analysis_id], self.boundaries[analysis_id])
            return self.get(analysis_id)

    def detail(self, analysis_id: str, way_id: int) -> AnalysisDetail:
        job = self.get(analysis_id)
        if not any(r.candidate.way_id == way_id for r in job.results):
            raise InvalidQuery("Road has no verified result in this analysis")
        return self.store.detail(analysis_id, way_id)

    def progress(self, analysis_id: str, stage: str, completed: int, total: int) -> None:
        if self.stops[analysis_id].is_set():
            raise InterruptedError()
        with self.lock:
            self.jobs[analysis_id] = replace(
                self.jobs[analysis_id],
                status="running",
                stage=stage,
                completed=completed,
                total=total,
            )

    def checkpoint(self, job: AnalysisJob) -> None:
        with self.lock:
            self.jobs[job.id] = job
            self.store.save(job, self.boundaries[job.id])

    def run(self, analysis_id: str) -> None:
        started = monotonic()
        elapsed = self.jobs[analysis_id].elapsed_seconds
        try:
            self.progress(analysis_id, "preparing", 0, 1)
            job = self.jobs[analysis_id]
            if job.fingerprint != self.fingerprint(self.boundaries[analysis_id]):
                raise ValueError("sources_changed")
            self.evaluation.baseline(self.roads.data.region_name(job.region_id))
            if not job.candidates:
                candidates = self.screening.candidates(
                    self.boundaries[analysis_id],
                    job.mode,
                    lambda stage, done, total: self.progress(analysis_id, stage, done, total),
                )
                self.checkpoint(
                    replace(
                        self.jobs[analysis_id],
                        candidates=candidates,
                        candidate_count=len(candidates),
                    )
                )
            job = self.jobs[analysis_id]
            checked = len(job.results) + len(job.failures)
            for candidate in job.candidates[checked : job.batch_target]:
                self.progress(analysis_id, "verifying", 0, 180)
                self.checkpoint(replace(self.jobs[analysis_id], current_way_id=candidate.way_id))
                try:
                    detail = self.evaluation.evaluate(
                        self.jobs[analysis_id],
                        candidate,
                        lambda done: self.progress(analysis_id, "verifying", done, 180),
                    )
                    self.store.save_detail(analysis_id, detail)
                    job = self.jobs[analysis_id]
                    self.checkpoint(replace(job, results=[*job.results, detail.result]))
                except InterruptedError:
                    raise
                except Exception as error:
                    if "baseline_mismatch" in str(error):
                        raise
                    StdlibLogger("road_analysis").error(
                        "candidate_failed", exc=error, way_id=candidate.way_id
                    )
                    job = self.jobs[analysis_id]
                    self.checkpoint(
                        replace(
                            job,
                            failures=[
                                *job.failures,
                                AnalysisFailure(candidate.way_id, "calculation_failed"),
                            ],
                        )
                    )
            job = self.jobs[analysis_id]
            finished = len(job.results) + len(job.failures) >= job.candidate_count
            self.checkpoint(
                replace(
                    job,
                    status="completed" if finished else "paused",
                    stage="complete" if finished else "batch_complete",
                    current_way_id=None,
                )
            )
        except InterruptedError:
            self.checkpoint(
                replace(self.jobs[analysis_id], status="cancelled", current_way_id=None)
            )
        except Exception as error:  # noqa: BLE001 - worker boundary persists failure and logs cause
            StdlibLogger("road_analysis").error(
                "analysis_failed", exc=error, analysis_id=analysis_id
            )
            code = (
                "baseline_mismatch" if "baseline_mismatch" in str(error) else "calculation_failed"
            )
            self.checkpoint(
                replace(self.jobs[analysis_id], status="failed", error=code, current_way_id=None)
            )
        finally:
            self.checkpoint(
                replace(self.jobs[analysis_id], elapsed_seconds=elapsed + monotonic() - started)
            )

    def close(self) -> None:
        for stop in self.stops.values():
            stop.set()
