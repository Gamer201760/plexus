from dataclasses import dataclass

from app.domain.transport import Confidence, Mode, Season


@dataclass(frozen=True, slots=True)
class RegionRecord:
    id: str
    name: str
    settlements: int
    population: int


@dataclass(frozen=True, slots=True)
class PointRecord:
    id: str
    name: str
    region_id: str
    lat: float
    lon: float
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class LinkRecord:
    id: str
    region_id: str
    mode: Mode
    season: Season | None
    from_id: str
    from_name: str
    to_id: str
    to_name: str
    km: float | None
    freq_per_week: float | None
    freq_note: str | None
    vehicle: str | None
    confidence: Confidence | None
    source_url: str | None
    source_date: str | None
    is_model: bool = False


@dataclass(frozen=True, slots=True)
class EconomyRecord:
    region_id: str
    company_rows: int | None
    strict_rows: int | None
    strict_revenue_rub: float | None
    fns_matched_rows: int | None


@dataclass(frozen=True, slots=True)
class SettlementRecord:
    id: str
    name: str
    region_id: str
    population: int | None
    x: float | None
    y: float | None
    companies: int | None
    revenue_rub: float | None


@dataclass(frozen=True, slots=True)
class SettlementName:
    id: str
    name: str
    region_id: str
    population: int | None


@dataclass(frozen=True, slots=True)
class RegionShape:
    id: str
    name: str
    path: str
    path_low: str | None = None


type LonLat = tuple[float, float]
type GeoRing = list[LonLat]
type GeoPolygon = list[GeoRing]


@dataclass(frozen=True, slots=True)
class BoundaryShape:
    id: str
    name: str
    bounds: tuple[float, float, float, float]
    polygons: list[GeoPolygon]


@dataclass(frozen=True, slots=True)
class GeoLayer:
    view_box: str
    shapes: list[RegionShape]
    source: str | None
    source_url: str | None


@dataclass(frozen=True, slots=True)
class WinterRoadRecord:
    district: str | None
    route: str | None
    road_km: float | None
    opening_date: str | None
    closure_date: str | None
    weight_limit_tonnes: float | None
    season_end_year: int | None
    report_date: str | None
    source_file: str | None


@dataclass(frozen=True, slots=True)
class SourceRecord:
    id: str
    title: str
    period: str | None
    url: str | None
    note: str | None
    rows: int | None


@dataclass(frozen=True, slots=True)
class IndexRecord:
    region_id: str
    scenario: str
    hansen: float | None
    covered_population: int | None = None
    total_population: int | None = None
    covered_settlements: int | None = None
    total_settlements: int | None = None
    model_version: str | None = None
    artifact_version: str | None = None
    hansen_1h: float | None = None
    hansen_2h: float | None = None
    hansen_4h: float | None = None
