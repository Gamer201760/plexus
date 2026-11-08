from dataclasses import dataclass, field

import pytest

from app.domain.errors import InvalidQuery, LinkNotFound, RegionNotFound
from app.domain.transport import Confidence, Mode, Season
from app.usecase.dto import (
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
from app.usecase.index_status import IndexState
from app.usecase.links import LinkQueries
from app.usecase.overview import OverviewQuery
from app.usecase.reference import ReferenceQueries
from app.usecase.regions import RegionQueries
from app.usecase.search import Search
from app.usecase.settlements import (
    SettlementQueries,
    SettlementQuery,
    SettlementSort,
    SortOrder,
)


def link(link_id: str, mode: Mode, season: Season | None, region: str = "R1") -> LinkRecord:
    return LinkRecord(
        id=link_id,
        region_id=region,
        mode=mode,
        season=season,
        from_id="P1",
        from_name="Ёлкино",
        to_id="P2",
        to_name="Озёрный",
        km=None,
        freq_per_week=None,
        freq_note=None,
        vehicle=None,
        confidence=Confidence.HIGH,
        source_url=None,
        source_date="2025-03",
    )


def settlement(
    sid: str, name: str, population: int | None, companies: int | None
) -> SettlementRecord:
    return SettlementRecord(sid, name, "R1", population, 1.0, 2.0, companies, None)


@dataclass
class FakeAtlas:
    region_rows: list[RegionRecord] = field(
        default_factory=lambda: [
            RegionRecord("R2", "Бета", 1, 5),
            RegionRecord("R1", "Альфа", 3, 30),
        ]
    )
    link_rows: list[LinkRecord] = field(
        default_factory=lambda: [
            link("0", Mode.AIR, Season.SUMMER),
            link("1", Mode.AIR, Season.ALL),
            link("2", Mode.WINTER_ROAD, Season.WINTER),
            link("3", Mode.RIVER, None),
            link("4", Mode.FERRY, Season.SUMMER, "R2"),
        ]
    )
    economy_rows: dict[str, EconomyRecord] = field(
        default_factory=lambda: {"R1": EconomyRecord("R1", 7, 4, 1.5e9, 3)}
    )
    index_rows: list[IndexRecord] = field(default_factory=list)
    settlement_rows: list[SettlementRecord] = field(
        default_factory=lambda: [
            settlement("S1", "село Ёлкино", 100, None),
            settlement("S2", "г. Озёрный", 900, 5),
            settlement("S3", "деревня Елочка", None, 2),
        ]
    )

    def regions(self) -> list[RegionRecord]:
        return self.region_rows

    def points(self) -> dict[str, PointRecord]:
        return {"P1": PointRecord("P1", "Ёлкино", "R1", 60.0, 100.0, 10.0, 20.0)}

    def links(self) -> list[LinkRecord]:
        return self.link_rows

    def economy(self) -> dict[str, EconomyRecord]:
        return self.economy_rows

    def total_settlements(self) -> int:
        return 4

    def settlements(self, region_id: str) -> list[SettlementRecord]:
        return [row for row in self.settlement_rows if row.region_id == region_id]

    def settlement_names(self) -> list[SettlementName]:
        return [
            SettlementName(s.id, s.name, s.region_id, s.population) for s in self.settlement_rows
        ]

    def geo(self) -> GeoLayer:
        return GeoLayer(
            "0 0 1000 620", [RegionShape("R1", "A", "M1,2L5,8Z")], "Geo snapshot 2013", None
        )

    def winter_roads(self) -> list[WinterRoadRecord]:
        return []

    def sources(self) -> list[SourceRecord]:
        return [
            SourceRecord("rfsd", "RFSD · финансы", "2025", None, None, 10),
            SourceRecord("other", "Издатель · набор", None, None, None, None),
        ]

    def indices(self) -> list[IndexRecord]:
        return self.index_rows


def test_regions_sorted_with_season_counts_and_unknown_economy() -> None:
    summaries = RegionQueries(FakeAtlas()).summaries(Season.WINTER)

    assert [item.id for item in summaries] == ["R1", "R2"]
    assert (summaries[0].links, summaries[0].links_season) == (4, 2)
    assert (summaries[1].companies, summaries[1].revenue_rub, summaries[1].hansen) == (
        None,
        None,
        None,
    )
    assert (summaries[0].has_geometry, summaries[1].has_geometry) == (True, False)


def test_region_detail_counts_modes_per_season() -> None:
    detail = RegionQueries(FakeAtlas()).detail("R1", Season.ALL)

    counts = {item.mode: (item.all, item.summer, item.winter) for item in detail.links_by_mode}
    assert counts == {Mode.AIR: (2, 2, 1), Mode.RIVER: (1, 0, 0), Mode.WINTER_ROAD: (1, 0, 1)}
    assert detail.bbox == (1.0, 2.0, 4.0, 6.0)
    assert detail.economy is not None and detail.economy.company_rows == 7
    with pytest.raises(RegionNotFound):
        RegionQueries(FakeAtlas()).detail("R9", Season.ALL)


def test_hansen_uses_road_scenario_for_all_seasons() -> None:
    atlas = FakeAtlas(
        index_rows=[IndexRecord("R1", "road", 80.0), IndexRecord("R1", "winter", 60.0)]
    )

    assert RegionQueries(atlas).summaries(Season.ALL)[0].hansen == 80.0
    assert RegionQueries(atlas).summaries(Season.WINTER)[0].hansen == 60.0
    assert RegionQueries(atlas).summaries(Season.SUMMER)[0].hansen is None
    assert ReferenceQueries(atlas).index().status is IndexState.READY


def test_region_links_filter_and_resolve_endpoints() -> None:
    queries = LinkQueries(FakeAtlas())

    winter = queries.region_links("R1", Season.WINTER)
    assert [item.id for item in winter] == ["1", "2"]
    assert [item.id for item in queries.region_links("R1", Season.ALL, Mode.AIR)] == ["0", "1"]
    first = queries.get("0")
    assert (first.origin.x, first.destination.x) == (10.0, None)
    assert first.freq_assumed is True
    assert queries.get("2").freq_assumed is False
    with pytest.raises(LinkNotFound):
        queries.get("x")
    with pytest.raises(RegionNotFound):
        queries.region_links("R9", Season.ALL)


def test_overview_counts_raw_seasons_and_sums_known_economy() -> None:
    overview = OverviewQuery(FakeAtlas()).run()

    assert overview.links_by_season == {"all": 1, "summer": 2, "winter": 1, "unknown": 1}
    assert overview.links_by_mode["air"] == 2 and overview.links_by_mode["ice_crossing"] == 0
    assert (overview.companies, overview.revenue_rub, overview.population) == (7, 1.5e9, 35)
    assert overview.index.status is IndexState.MISSING and overview.index.reason
    assert OverviewQuery(FakeAtlas(economy_rows={})).run().companies is None


@pytest.mark.parametrize(
    ("sort", "order", "expected"),
    [
        (SettlementSort.POPULATION, SortOrder.DESC, ["S2", "S1", "S3"]),
        (SettlementSort.POPULATION, SortOrder.ASC, ["S1", "S2", "S3"]),
        (SettlementSort.COMPANIES, SortOrder.DESC, ["S2", "S3", "S1"]),
        (SettlementSort.NAME, SortOrder.ASC, ["S2", "S3", "S1"]),
        (SettlementSort.NAME, SortOrder.DESC, ["S1", "S3", "S2"]),
    ],
)
def test_settlement_sorting_keeps_unknown_last(
    sort: SettlementSort, order: SortOrder, expected: list[str]
) -> None:
    page = SettlementQueries(FakeAtlas()).page(SettlementQuery("R1", sort=sort, order=order))

    assert [item.id for item in page.items] == expected


def test_settlement_text_filter_and_paging() -> None:
    queries = SettlementQueries(FakeAtlas())

    page = queries.page(SettlementQuery("R1", text="ЕЛ", limit=1, offset=1))
    assert (page.total, [item.id for item in page.items]) == (2, ["S3"])
    with pytest.raises(InvalidQuery):
        queries.page(SettlementQuery("R1", limit=0))
    with pytest.raises(RegionNotFound):
        queries.page(SettlementQuery("R9"))


def test_search_folds_yo_and_ranks_word_starts() -> None:
    result = Search(FakeAtlas()).run("ёл", limit=5)

    assert [hit.id for hit in result.settlements] == ["S1", "S3"]
    assert result.settlements[0].region_name == "Альфа"
    assert [hit.id for hit in Search(FakeAtlas()).run("ал").regions] == ["R1"]
    with pytest.raises(InvalidQuery):
        Search(FakeAtlas()).run(" е ")


def test_sources_and_geo_combine_atlas_and_additional() -> None:
    reference = ReferenceQueries(FakeAtlas())

    sources = reference.sources()
    assert [item.id for item in sources][-2:] == ["rfsd", "other"]
    assert sources[0].rows == 5 and sources[0].period == "2025"
    assert sources[2].title == "Границы регионов: Click That Hood, OpenStreetMap"
    assert sources[2].period == "2013"
    assert [item.title for item in sources][-2:] == ["Финансы компаний: RFSD", "Издатель: набор"]
    assert all("·" not in item.title for item in sources)
    geo = reference.geo()
    assert [shape.name for shape in geo.regions] == ["Альфа"]
    assert [(stub.id, stub.name) for stub in geo.missing] == [("R2", "Бета")]
