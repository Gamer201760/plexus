from fastapi import APIRouter

from app.controller.errors import ErrorResponse
from app.controller.scenarios.schemas import (
    ScenarioCatalogResponse,
    ScenarioEvaluationRequest,
    ScenarioEvaluationResponse,
)
from app.domain.market_scenario import NewTrunkLink
from app.usecase.scenarios import ScenarioQueries


def build_scenarios_router(queries: ScenarioQueries) -> APIRouter:
    router = APIRouter(
        tags=["scenarios"],
        responses={
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )

    @router.get("/scenarios")
    def get_catalog() -> ScenarioCatalogResponse:
        return ScenarioCatalogResponse.model_validate(queries.catalog())

    @router.post("/scenarios/evaluate", responses={409: {"model": ErrorResponse}})
    def evaluate_scenario(request: ScenarioEvaluationRequest) -> ScenarioEvaluationResponse:
        result = queries.evaluate(
            request.season,
            request.model_version,
            request.artifact_version,
            tuple(
                NewTrunkLink(
                    link.from_city,
                    link.to_city,
                    link.mode,
                    link.travel_h,
                    link.frequency_per_week,
                )
                for link in request.links
            ),
        )
        return ScenarioEvaluationResponse.model_validate(result)

    return router
