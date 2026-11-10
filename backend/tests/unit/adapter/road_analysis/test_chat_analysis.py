import json
from unittest.mock import Mock

from pydantic_ai import RunContext

from app.adapter.chat.analysis_tools import AnalysisTools
from app.adapter.chat.artifacts import ChatRun
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_analysis import AnalysisJob


def test_start_emits_inline_analysis_instead_of_navigation_url() -> None:
    analysis = Mock()
    job = AnalysisJob("analysis-1", "16", "Tatarstan", "improvement", 20, "snapshot")
    analysis.submit.return_value = job
    run = ChatRun(ChatContext("16", Season.WINTER, NetworkMode.ROAD, "hansen"))
    context = Mock(spec=RunContext)
    context.deps = run

    result = json.loads(AnalysisTools(analysis).start_road_analysis(context, "16", "improvement"))

    assert len(run.pending) == 1
    assert run.pending[0].type == "analysis"
    assert run.pending[0].analysis == job
    assert "url" not in result
    analysis.submit.assert_called_once_with("16", "improvement", 20)
