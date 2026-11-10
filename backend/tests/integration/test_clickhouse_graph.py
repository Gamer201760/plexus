import math

from tests.storage import atlas_repository

from app.domain.text import normalize_name
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.state import ClickHouseAnalysisStore, ClickHouseRoadJobStore


def test_graph_parameters_preserve_search_literals_and_numeric_identifiers() -> None:
    source = ClickHouseGraphSnapshot(atlas_repository().reader)
    region = source.read("region_name", {"region_id": "17000000"})[0][0]
    assert source.read("region_codes", {"regions": [region]}) == [("17000000", region)]
    points = source.read("locations", {"query": "Владимир", "region": region})
    assert any(p[1] == "г. Владимир" for p in points)
    assert source.read("locations", {"query": "%' OR 1=1 --", "region": ""}) == []
    assert source.read("road_reference", {"name": "м7"})


def test_arrow_keeps_unreachable_matrix_values_infinite() -> None:
    reader = atlas_repository().reader
    source = ClickHouseGraphSnapshot(reader)
    times = source.read("delta_times", {"region": "Владимирская область"})
    expected = reader.rows(
        "SELECT count() AS rows,countIf(isInfinite(road_h)) AS unreachable "
        "FROM plexus_casechamp.np_city_times WHERE season='road' AND point_id IN "
        "(SELECT point_id FROM plexus_casechamp.idx_np "
        "WHERE season='road' AND region={region:String})",
        {"region": "Владимирская область"},
    )[0]
    assert len(times) == expected["rows"] > 0
    assert sum(math.isinf(row[2]) for row in times) == expected["unreachable"]
    values = reader.arrow("SELECT toFloat32('inf') AS unreachable", {})
    assert math.isinf(values["unreachable"][0].as_py())


def test_saved_analysis_details_remain_readable() -> None:
    reader = atlas_repository().reader
    store = ClickHouseAnalysisStore(reader)
    states = store.load()
    assert states
    for job, boundary in states:
        assert job.region_id == boundary.id
        for result in job.results:
            assert store.detail(job.id, result.candidate.way_id).result == result
    assert ClickHouseRoadJobStore(reader).load()


def test_indexed_search_normalization_matches_domain_for_every_name() -> None:
    rows = atlas_repository().reader.rows("SELECT name,name_key FROM plexus_atlas.atlas_settlements", {})
    assert len(rows) == 155412
    assert all(normalize_name(row["name"]) == row["name_key"] for row in rows)
