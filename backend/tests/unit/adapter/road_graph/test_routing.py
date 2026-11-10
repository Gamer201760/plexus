import math
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.routing import GraphRouting
from app.usecase.road_graph import RoadChange


@pytest.fixture
def routing(tmp_path: Path) -> GraphRouting:
    graph = tmp_path / "graph_ru"
    graph.mkdir()
    pq.write_table(
        pa.table({"lat": [0.0, 0.0, 0.0], "lon": [0.0, 1.0, 2.0]}), graph / "nodes.parquet"
    )
    pq.write_table(
        pa.table(
            {
                "src": [0, 1, 0, 0],
                "dst": [1, 2, 1, 2],
                "h": pa.array([1.0, 1.0, 3.0, 5.0], type=pa.float32()),
                "km": [10.0, 10.0, 30.0, 50.0],
                "way_idx": [0, 1, 2, 3],
            }
        ),
        graph / "edges.parquet",
    )
    pq.write_table(
        pa.table({"point_id": ["origin"], "node": [0], "snap_km": [0.0]}), graph / "points.parquet"
    )
    pq.write_table(
        pa.table(
            {"way_id": [100, 101, 102, 103], "way_idx": [0, 1, 2, 3], "highway": ["primary"] * 4}
        ),
        graph / "ways.parquet",
    )
    with duckdb.connect(str(tmp_path / "casechamp.duckdb")) as con:
        con.execute(
            "create table idx_np as select 'origin' point_id, 10 population, "
            "'region' region, 'road' season, 50. hansen_2h, 50. hansen_idx"
        )
        con.execute(
            "create table market_cities as select 'market' city, 2 node, 0. snap_h, 100 population"
        )
        con.execute(
            "create table stg_intercity(city_from varchar, city_to varchar, "
            "transport_type varchar, distance_hr double)"
        )
    return GraphRouting(GraphData(tmp_path))


def test_parallel_roads_use_minimum_and_fixed_normalization(routing: GraphRouting) -> None:
    before, population, settlements, _, norm = routing.calculate(
        "region", "road", [], lambda _: None
    )
    after, _, _, changed, same_norm = routing.calculate(
        "region", "road", [RoadChange(101, 2.0)], lambda _: None
    )
    assert before == pytest.approx(50.0)
    assert after == pytest.approx(100 * math.exp(-math.log(2) * 1.5 / 2))
    assert norm == same_norm == 100
    assert (population, settlements, changed) == (10, 1, 1)


def test_closure_recomputes_alternative_route(routing: GraphRouting) -> None:
    value, _, _, _, _ = routing.calculate("region", "road", [RoadChange(101, 0)], lambda _: None)
    assert value == pytest.approx(100 * math.exp(-math.log(2) * 5 / 2))


def test_identity_change_preserves_index(routing: GraphRouting) -> None:
    value, _, _, _, _ = routing.calculate("region", "road", [RoadChange(101, 1)], lambda _: None)
    assert value == pytest.approx(50)
