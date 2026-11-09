import re
from dataclasses import dataclass, replace

from app.usecase.dto import RegionShape, SourceRecord, WinterRoadRecord
from app.usecase.index_status import IndexStatus, index_status
from app.usecase.interface import AtlasRepository


@dataclass(frozen=True, slots=True)
class RegionStub:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class GeoRegions:
    view_box: str
    regions: list[RegionShape]
    missing: list[RegionStub]


SOURCE_TITLES: dict[str, str] = {
    "rfsd": "Финансы компаний: RFSD",
    "fns-revexp": "Доходы и расходы организаций: ФНС",
    "nighttime-lights": "Ночная освещённость: OpenGeoHub, VIIRS",
    "seasonal-ugra": "Зимники и переправы Югры",
    "seasonal-closures": "Состояние сезонных объектов: МЧС",
}
GEOMETRY_TITLE = "Границы регионов: Click That Hood, OpenStreetMap"
SEPARATOR = re.compile(r"\s*\u00b7\s*")
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def _source_title(record: SourceRecord) -> str:
    return SOURCE_TITLES.get(record.id) or SEPARATOR.sub(": ", record.title)


def _snapshot_year(source: str | None) -> str | None:
    match = YEAR.search(source or "")
    return match.group(0) if match else None


def _years(dates: list[str | None]) -> str | None:
    years = sorted({date[:4] for date in dates if date and date[:4].isdigit()})
    if not years:
        return None
    return years[0] if years[0] == years[-1] else f"{years[0]}–{years[-1]}"


class ReferenceQueries:
    def __init__(self, repository: AtlasRepository) -> None:
        self._repository = repository

    def geo(self) -> GeoRegions:
        layer = self._repository.geo()
        names = {region.id: region.name for region in self._repository.regions()}
        shapes = [replace(shape, name=names.get(shape.id, shape.name)) for shape in layer.shapes]
        drawn = {shape.id for shape in shapes}
        missing = [
            RegionStub(id=region_id, name=name)
            for region_id, name in sorted(names.items(), key=lambda item: item[1])
            if region_id not in drawn
        ]
        return GeoRegions(view_box=layer.view_box, regions=shapes, missing=missing)

    def winter_roads(self) -> list[WinterRoadRecord]:
        return self._repository.winter_roads()

    def index(self) -> IndexStatus:
        return index_status(self._repository.indices())

    def sources(self) -> list[SourceRecord]:
        links = self._repository.links()
        layer = self._repository.geo()
        atlas = [
            SourceRecord(
                id="atlas-links",
                title="Атлас: дополнительные транспортные связи",
                period=_years([link.source_date for link in links]),
                url=None,
                note="Региональные CSV и реестр автобусов: у каждой связи своя ссылка и дата источника.",
                rows=len(links),
            ),
            SourceRecord(
                id="atlas-settlements",
                title="Атлас: населённые пункты",
                period=None,
                url=None,
                note="Координаты и население населённых пунктов 82 регионов атласа.",
                rows=self._repository.total_settlements(),
            ),
            SourceRecord(
                id="region-geometry",
                title=GEOMETRY_TITLE,
                period=_snapshot_year(layer.source),
                url=layer.source_url,
                note=None,
                rows=len(layer.shapes),
            ),
        ]
        extra = [
            replace(record, title=_source_title(record)) for record in self._repository.sources()
        ]
        return [*atlas, *extra]
