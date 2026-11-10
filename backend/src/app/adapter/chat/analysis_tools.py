import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError
from app.usecase.road_analysis import AnalysisMode, RoadAnalysis


class AnalysisTools:
    def __init__(self, analysis: RoadAnalysis) -> None:
        self.analysis = analysis

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Start automatic regional road analysis. criticality checks closures with separate accessibility loss and newly isolated population rankings; improvement checks individual ways at the same speed increase percent (default20). BASE snapshot network including existing trunk rail/air. Ten candidates per batch, exact checks may take minutes each. Return job ID and map URL /map?analysis=ID. Never busy-poll or invent results. Ranking is best among checked roads, not global optimum or financial return.",
        )(self.start_road_analysis)
        agent.tool(
            sequential=True,
            description="Read saved road analysis progress and verified results; heuristics are candidates only. Do not treat affected population as measured traffic.",
        )(self.read_road_analysis)
        agent.tool(
            sequential=True,
            description="Continue another batch of ten road candidates, or cancel an analysis, only when the user requests this action.",
        )(self.control_road_analysis)

    def start_road_analysis(
        self, ctx: RunContext[ChatRun], region_id: str, mode: AnalysisMode, percent: int = 20
    ) -> str:
        try:
            job = self.analysis.submit(region_id, mode, percent)
            return json.dumps(
                {"analysis": asdict(job), "url": f"/map?analysis={job.id}&analysis_mode={job.mode}&region={job.region_id}"}, ensure_ascii=False
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def read_road_analysis(self, ctx: RunContext[ChatRun], analysis_id: str) -> str:
        try:
            return json.dumps(asdict(self.analysis.get(analysis_id)), ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def control_road_analysis(self, ctx: RunContext[ChatRun], analysis_id: str, action: str) -> str:
        if action not in {"continue", "cancel"}:
            raise ModelRetry("Choose continue or cancel")
        try:
            job = (
                self.analysis.resume(analysis_id)
                if action == "continue"
                else self.analysis.cancel(analysis_id)
            )
            return json.dumps(asdict(job), ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error
