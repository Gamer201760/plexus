from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.controller.road_analysis.schemas import AnalysisResponse
from app.usecase.dto.road_analysis import AnalysisDetail, AnalysisJob, AnalysisMode
from app.usecase.road_analysis import RoadAnalysis


class AnalysisInput(BaseModel):
    region_id: str = Field(min_length=1, max_length=64)
    mode: AnalysisMode
    percent: int = Field(default=20, ge=1, le=200, strict=True)


def build_analysis_router(analysis: RoadAnalysis) -> APIRouter:
    router = APIRouter(prefix="/road-analyses", tags=["road-analysis"])

    @router.post("", response_model=AnalysisResponse)
    def submit(body: AnalysisInput) -> AnalysisJob:
        return analysis.submit(body.region_id, body.mode, body.percent)

    @router.get("", response_model=list[AnalysisResponse])
    def recent() -> list[AnalysisJob]:
        return analysis.recent()

    @router.get("/{analysis_id}", response_model=AnalysisResponse)
    def get(analysis_id: str) -> AnalysisJob:
        return analysis.get(analysis_id)

    @router.post("/{analysis_id}/continue", response_model=AnalysisResponse)
    def resume(analysis_id: str) -> AnalysisJob:
        return analysis.resume(analysis_id)

    @router.post("/{analysis_id}/cancel", response_model=AnalysisResponse)
    def cancel(analysis_id: str) -> AnalysisJob:
        return analysis.cancel(analysis_id)

    @router.get("/{analysis_id}/results/{way_id}", response_model=AnalysisDetail)
    def detail(analysis_id: str, way_id: int) -> AnalysisDetail:
        return analysis.detail(analysis_id, way_id)

    return router
