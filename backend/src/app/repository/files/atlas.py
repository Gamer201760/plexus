from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from threading import Lock, RLock

from app.domain.errors import RegionNotFound
from app.domain.projection import SvgFrame
from app.domain.text import normalize_name
from app.repository.files.geo import boundary_frame, boundary_layer, region_layer
from app.repository.files.json_values import JsonObject, obj, objects, read_json
from app.repository.files.mapping import (
    economy_record,
    index_record,
    link_record,
    point_record,
    region_record,
    settlement_name,
    settlement_record,
    source_record,
    winter_road_record,
)
from app.usecase.dto.atlas import (
    BoundaryShape,
    EconomyRecord,
    GeoLayer,
    IndexRecord,
    LinkRecord,
    PointRecord,
    RegionRecord,
    SettlementName,
    SettlementRecord,
    SourceRecord,
    WinterRoadRecord,
)

ATLAS = "atlas.json"
ADDITIONAL = "additional.json"
INDICES = "indices.json"
REGION_FILE = "additional/regions/{region_id}.json"


@dataclass(frozen=True, slots=True)
class _Atlas:
    regions: list[RegionRecord]
    points: dict[str, PointRecord]
    links: list[LinkRecord]
    total_settlements: int
    sources: list[SourceRecord]


@dataclass(frozen=True, slots=True)
class _Additional:
    economy: dict[str, EconomyRecord]
    winter_roads: list[WinterRoadRecord]
    sources: list[SourceRecord]


class JsonAtlasRepository:
    def __init__(self, data_dir: Path, region_cache_size: int = 8) -> None:
        self._data_dir = data_dir
        self._cache_size = region_cache_size
        self._lock = RLock()
        self._region_lock = Lock()
        self._frame: SvgFrame | None = None
        self._geo: GeoLayer | None = None
        self._boundaries: list[BoundaryShape] | None = None
        self._atlas: _Atlas | None = None
        self._additional: _Additional | None = None
        self._indices: list[IndexRecord] | None = None
        self._names: list[SettlementName] | None = None
        self._settlements: OrderedDict[str, list[SettlementRecord]] = OrderedDict()

    def regions(self) -> list[RegionRecord]:
        return self._load_atlas().regions

    def points(self) -> dict[str, PointRecord]:
        return self._load_atlas().points

    def links(self, region_id: str | None = None) -> list[LinkRecord]:
        return [
            link
            for link in self._load_atlas().links
            if region_id is None or link.region_id == region_id
        ]

    def total_settlements(self) -> int:
        return self._load_atlas().total_settlements

    def economy(self) -> dict[str, EconomyRecord]:
        return self._load_additional().economy

    def winter_roads(self) -> list[WinterRoadRecord]:
        return self._load_additional().winter_roads

    def sources(self) -> list[SourceRecord]:
        return [*self._load_additional().sources, *self._load_atlas().sources]

    def search_names(self, needle: str) -> list[SettlementName]:
        return [p for p in self.settlement_names() if needle in normalize_name(p.name)]

    def geo(self) -> GeoLayer:
        with self._lock:
            if self._geo is None:
                self._geo = region_layer(self._data_dir)
            return self._geo

    def boundaries(self) -> list[BoundaryShape]:
        with self._lock:
            if self._boundaries is None:
                self._boundaries = boundary_layer(self._data_dir)
            return self._boundaries

    def indices(self) -> list[IndexRecord]:
        with self._lock:
            if self._indices is None:
                rows = [index_record(row) for row in objects(read_json(self._data_dir, INDICES))]
                self._indices = [row for row in rows if row is not None]
            return self._indices

    def settlements(self, region_id: str) -> list[SettlementRecord]:
        with self._region_lock:
            cached = self._settlements.get(region_id)
            if cached is not None:
                self._settlements.move_to_end(region_id)
                return cached
        frame = self.frame()
        rows = [settlement_record(row, frame) for row in self._region_rows(region_id)]
        records = [row for row in rows if row is not None]
        with self._region_lock:
            self._settlements[region_id] = records
            while len(self._settlements) > self._cache_size:
                self._settlements.popitem(last=False)
        return records

    def cached_regions(self) -> list[str]:
        with self._region_lock:
            return list(self._settlements)

    def settlement_names(self) -> list[SettlementName]:
        with self._lock:
            if self._names is None:
                names = [
                    settlement_name(row)
                    for region in self.regions()
                    for row in self._region_rows(region.id)
                ]
                self._names = [name for name in names if name is not None]
            return self._names

    def frame(self) -> SvgFrame:
        with self._lock:
            if self._frame is None:
                self._frame = boundary_frame(self._data_dir)
            return self._frame

    def _region_rows(self, region_id: str) -> list[JsonObject]:
        if region_id not in {region.id for region in self.regions()}:
            raise RegionNotFound()
        return objects(read_json(self._data_dir, REGION_FILE.format(region_id=region_id)))

    def _load_atlas(self) -> _Atlas:
        with self._lock:
            if self._atlas is None:
                document = obj(read_json(self._data_dir, ATLAS))
                network = (
                    obj(read_json(self._data_dir, "network-links.json"))
                    if (self._data_dir / "network-links.json").exists()
                    else {}
                )
                frame = self.frame()
                regions = [region_record(row) for row in objects(document.get("regions"))]
                point_rows = objects(document.get("points")) + objects(network.get("points"))
                link_rows = objects(document.get("links")) + objects(network.get("links"))
                points = [point_record(row, frame) for row in point_rows]
                links = [link_record(row) for row in link_rows]
                sources = [source_record(row) for row in objects(network.get("sources"))]
                kept = [region for region in regions if region is not None]
                self._atlas = _Atlas(
                    regions=kept,
                    points={point.id: point for point in points if point is not None},
                    links=[link for link in links if link is not None],
                    total_settlements=sum(region.settlements for region in kept),
                    sources=[source for source in sources if source is not None],
                )
            return self._atlas

    def _load_additional(self) -> _Additional:
        with self._lock:
            if self._additional is None:
                document = obj(read_json(self._data_dir, ADDITIONAL))
                economy = [economy_record(row) for row in objects(document.get("regions"))]
                sources = [source_record(row) for row in objects(document.get("sources"))]
                self._additional = _Additional(
                    economy={row.region_id: row for row in economy if row is not None},
                    winter_roads=[
                        winter_road_record(row) for row in objects(document.get("route_seasons"))
                    ],
                    sources=[row for row in sources if row is not None],
                )
            return self._additional
