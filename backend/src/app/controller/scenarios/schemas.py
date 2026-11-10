from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MarketCityResponse(Response):
    id: str
    region: str
    population: float
    latitude: float
    longitude: float
    is_capital: bool


class ScenarioRegionResponse(Response):
    region_id: str
    name: str


class ScenarioCatalogResponse(Response):
    model_version: str
    artifact_version: str
    seasons: tuple[str, ...]
    cities: tuple[MarketCityResponse, ...]
    regions: tuple[ScenarioRegionResponse, ...]
    assumptions: tuple[str, ...]


class TrunkLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    from_id: str = Field(min_length=1, max_length=120)
    to_id: str = Field(min_length=1, max_length=120)
    mode: Literal["air", "rail", "road"]
    travel_h: float = Field(gt=0, le=200)
    frequency_per_week: int | None = Field(default=None, ge=1, le=28, strict=True)


class ScenarioEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    season: Literal["road", "summer", "winter"]
    model_version: str = Field(min_length=1, max_length=120)
    artifact_version: str = Field(min_length=1, max_length=120)
    links: tuple[TrunkLinkRequest, ...] = Field(min_length=1, max_length=5)


class CityPairChangeResponse(Response):
    from_city: str
    to_city: str
    baseline_h: float | None
    changed_h: float


class SettlementImpactResponse(Response):
    point_id: str
    baseline_index: float
    changed_index: float
    delta_index: float


class RegionImpactResponse(Response):
    region_id: str
    name: str
    population: float
    baseline_index: float
    changed_index: float
    delta_index: float


class ScenarioEvaluationResponse(Response):
    season: str
    model_version: str
    artifact_version: str
    links: tuple[TrunkLinkRequest, ...]
    assumptions: tuple[str, ...]
    national_baseline_index: float
    national_changed_index: float
    improved_city_pairs: int
    city_pairs: tuple[CityPairChangeResponse, ...]
    regions: tuple[RegionImpactResponse, ...]
    settlements: tuple[SettlementImpactResponse, ...]
