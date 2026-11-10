from typing import Any

import numpy as np

from app.adapter.road_graph.data import GraphData


class ViewData(GraphData):
    def __init__(self, count: int) -> None:
        super().__init__()
        self.loaded = True
        self.modern_model = False
        self.nodes = {"lon": np.linspace(-2, 2, count + 1), "lat": np.zeros(count + 1)}
        self.edges = {
            "src": np.arange(count),
            "dst": np.arange(1, count + 1),
            "way_idx": np.arange(count),
        }
        self.road_rank = np.ones(count, dtype=np.uint8)

    def ways(self, ids: list[int]) -> dict[int, dict[str, Any]]:
        return {
            i: {"way_id": i, "name": str(i), "highway": "trunk", "speed_kmh": 80.0} for i in ids
        }


def test_edge_crossing_viewport_survives_zoom() -> None:
    view = ViewData(1).view((-1.0, -1.0, 1.0, 1.0), 12.0)
    assert len(view.segments) == 1


def test_road_class_is_not_fragmented_by_arbitrary_way_budget() -> None:
    view = ViewData(9000).view((-3.0, -1.0, 3.0, 1.0), 7.0)
    assert len(view.segments) == 9000
