from threading import Event, Lock
from unittest.mock import Mock

from app.adapter.road_graph.jobs import RoadJobs
from app.domain.errors import DataUnavailable
from app.usecase.dto.road_graph import RoadJob


def test_completed_calculation_survives_storage_timeout() -> None:
    job = RoadJob("job", "region", "Region", "road", [], "running", 180, 360, "test")
    engine = RoadJobs.__new__(RoadJobs)
    engine.lock = Lock()
    engine.jobs = {job.id: job}
    engine.stops = {job.id: Event()}
    engine.data = Mock()
    engine.data.region_name.return_value = "Region"
    engine.cache = Mock()
    engine.cache.read.return_value = 100.0
    engine.baselines = {}
    engine.routing = Mock()
    engine.routing.calculate.return_value = (99.0, 1000, 20, 190, 10.0)
    engine.store = Mock()
    engine.store.save.side_effect = DataUnavailable("Calculation storage is unavailable")

    engine.run(job)

    completed = engine.job(job.id)
    assert completed.status == "completed"
    assert completed.result is not None
    assert completed.result.after == 99.0
    assert completed.error == "storage_pending"
