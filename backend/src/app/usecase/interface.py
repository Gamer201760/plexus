from typing import Protocol

from app.usecase.dto import (
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

type LogValue = str | int | float | bool | None


class Logger(Protocol):
    def info(self, event: str, **fields: LogValue) -> None: ...

    def warning(self, event: str, **fields: LogValue) -> None: ...

    def error(
        self, event: str, *, exc: BaseException | None = None, **fields: LogValue
    ) -> None: ...


class AtlasRepository(Protocol):
    def regions(self) -> list[RegionRecord]: ...

    def points(self) -> dict[str, PointRecord]: ...

    def links(self, region_id: str | None = None) -> list[LinkRecord]: ...

    def economy(self) -> dict[str, EconomyRecord]: ...

    def total_settlements(self) -> int: ...

    def settlements(self, region_id: str) -> list[SettlementRecord]: ...

    def settlement_names(self) -> list[SettlementName]: ...

    def search_names(self, needle: str) -> list[SettlementName]: ...

    def geo(self) -> GeoLayer: ...

    def boundaries(self) -> list[BoundaryShape]: ...

    def winter_roads(self) -> list[WinterRoadRecord]: ...

    def sources(self) -> list[SourceRecord]: ...

    def indices(self) -> list[IndexRecord]: ...
