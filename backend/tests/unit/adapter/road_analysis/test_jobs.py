import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from typing import cast

import pytest

from app.adapter.road_analysis.jobs import AnalysisJobs
from app.adapter.road_graph.jobs import RoadJobs
from app.domain.road_analysis import SettlementImpact
from app.repository.files.road_analysis import FileAnalysisStore
from app.usecase.dto import BoundaryShape
from app.usecase.road_analysis import (
    AnalysisDetail,
    AnalysisJob,
    Candidate,
    ImpactLocation,
    VerifiedRoad,
)


class Cache:
    def path(self, region: str, scenario: str) -> Path:
        return Path("fixed-sources")


def wait(job_id: str, engine: AnalysisJobs) -> None:
    deadline = time.monotonic() + 5
    while engine.get(job_id).status in {"running", "queued", "cancelling"}:
        if time.monotonic() > deadline:
            pytest.fail("Background worker did not finish")
        time.sleep(0.01)


def engine_for(tmp_path: Path) -> tuple[AnalysisJobs, ThreadPoolExecutor]:
    pool = ThreadPoolExecutor(max_workers=1)
    roads = cast(
        RoadJobs,
        SimpleNamespace(
            pool=pool,
            cache=Cache(),
            delta=SimpleNamespace(base=None),
            data=SimpleNamespace(region_name=lambda _: "Region"),
        ),
    )
    engine = AnalysisJobs(roads, FileAnalysisStore(tmp_path))
    return engine, pool


def boundary() -> BoundaryShape:
    return BoundaryShape("1", "Region", (0.0, 0.0, 1.0, 1.0), [])


def test_batch_continue_restart_and_detail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine, pool = engine_for(tmp_path)
    candidates = [Candidate(i, str(i), 1.0, float(i), 0.0, False) for i in range(12)]
    monkeypatch.setattr(engine.screening, "candidates", lambda *_: candidates)
    monkeypatch.setattr(engine.evaluation, "baseline", lambda _: ())

    def evaluate(job: object, candidate: Candidate, progress: object) -> AnalysisDetail:
        result = VerifiedRoad(candidate, 100.0, 101.0, 1.0, 10, 0, 0.1)
        return AnalysisDetail(
            result,
            [],
            [
                ImpactLocation(
                    SettlementImpact("a", 10, 100.0, 101.0, 1.0, False, True), "A", 0.0, 0.0
                )
            ],
        )

    monkeypatch.setattr(engine.evaluation, "evaluate", evaluate)
    job = engine.submit(boundary(), "improvement", 20)
    wait(job.id, engine)
    assert len(engine.get(job.id).results) == 10
    assert engine.get(job.id).status == "paused"
    assert engine.detail(job.id, 0).settlements[0].impact.delta == 1
    assert engine.submit(boundary(), "improvement", 20).id == job.id
    engine.resume(job.id)
    wait(job.id, engine)
    assert len(engine.get(job.id).results) == 12
    assert engine.get(job.id).status == "completed"
    pool.shutdown()
    restored, pool2 = engine_for(tmp_path)
    assert len(restored.get(job.id).results) == 12
    pool2.shutdown()


def test_cancel_keeps_finished_results_and_retries_unfinished(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, pool = engine_for(tmp_path)
    started = Event()
    candidates = [Candidate(i, str(i), 1.0, 0.0, 0.0, False) for i in range(2)]
    monkeypatch.setattr(engine.screening, "candidates", lambda *_: candidates)
    monkeypatch.setattr(engine.evaluation, "baseline", lambda _: ())

    def evaluate(job: object, candidate: Candidate, progress: object) -> AnalysisDetail:
        if candidate.way_id == 1:
            started.set()
            while not engine.stops[next(iter(engine.jobs))].is_set():
                time.sleep(0.01)
            raise InterruptedError()
        return AnalysisDetail(VerifiedRoad(candidate, 100.0, 101.0, 1.0, 10, 0, 0.1), [], [])

    monkeypatch.setattr(engine.evaluation, "evaluate", evaluate)
    job = engine.submit(boundary(), "improvement", 20)
    assert started.wait(3)
    engine.cancel(job.id)
    wait(job.id, engine)
    assert engine.get(job.id).status == "cancelled"
    assert len(engine.get(job.id).results) == 1
    pool.shutdown()


def test_restart_marks_running_interrupted_and_source_change_blocks_continue(
    tmp_path: Path,
) -> None:
    engine, pool = engine_for(tmp_path)

    job = AnalysisJob(
        "safe-id", "1", "Region", "criticality", 0, engine.fingerprint(boundary()), status="running"
    )
    engine.store.save(job, boundary())
    restored, pool2 = engine_for(tmp_path)
    assert restored.get(job.id).status == "interrupted"
    restored.jobs[job.id] = replace(restored.jobs[job.id], compatible=False)
    with pytest.raises(Exception, match="sources have changed"):
        restored.resume(job.id)
    pool.shutdown()
    pool2.shutdown()


def test_failed_candidate_does_not_erase_other_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, pool = engine_for(tmp_path)
    monkeypatch.setattr(
        engine.screening,
        "candidates",
        lambda *_: [Candidate(i, str(i), 1.0, 0.0, 0.0, False) for i in range(3)],
    )
    monkeypatch.setattr(engine.evaluation, "baseline", lambda _: ())

    def evaluate(job: object, candidate: Candidate, progress: object) -> AnalysisDetail:
        if candidate.way_id == 1:
            raise ValueError("invalid candidate")
        return AnalysisDetail(VerifiedRoad(candidate, 100.0, 101.0, 1.0, 10, 0, 0.1), [], [])

    monkeypatch.setattr(engine.evaluation, "evaluate", evaluate)
    job = engine.submit(boundary(), "improvement", 20)
    wait(job.id, engine)
    assert [r.candidate.way_id for r in engine.get(job.id).results] == [0, 2]
    assert engine.get(job.id).failures[0].way_id == 1
    pool.shutdown()


def test_baseline_mismatch_never_publishes_rankings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, pool = engine_for(tmp_path)

    def baseline(region: str) -> None:
        raise ValueError("baseline_mismatch")

    monkeypatch.setattr(engine.evaluation, "baseline", baseline)
    job = engine.submit(boundary(), "criticality", 0)
    wait(job.id, engine)
    assert engine.get(job.id).error == "baseline_mismatch"
    assert not engine.get(job.id).results
    pool.shutdown()


def test_queued_cancel_does_not_wait_for_manual_worker(tmp_path: Path) -> None:
    engine, pool = engine_for(tmp_path)
    release = Event()
    pool.submit(release.wait)
    job = engine.submit(boundary(), "improvement", 20)
    assert engine.get(job.id).status == "queued"
    assert engine.cancel(job.id).status == "cancelled"
    release.set()
    pool.shutdown()
    assert engine.get(job.id).status == "cancelled"
