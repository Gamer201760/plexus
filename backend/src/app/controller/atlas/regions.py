from typing import Annotated

from fastapi import APIRouter, Query

from app.controller.atlas.mapping import (
    detail_response,
    link_response,
    route_response,
    settlement_response,
    summary_response,
)
from app.controller.atlas.responses import INVALID, NOT_FOUND, UNAVAILABLE
from app.controller.atlas.schemas import (
    LinkResponse,
    RegionDetailResponse,
    RegionSummaryResponse,
    RouteResponse,
    SettlementPageResponse,
)
from app.domain.transport import Mode, NetworkMode, Season
from app.usecase.links import LinkQueries
from app.usecase.regions import RegionQueries
from app.usecase.settlements import (
    MAX_PAGE,
    SettlementQueries,
    SettlementQuery,
    SettlementSort,
    SortOrder,
)


def build_regions_router(
    regions: RegionQueries, links: LinkQueries, settlements: SettlementQueries
) -> APIRouter:
    router = APIRouter(tags=["regions"])

    @router.get("/regions", responses=INVALID)
    def list_regions(
        season: Season = Season.ALL, network_mode: NetworkMode = NetworkMode.MULTIMODAL
    ) -> list[RegionSummaryResponse]:
        return [summary_response(item) for item in regions.summaries(season, network_mode)]

    @router.get("/regions/{region_id}", responses=NOT_FOUND)
    def get_region(
        region_id: str,
        season: Season = Season.ALL,
        network_mode: NetworkMode = NetworkMode.MULTIMODAL,
    ) -> RegionDetailResponse:
        return detail_response(regions.detail(region_id, season, network_mode))

    @router.get("/regions/{region_id}/links", responses=NOT_FOUND)
    def list_region_links(
        region_id: str, season: Season = Season.ALL, mode: Mode | None = None
    ) -> list[LinkResponse]:
        return [link_response(item) for item in links.region_links(region_id, season, mode)]

    @router.get("/regions/{region_id}/settlements", responses=NOT_FOUND)
    def list_settlements(
        region_id: str,
        q: Annotated[str | None, Query(max_length=100)] = None,
        sort: SettlementSort = SettlementSort.POPULATION,
        order: SortOrder = SortOrder.DESC,
        limit: Annotated[int, Query(ge=1, le=MAX_PAGE)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> SettlementPageResponse:
        page = settlements.page(
            SettlementQuery(
                region_id=region_id, text=q, sort=sort, order=order, limit=limit, offset=offset
            )
        )
        return SettlementPageResponse(
            total=page.total, items=[settlement_response(item) for item in page.items]
        )

    @router.get("/links", responses=UNAVAILABLE)
    def list_routes() -> list[RouteResponse]:
        return [route_response(item) for item in links.routes()]

    @router.get("/links/{link_id}", responses=NOT_FOUND)
    def get_link(link_id: str) -> LinkResponse:
        return link_response(links.get(link_id))

    return router
