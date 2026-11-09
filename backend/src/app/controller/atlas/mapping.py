from dataclasses import asdict

from app.controller.atlas.schemas import (
    EconomyResponse,
    EndpointResponse,
    IndexComponentResponse,
    IndexStatusResponse,
    LinkResponse,
    ModeCountsResponse,
    ModeTotalsResponse,
    OverviewResponse,
    RegionDetailResponse,
    RegionSummaryResponse,
    RouteResponse,
    SeasonCountsResponse,
    SettlementResponse,
)
from app.usecase.dto import SettlementRecord
from app.usecase.index_status import IndexStatus
from app.usecase.links import Endpoint, LinkView, RouteView
from app.usecase.overview import Overview
from app.usecase.regions import RegionDetail, RegionSummary


def index_response(status: IndexStatus) -> IndexStatusResponse:
    return IndexStatusResponse(
        status=status.status,
        reason=status.reason,
        formula=status.formula,
        half_life_hours=status.half_life_hours,
        markets=status.markets,
        components=[IndexComponentResponse(**asdict(item)) for item in status.components],
    )


def overview_response(overview: Overview) -> OverviewResponse:
    return OverviewResponse(
        regions=overview.regions,
        settlements=overview.settlements,
        population=overview.population,
        links=overview.links,
        links_by_mode=ModeTotalsResponse(**overview.links_by_mode),
        links_by_season=SeasonCountsResponse(**overview.links_by_season),
        companies=overview.companies,
        revenue_rub=overview.revenue_rub,
        index=index_response(overview.index),
    )


def summary_response(summary: RegionSummary) -> RegionSummaryResponse:
    return RegionSummaryResponse(**asdict(summary))


def detail_response(detail: RegionDetail) -> RegionDetailResponse:
    economy = detail.economy
    return RegionDetailResponse(
        **asdict(detail.summary),
        path=detail.path,
        bbox=detail.bbox,
        links_by_mode=[
            ModeCountsResponse(mode=item.mode, all=item.all, summer=item.summer, winter=item.winter)
            for item in detail.links_by_mode
        ],
        economy=EconomyResponse(
            company_rows=economy.company_rows,
            strict_rows=economy.strict_rows,
            strict_revenue_rub=economy.strict_revenue_rub,
            fns_matched_rows=economy.fns_matched_rows,
        )
        if economy
        else None,
    )


def _endpoint(endpoint: Endpoint) -> EndpointResponse:
    return EndpointResponse(id=endpoint.id, name=endpoint.name, x=endpoint.x, y=endpoint.y)


def link_response(link: LinkView) -> LinkResponse:
    return LinkResponse(
        id=link.id,
        region_id=link.region_id,
        mode=link.mode,
        season=link.season,
        origin=_endpoint(link.origin),
        destination=_endpoint(link.destination),
        km=link.km,
        freq_per_week=link.freq_per_week,
        freq_assumed=link.freq_assumed,
        freq_note=link.freq_note,
        vehicle=link.vehicle,
        confidence=link.confidence,
        source_url=link.source_url,
        source_date=link.source_date,
    )


def route_response(route: RouteView) -> RouteResponse:
    return RouteResponse(**asdict(route))


def settlement_response(record: SettlementRecord) -> SettlementResponse:
    return SettlementResponse(**asdict(record))
