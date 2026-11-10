from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from scipy.sparse.csgraph import dijkstra

from app.adapter.road_graph.delta import DeltaCalculation, added_edge_distances
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.routing import minimum_csr
from app.domain.road_economics import MoneyAssumptions, time_savings
from app.usecase.road_graph import RoadAddition


@pytest.mark.parametrize("source,target,hours", [(0, 3, 0.5), (1, 4, 2.0), (0, 2, 20.0)])
def test_single_edge_delta_matches_full_shortest_path_search(
    source: int, target: int, hours: float
) -> None:
    a, b, w = np.array([0, 1, 2, 3]), np.array([1, 2, 3, 4]), np.array([2.0, 3.0, 4.0, 90.0])
    graph = minimum_csr(a, b, w, 6)
    before = dijkstra(graph, directed=True, limit=72.0)
    expected = dijkstra(
        minimum_csr(np.append(a, source), np.append(b, target), np.append(w, hours), 6),
        directed=True,
        limit=72.0,
    )
    actual = added_edge_distances(
        before, before[:, source], before[:, target], before[source], before[target], hours
    )
    np.testing.assert_allclose(actual, expected)


def test_money_is_time_savings_for_explicit_flow_not_index_conversion() -> None:
    assumptions = MoneyAssumptions("origin", "market", 1000, 300, 900000, 50000)
    effect = time_savings(2, 1.5, assumptions)
    assert effect is not None
    assert effect.annual_hours_saved == 500
    assert effect.annual_gross_rub == 150000
    assert effect.annual_net_rub == 100000
    assert effect.simple_payback_years == 9
    assert time_savings(float("inf"), 1.5, assumptions) is None


def test_settlement_effects_include_transit_origins() -> None:
    roads = np.array([[10.0], [8.0], [0.0]], dtype=np.float32)
    baseline = np.exp(-np.log(2) / 2 * roads[:, 0])
    region = SimpleNamespace(
        ids=["endpoint-a", "neighbor", "endpoint-b"],
        roads=roads,
        snaps=np.zeros(3),
        market_snaps=np.zeros(1),
        city_roads=np.zeros((1, 1)),
        trunk=np.zeros((1, 1)),
        market_weights=np.ones(1),
        population=np.ones(3),
        normalization=1.0,
        baseline_times=roads,
        baseline_hansen=baseline,
        baseline_index=float(baseline.mean() * 100),
    )
    terminals = {
        0: (np.array([0.0, 2.0, 10.0]), np.array([10.0])),
        2: (np.array([10.0, 8.0, 0.0]), np.array([0.0])),
    }
    base = Mock(spec=DeltaBase)
    base.region.return_value = region
    base.terminal.side_effect = lambda node, _: terminals[node]
    result = DeltaCalculation(base).calculate("region", RoadAddition(0, 2, 1.0), None, lambda _: None)
    effects = {item.point_id: item for item in result.settlement_effects}
    assert set(effects) == {"endpoint-a", "neighbor"}
    assert effects["neighbor"].after == pytest.approx(100 * np.exp(-np.log(2) / 2 * 3))
    assert result.affected_settlements == 2
    assert result.delta == pytest.approx(sum(item.delta for item in effects.values()) / 3)
