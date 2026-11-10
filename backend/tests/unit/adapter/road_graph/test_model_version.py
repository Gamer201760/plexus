from pathlib import Path
from typing import Any, Literal

import numpy as np
import pytest

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.routing import GraphRouting
from app.usecase.graph_snapshot import GraphParameters, GraphQuery


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


def test_road_baseline_excludes_seasonal_shortcut_and_air(tmp_path: Path) -> None:
    routing = GraphRouting(GraphData(tmp_path, ModernSnapshot(winter=True)))
    road = routing.calculate("region", "road", [], lambda _: None)[0]
    winter = routing.calculate("region", "road_winter", [], lambda _: None)[0]
    assert road == pytest.approx(3.125)
    assert winter == pytest.approx(100 * 2 ** (-.1 / 2))


def test_multimodal_route_keeps_documented_frequency_wait(tmp_path: Path) -> None:
    routing = GraphRouting(GraphData(tmp_path, ModernSnapshot()))
    summer = routing.calculate("region", "summer", [], lambda _: None)[0]
    assert summer == pytest.approx(3.125)


def test_market_origin_has_zero_self_trip_like_national_etl(tmp_path: Path) -> None:
    routing = GraphRouting(GraphData(tmp_path, ModernSnapshot(own_market=True)))
    assert routing.calculate("region", "road", [], lambda _: None)[0] == pytest.approx(100.)


def test_prepared_delta_accepts_pure_road_v2_baseline(tmp_path: Path) -> None:
    base = DeltaBase(GraphData(tmp_path, ModernSnapshot()))
    assert base.region("region").baseline_index == pytest.approx(3.125)
