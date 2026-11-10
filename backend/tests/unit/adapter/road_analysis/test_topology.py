import numpy as np

from app.adapter.road_analysis.topology import bridge_exposure
from app.adapter.road_graph.routing import minimum_csr


def test_bridge_exposure_excludes_branch_with_another_market() -> None:
    graph = minimum_csr(np.array([0, 1, 1]), np.array([1, 2, 3]), np.ones(3), 4)
    result = bridge_exposure(
        graph, np.array([0, 2]), np.array([2, 3]), np.array([50.0, 100.0]), lambda: None
    )
    assert result == {(1, 3): 100.0}


def test_alternative_path_is_not_a_bridge() -> None:
    graph = minimum_csr(np.array([0, 1, 0]), np.array([1, 2, 2]), np.ones(3), 3)
    assert (
        bridge_exposure(graph, np.array([0]), np.array([2]), np.array([100.0]), lambda: None) == {}
    )
