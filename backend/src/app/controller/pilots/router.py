from dataclasses import asdict

from fastapi import APIRouter

from app.controller.errors import ErrorResponse
from app.controller.pilots.schemas import (
    EdgeResponse,
    EvaluationRequest,
    EvaluationResponse,
    PairResponse,
    PilotResponse,
    PilotSummaryResponse,
    PointResponse,
)
from app.domain.pilot import EdgeChange, NewLink
from app.domain.pilot_routing import SCHEDULED_MODES
from app.usecase.pilots import PilotQueries


def build_pilots_router(queries: PilotQueries) -> APIRouter:
    router = APIRouter(
        tags=["pilots"],
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )

    @router.get("/pilots")
    def list_pilots() -> tuple[PilotSummaryResponse, ...]:
        return tuple(
            PilotSummaryResponse(
                id=pilot.id,
                name=pilot.name,
                model_version=pilot.model_version,
                artifact_version=pilot.artifact_version,
                point_count=len(pilot.points),
                edge_count=len(pilot.edges),
                pair_count=len(pilot.pairs),
                unknown_frequency_links=sum(
                    edge.mode in SCHEDULED_MODES and edge.frequency_per_week is None
                    for edge in pilot.edges
                ),
            )
            for pilot in queries.list()
        )

    @router.get("/pilots/{pilot_id}")
    def get_pilot(pilot_id: str) -> PilotResponse:
        pilot = queries.get(pilot_id)
        edges = []
        for edge in pilot.edges:
            allowed = edge.frequency_per_week is None or 1 <= edge.frequency_per_week <= 28
            editable = edge.editable and allowed
            reason = None
            if not allowed:
                reason = "source_frequency_out_of_range"
            elif not edge.editable:
                reason = "derived_road_edge"
            edges.append(
                EdgeResponse(
                    **{**asdict(edge), "editable": editable},
                    frequency_editable=editable and edge.mode in SCHEDULED_MODES,
                    edit_disabled_reason=reason,
                )
            )
        return PilotResponse(
            id=pilot.id,
            name=pilot.name,
            model_version=pilot.model_version,
            artifact_version=pilot.artifact_version,
            points=tuple(PointResponse.model_validate(point) for point in pilot.points),
            edges=tuple(edges),
            pairs=tuple(PairResponse.model_validate(pair) for pair in pilot.pairs),
            assumptions=pilot.assumptions,
        )

    @router.post("/pilots/{pilot_id}/evaluate", responses={409: {"model": ErrorResponse}})
    def evaluate_pilot(pilot_id: str, request: EvaluationRequest) -> EvaluationResponse:
        result = queries.evaluate(
            pilot_id,
            request.season,
            request.model_version,
            request.artifact_version,
            tuple(
                EdgeChange(change.edge_id, change.enabled, change.frequency_per_week)
                for change in request.changes
            ),
            tuple(
                NewLink(
                    link.from_id,
                    link.to_id,
                    link.mode,
                    link.travel_h,
                    link.seasons,
                    link.frequency_per_week,
                    link.bidirectional,
                )
                for link in request.additions
            ),
        )
        return EvaluationResponse.model_validate(result)

    return router
