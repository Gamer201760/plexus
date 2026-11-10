from unittest.mock import Mock

from pydantic_ai import RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.corridor_tools import CorridorTools
from app.domain.transport import NetworkMode, Season
from app.usecase.dto.chat import ChatContext
from app.usecase.dto.road_corridor import CorridorRegion, RoadCorridor
from app.usecase.dto.road_graph import RoadJob
from app.usecase.road_corridor import RoadCorridors


def test_closure_emits_geometry_and_both_jobs_without_waiting_for_results() -> None:
    corridor = RoadCorridor(
        "corridor", "R-1", "A", "B", [7], 4, 0, 0,
        [CorridorRegion("1", "First"), CorridorRegion("2", "Second")],
        [[[40.0, 44.0], [41.0, 45.0]]],
    )
    engine = Mock()
    engine.get.return_value = corridor
    engine.close.return_value = [
        RoadJob(str(i), str(i), name, "road", [], "queued", 0, 360, "test")
        for i, name in [(1, "First"), (2, "Second")]
    ]
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    context = Mock(spec=RunContext)
    context.deps = run
    pending = run.pending
    tools = CorridorTools(RoadCorridors(engine))
    tools.close_road_corridor(context, "corridor")
    assert len(pending) == 1
    event = pending[0]
    assert event.type == "calculation"
    assert event.calculation is not None
    assert event.calculation.corridor.lines == corridor.lines
    assert event.calculation.job_ids == ["1", "2"]
    engine.close.assert_called_once_with("corridor")
