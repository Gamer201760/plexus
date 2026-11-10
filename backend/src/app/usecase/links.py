from dataclasses import dataclass

from app.domain.errors import LinkNotFound, RegionNotFound
from app.domain.transport import (
    Confidence,
    Mode,
    Season,
    great_circle_km,
    is_frequency_assumed,
    runs_in_season,
)
from app.usecase.dto import LinkRecord, PointRecord
from app.usecase.interface import AtlasRepository


@dataclass(frozen=True, slots=True)
class Endpoint:
    id: str
    name: str
    x: float | None
    y: float | None
    lat: float | None = None
    lon: float | None = None


@dataclass(frozen=True, slots=True)
class LinkView:
    id: str
    region_id: str
    mode: Mode
    season: Season | None
    origin: Endpoint
    destination: Endpoint
    km: float | None
    freq_per_week: float | None
    freq_assumed: bool
    freq_note: str | None
    vehicle: str | None
    confidence: Confidence | None
    source_url: str | None
    source_date: str | None
    is_model: bool = False


@dataclass(frozen=True, slots=True)
class RouteView:
    id: str
    mode: Mode
    season: Season | None
    from_name: str
    to_name: str
    x1: float
    y1: float
    x2: float
    y2: float


def _endpoint(point_id: str, name: str, points: dict[str, PointRecord]) -> Endpoint:
    point = points.get(point_id)
    if point is None:
        return Endpoint(id=point_id, name=name, x=None, y=None)
    return Endpoint(
        id=point_id, name=name, x=point.x, y=point.y, lat=point.lat, lon=point.lon
    )


def _span_km(link: LinkRecord, points: dict[str, PointRecord]) -> float | None:
    start, end = points.get(link.from_id), points.get(link.to_id)
    if start is None or end is None:
        return None
    return great_circle_km((start.lat, start.lon), (end.lat, end.lon))


def link_view(link: LinkRecord, points: dict[str, PointRecord]) -> LinkView:
    return LinkView(
        id=link.id,
        region_id=link.region_id,
        mode=link.mode,
        season=link.season,
        origin=_endpoint(link.from_id, link.from_name, points),
        destination=_endpoint(link.to_id, link.to_name, points),
        km=link.km,
        freq_per_week=link.freq_per_week,
        freq_assumed=not link.is_model
        and is_frequency_assumed(link.mode, link.freq_per_week, _span_km(link, points)),
        freq_note=link.freq_note,
        vehicle=link.vehicle,
        confidence=link.confidence,
        source_url=link.source_url,
        source_date=link.source_date,
        is_model=link.is_model,
    )


class LinkQueries:
    def __init__(self, repository: AtlasRepository) -> None:
        self._repository = repository

    def region_links(
        self, region_id: str, season: Season, mode: Mode | None = None,
        include_unknown: bool = False,
    ) -> list[LinkView]:
        if region_id not in {region.id for region in self._repository.regions()}:
            raise RegionNotFound()
        points = self._repository.points()
        return [
            link_view(link, points)
            for link in self._repository.links(region_id)
            if link.region_id == region_id
            and (runs_in_season(link.season, season) or (include_unknown and link.season is None))
            and (mode is None or link.mode is mode)
        ]

    def routes(self) -> list[RouteView]:
        points = self._repository.points()
        routes: list[RouteView] = []
        for link in self._repository.links():
            start, end = points.get(link.from_id), points.get(link.to_id)
            if start is None or end is None:
                continue
            routes.append(
                RouteView(
                    id=link.id,
                    mode=link.mode,
                    season=link.season,
                    from_name=link.from_name,
                    to_name=link.to_name,
                    x1=start.x,
                    y1=start.y,
                    x2=end.x,
                    y2=end.y,
                )
            )
        return routes

    def get(self, link_id: str) -> LinkView:
        link = next((item for item in self._repository.links() if item.id == link_id), None)
        if link is None:
            raise LinkNotFound()
        return link_view(link, self._repository.points())
