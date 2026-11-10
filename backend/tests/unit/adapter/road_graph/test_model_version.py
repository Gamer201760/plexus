from typing import Any, Literal

import numpy as np
import pytest

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.routing import GraphRouting
from app.usecase.dto.graph_snapshot import GraphParameters, GraphQuery
from app.usecase.dto.road_graph import DeltaRegion


class ModernSnapshot:
    revision = '["hansen-frequency-v2","fixture"]'

    def __init__(self, winter: bool = False, own_market: bool = False) -> None:
        self.winter = winter
        self.own_market = own_market

    def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]:
        if name == "edges":
            return {
                "src": np.array([0, 0]), "dst": np.array([1, 1]),
                "h": np.array([10., .1], dtype=np.float32), "km": np.array([10., 1.]),
                "way_idx": np.array([0, 1]),
            }
        if name == "nodes":
            return {"lat": np.array([0., 0.]), "lon": np.array([0., 1.])}
        if name == "seasons":
            return {"season": np.array([0, 2 if self.winter else 3], dtype=np.uint8)}
        return {"rank": np.array([2, 2])}

    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]:
        if self.own_market:
            own: dict[str, list[tuple[Any, ...]]] = {
                "points": [("origin", 0, 3.)],
                "cities": [("a", 0, .2, 100, "origin")],
                "trunk": [],
            }
            if query in own:
                return own[query]
        rows: dict[str, list[tuple[Any, ...]]] = {
            "model_version": [("hansen-frequency-v2",)],
            "points": [("origin", 0, 0.)], "origins": [("origin", 10)],
            "cities": [("a", 0, 0., 0, "a-id"), ("b", 1, 0., 100, "b-id")],
            "trunk": [("a", "b", "air", 0.)], "normalization": [(100.,)],
            "manual": [], "manual_v2": [],
            "delta_points": [("origin", 10, 0, 0.)],
            "delta_cities": [("a", "a-id", 0, 0., 0), ("b", "b-id", 1, 0., 100)],
            "delta_times": [("origin", "a", 0.), ("origin", "b", 10.)],
            "city_times": [("a-id", "a", 0.), ("a-id", "b", 10.),
                           ("b-id", "a", 10.), ("b-id", "b", 0.)],
            "expected": [(3.125,)], "regions": [],
        }
        return rows[query]


def test_road_baseline_excludes_seasonal_shortcut_and_air() -> None:
    routing = GraphRouting(GraphData(ModernSnapshot(winter=True)))
    road = routing.calculate("region", "road", [], lambda _: None)[0]
    winter = routing.calculate("region", "road_winter", [], lambda _: None)[0]
    assert road == pytest.approx(3.125)
    assert winter == pytest.approx(100 * 2 ** (-.1 / 2))


def test_multimodal_route_keeps_documented_frequency_wait() -> None:
    routing = GraphRouting(GraphData(ModernSnapshot()))
    summer = routing.calculate("region", "summer", [], lambda _: None)[0]
    assert summer == pytest.approx(3.125)


def test_market_origin_has_zero_self_trip_like_national_etl() -> None:
    routing = GraphRouting(GraphData(ModernSnapshot(own_market=True)))
    assert routing.calculate("region", "road", [], lambda _: None)[0] == pytest.approx(100.)


class MemoryDeltaStore:
    def __init__(self) -> None:
        self.regions: dict[str, DeltaRegion] = {}

    def names(self) -> list[str]:
        return list(self.regions)

    def read(self, region: str) -> DeltaRegion | None:
        return self.regions.get(region)

    def write(self, region: str, value: DeltaRegion) -> None:
        self.regions[region] = value

    def read_terminal(self, node: int) -> tuple[Any, Any] | None:
        return None

    def write_terminal(self, node: int, nodes: Any, distances: Any) -> None:
        return None

    def write_manifest(self, report: dict[str, object]) -> None:
        return None


class MemoryMatrixStore:
    graph: Any = None

    def read(self) -> Any | None:
        return self.graph

    def write(self, graph: Any) -> None:
        self.graph = graph


def test_prepared_delta_accepts_pure_road_v2_baseline() -> None:
    store = MemoryDeltaStore()
    base = DeltaBase(GraphData(ModernSnapshot()), store, MemoryMatrixStore())
    assert base.region("region").baseline_index == pytest.approx(3.125)
