from fastapi import APIRouter

from app.controller.errors import ErrorResponse
from app.domain.transport import NetworkMode, Season
from app.usecase.sensitivity import AccessibilitySensitivity, SensitivityResult


def build_sensitivity_router(sensitivity: AccessibilitySensitivity) -> APIRouter:
    router = APIRouter(tags=["scenarios"], responses={
        404: {"model": ErrorResponse}, 503: {"model": ErrorResponse},
    })

    @router.get("/regions/{region_id}/sensitivity", response_model=SensitivityResult)
    def evaluate(
        region_id: str, season: Season = Season.SUMMER, network_mode: NetworkMode = NetworkMode.ROAD
    ) -> SensitivityResult:
        return sensitivity.evaluate(region_id, season, network_mode)

    return router
