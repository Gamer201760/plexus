from pydantic import BaseModel, Field

from app.domain.transport import Confidence, Mode, Season
from app.usecase.index_status import IndexState


class IndexComponentResponse(BaseModel):
    key: str
    title: str
    description: str
    source: str


class IndexStatusResponse(BaseModel):
    status: IndexState
    reason: str | None
    formula: str
    half_life_hours: int
    markets: int
    components: list[IndexComponentResponse]


class SeasonCountsResponse(BaseModel):
    summer: int
    winter: int
    all: int
    unknown: int


class ModeTotalsResponse(BaseModel):
    bus: int
    air: int
    river: int
    winter_road: int
    ferry: int
    ice_crossing: int
    pontoon_bridge: int


class OverviewResponse(BaseModel):
    regions: int
    settlements: int
    population: int
    links: int
    links_by_mode: ModeTotalsResponse
    links_by_season: SeasonCountsResponse
    companies: int | None
    revenue_rub: float | None
    index: IndexStatusResponse


class RegionRefResponse(BaseModel):
    id: str
    name: str


class RegionShapeResponse(BaseModel):
    id: str
    name: str
    path: str
    path_low: str | None = None


class GeoRegionsResponse(BaseModel):
    view_box: str
    regions: list[RegionShapeResponse]
    missing: list[RegionRefResponse]


class RegionSummaryResponse(BaseModel):
    id: str
    name: str
    settlements: int
    population: int
    links: int
    links_season: int
    companies: int | None
    revenue_rub: float | None
    hansen: float | None
    has_geometry: bool


class ModeCountsResponse(BaseModel):
    mode: Mode
    all: int
    summer: int
    winter: int


class EconomyResponse(BaseModel):
    company_rows: int | None
    strict_rows: int | None
    strict_revenue_rub: float | None
    fns_matched_rows: int | None


class RegionDetailResponse(RegionSummaryResponse):
    path: str | None
    bbox: tuple[float, float, float, float] | None
    links_by_mode: list[ModeCountsResponse]
    economy: EconomyResponse | None


class EndpointResponse(BaseModel):
    id: str
    name: str
    x: float | None
    y: float | None


class LinkResponse(BaseModel):
    id: str
    region_id: str
    mode: Mode
    season: Season | None
    origin: EndpointResponse = Field(serialization_alias="from")
    destination: EndpointResponse = Field(serialization_alias="to")
    km: float | None
    freq_per_week: float | None
    freq_assumed: bool
    freq_note: str | None
    vehicle: str | None
    confidence: Confidence | None
    source_url: str | None
    source_date: str | None


class SettlementResponse(BaseModel):
    id: str
    name: str
    region_id: str
    population: int | None
    x: float | None
    y: float | None
    companies: int | None
    revenue_rub: float | None


class SettlementPageResponse(BaseModel):
    total: int
    items: list[SettlementResponse]


class SettlementHitResponse(BaseModel):
    id: str
    name: str
    region_id: str
    region_name: str
    population: int | None


class SearchResponse(BaseModel):
    regions: list[RegionRefResponse]
    settlements: list[SettlementHitResponse]


class WinterRoadResponse(BaseModel):
    district: str | None
    route: str | None
    road_km: float | None
    opening_date: str | None
    closure_date: str | None
    weight_limit_tonnes: float | None
    season_end_year: int | None
    report_date: str | None
    source_file: str | None


class SourceResponse(BaseModel):
    id: str
    title: str
    period: str | None
    url: str | None
    note: str | None
    rows: int | None
