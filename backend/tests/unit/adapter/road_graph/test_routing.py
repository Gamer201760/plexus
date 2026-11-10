import math
from typing import Any, Literal, cast

import numpy as np
import pytest

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.routing import GraphRouting
from app.usecase.dto.graph_snapshot import GraphParameters, GraphQuery
from app.usecase.dto.road_graph import RoadChange


class Snapshot:
    revision = "[]"

    def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]:
        if name == "edges":
            return {"src":np.array([0,1,0,0]), "dst":np.array([1,2,1,2]),
                    "h":np.array([1,1,3,5],dtype=np.float32), "km":np.array([10,10,30,50]),
                    "way_idx":np.array([0,1,2,3])}
        if name == "nodes":
            return {"lat":np.array([0.,0.,0.]), "lon":np.array([0.,1.,2.])}
        return {"rank":np.array([2,2,2,2])}

    def read(self, query: GraphQuery, parameters: GraphParameters | None = None) -> list[tuple[Any,...]]:
        rows: dict[GraphQuery,list[tuple[Any,...]]] = {
            "model_version": [],
            "points": [("origin",0,0.)], "origins": [("origin",10)],
            "cities": [("market",2,0.,100)], "trunk": [], "normalization": [(100.,)],
        }
        if query == "way_indices":
            assert parameters is not None
            ids = cast(list[int], parameters["ids"])
            return [(way,way-100) for way in ids]
        return rows[query]


@pytest.fixture
def routing() -> GraphRouting:
    return GraphRouting(GraphData(Snapshot()))


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
