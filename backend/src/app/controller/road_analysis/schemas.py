from pydantic import BaseModel, ConfigDict

from app.usecase.road_analysis import AnalysisFailure, AnalysisMode, Candidate, VerifiedRoad


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    region_id: str
    region: str
    mode: AnalysisMode
    percent: int
    fingerprint: str
    status: str
    stage: str
    candidates: list[Candidate]
    results: list[VerifiedRoad]
    failures: list[AnalysisFailure]
    candidate_count: int
    batch_target: int
    current_way_id: int | None
    completed: int
    total: int
    elapsed_seconds: float
    error: str | None
    compatible: bool
