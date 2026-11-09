from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Query

from app.controller.atlas.mapping import index_response, overview_response
from app.controller.atlas.responses import INVALID, UNAVAILABLE
from app.controller.atlas.schemas import (
    GeoRegionsResponse,
    IndexStatusResponse,
    OverviewResponse,
    RegionRefResponse,
    RegionShapeResponse,
    SearchResponse,
    SettlementHitResponse,
    SourceResponse,
    WinterRoadResponse,
)
from app.usecase.overview import OverviewQuery
from app.usecase.reference import ReferenceQueries
from app.usecase.search import MAX_LIMIT, MIN_QUERY, Search


def build_catalog_router(
    overview: OverviewQuery, reference: ReferenceQueries, search: Search
) -> APIRouter:
    router = APIRouter(tags=["catalog"])

    @router.get("/overview", responses=UNAVAILABLE)
    def get_overview() -> OverviewResponse:
        return overview_response(overview.run())

    @router.get("/geo/regions", responses=UNAVAILABLE)
    def get_geo_regions() -> GeoRegionsResponse:
        geo = reference.geo()
        return GeoRegionsResponse(
            view_box=geo.view_box,
            regions=[RegionShapeResponse(**asdict(item)) for item in geo.regions],
            missing=[RegionRefResponse(**asdict(item)) for item in geo.missing],
        )

    @router.get("/search", responses=INVALID)
    def search_atlas(
        q: Annotated[str, Query(min_length=MIN_QUERY, max_length=100)],
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = 8,
    ) -> SearchResponse:
        result = search.run(q, limit)
        return SearchResponse(
            regions=[RegionRefResponse(**asdict(item)) for item in result.regions],
            settlements=[SettlementHitResponse(**asdict(item)) for item in result.settlements],
        )

    @router.get("/seasons/winter-roads", responses=UNAVAILABLE)
    def list_winter_roads() -> list[WinterRoadResponse]:
        return [WinterRoadResponse(**asdict(item)) for item in reference.winter_roads()]

    @router.get("/sources", responses=UNAVAILABLE)
    def list_sources() -> list[SourceResponse]:
        return [SourceResponse(**asdict(item)) for item in reference.sources()]

    @router.get("/index", responses=UNAVAILABLE)
    def get_index() -> IndexStatusResponse:
        return index_response(reference.index())

    return router
