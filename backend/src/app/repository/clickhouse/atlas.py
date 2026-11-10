from dataclasses import fields
from functools import cached_property
from typing import Any, cast

from app.domain.errors import RegionNotFound
from app.domain.transport import Confidence, Mode, Season
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.dto.atlas import (
    BoundaryShape,
    EconomyRecord,
    GeoLayer,
    IndexRecord,
    LinkRecord,
    PointRecord,
    RegionRecord,
    RegionShape,
    SettlementName,
    SettlementRecord,
    SourceRecord,
    WinterRoadRecord,
)


def record[T](kind: type[T], row: dict[str, Any]) -> T:
    if kind is LinkRecord:
        for key, enum in [("mode", Mode), ("season", Season), ("confidence", Confidence)]:
            if row[key] is not None:
                row[key] = enum(row[key])
    if kind is BoundaryShape:
        row["bounds"] = tuple(row["bounds"])
    return kind(**row)


class ClickHouseAtlasRepository:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def load[T](self, table: str, kind: type[T], region_id: str | None = None) -> list[T]:
        columns = ",".join("`" + f.name + "`" for f in fields(cast(Any, kind)))
        condition = " WHERE region_id={region:String}" if region_id is not None else ""
        rows = self.reader.rows(
            f"SELECT {columns} FROM plexus_atlas.{table}" + condition + " ORDER BY ordinal",
            {"region": region_id or ""},
        )
        return [record(kind, row) for row in rows]

    @cached_property
    def region_records(self) -> list[RegionRecord]:
        return self.load("atlas_regions", RegionRecord)

    def regions(self) -> list[RegionRecord]:
        return self.region_records

    @cached_property
    def point_records(self) -> dict[str, PointRecord]:
        return {p.id: p for p in self.load("atlas_points", PointRecord)}

    def points(self) -> dict[str, PointRecord]:
        return self.point_records

    @cached_property
    def link_records(self) -> list[LinkRecord]:
        return self.load("atlas_links", LinkRecord)

    def links(self, region_id: str | None = None) -> list[LinkRecord]:
        if region_id is not None:
            return self.load("atlas_links", LinkRecord, region_id)
        return self.link_records

    def economy(self) -> dict[str, EconomyRecord]:
        return {r.region_id: r for r in self.load("atlas_economy", EconomyRecord)}

    def total_settlements(self) -> int:
        return sum(r.settlements for r in self.regions())

    def settlements(self, region_id: str) -> list[SettlementRecord]:
        if region_id not in {r.id for r in self.regions()}:
            raise RegionNotFound()
        return self.load("atlas_settlements", SettlementRecord, region_id)

    def settlement_names(self) -> list[SettlementName]:
        return self.load("atlas_settlements", SettlementName)

    def search_names(self, needle: str) -> list[SettlementName]:
        pattern = "%" + needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        rows = self.reader.rows(
            "SELECT id,name,region_id,population FROM plexus_atlas.atlas_settlements WHERE name_key LIKE {pattern:String} ORDER BY ordinal",
            {"pattern": pattern},
        )
        return [SettlementName(**r) for r in rows]

    @cached_property
    def metadata(self) -> dict[str, str]:
        return {
            r["key"]: r["value"]
            for r in self.reader.rows("SELECT key,value FROM plexus_atlas.atlas_metadata", {})
        }

    @cached_property
    def geometry(self) -> GeoLayer:
        return GeoLayer(
            self.metadata["view_box"],
            self.load("atlas_shapes", RegionShape),
            self.metadata["geo_source"] or None,
            self.metadata["geo_url"] or None,
        )

    def geo(self) -> GeoLayer:
        return self.geometry

    @cached_property
    def boundary_records(self) -> list[BoundaryShape]:
        return self.load("atlas_boundaries", BoundaryShape)

    def boundaries(self) -> list[BoundaryShape]:
        return self.boundary_records

    def winter_roads(self) -> list[WinterRoadRecord]:
        return self.load("atlas_winter_roads", WinterRoadRecord)

    def sources(self) -> list[SourceRecord]:
        return self.load("atlas_sources", SourceRecord)

    @cached_property
    def index_records(self) -> list[IndexRecord]:
        return self.load("atlas_indices", IndexRecord)

    def indices(self) -> list[IndexRecord]:
        return self.index_records
