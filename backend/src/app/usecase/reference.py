from dataclasses import dataclass

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
        shapes = [
            RegionShape(id=shape.id, name=names.get(shape.id, shape.name), path=shape.path)
            for shape in layer.shapes
        ]
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
                title="Атлас · ручные транспортные связи",
                period=_years([link.source_date for link in links]),
                url=None,
                note="Региональные CSV проекта: у каждой связи своя ссылка и дата источника.",
                rows=len(links),
            ),
            SourceRecord(
                id="atlas-settlements",
                title="Атлас · населённые пункты",
                period=None,
                url=None,
                note="Координаты и население населённых пунктов 82 регионов атласа.",
                rows=self._repository.total_settlements(),
            ),
            SourceRecord(
                id="region-geometry",
                title=layer.source or "Границы регионов",
                period=None,
                url=layer.source_url,
                note=None,
                rows=len(layer.shapes),
            ),
        ]
        return [*atlas, *self._repository.sources()]
