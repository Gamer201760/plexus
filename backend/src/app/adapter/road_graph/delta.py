from collections.abc import Callable
from time import monotonic
from typing import Any

import numpy as np

from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.delta_model import access_times
from app.domain.errors import InvalidQuery
from app.domain.road_economics import MoneyAssumptions, time_savings
from app.usecase.dto.road_graph import RoadAddition, RoadResult, SettlementEffect


def added_edge_distances(
    base: Any,
    left_origins: Any,
    right_origins: Any,
    left_targets: Any,
    right_targets: Any,
    hours: float,
    limit: float = 72.0,
) -> Any:
    forward = left_origins[:, None] + hours + right_targets[None, :]
    reverse = right_origins[:, None] + hours + left_targets[None, :]
    update = np.minimum(forward, reverse)
    update[update > limit] = np.inf
    return np.minimum(base, update)


class DeltaCalculation:
    def __init__(self, base: DeltaBase) -> None:
        self.base = base

    def calculate(
        self,
        region: str,
        addition: RoadAddition,
        money: MoneyAssumptions | None,
        progress: Callable[[int], None],
    ) -> RoadResult:
        started = monotonic()
        progress(0)
        progress(1)
        r = self.base.region(region)
        progress(2)
        if money and (
            money.origin_point_id not in r.ids or money.market_city not in r.market_names
        ):
            raise InvalidQuery(
                "Economic origin must belong to the selected region and target to a market"
            )
        before_times = r.baseline_times
        before_hansen = r.baseline_hansen
        total = float(r.population.sum())
        before = r.baseline_index
        la, ca = self.base.terminal(addition.source_node, r)
        progress(3)
        lb, cb = self.base.terminal(addition.target_node, r)
        progress(4)
        raw_roads = r.roads.astype(np.float64) - r.snaps[:, None] - r.market_snaps
        limit = np.inf if self.base.data.modern_model else 72.0
        road = added_edge_distances(raw_roads, la, lb, ca, cb, addition.travel_hours, limit)
        road = (road + r.snaps[:, None] + r.market_snaps).astype(np.float32)
        raw_cities = r.city_roads - r.market_snaps[:, None] - r.market_snaps
        city = added_edge_distances(raw_cities, ca, cb, ca, cb, addition.travel_hours, limit)
        city += r.market_snaps[:, None] + r.market_snaps
        after_times = access_times(road, city, r.trunk)
        after_hansen = np.exp(-np.log(2) / 2 * after_times.astype(np.float64)) @ r.market_weights
        after = float(after_hansen @ r.population / total / r.normalization * 100)
        effect = None
        if money:
            i, j = r.ids.index(money.origin_point_id), r.market_names.index(money.market_city)
            effect = time_savings(float(before_times[i, j]), float(after_times[i, j]), money)
        affected = int(np.count_nonzero(after_hansen > before_hansen + 1e-5))
        scale = 100.0 / r.normalization
        differences = (after_hansen - before_hansen) * scale
        order = np.argsort(-differences, kind="stable")
        effects = [
            SettlementEffect(
                r.ids[i],
                float(before_hansen[i] * scale),
                float(after_hansen[i] * scale),
                float(differences[i]),
            )
            for i in order
            if after_hansen[i] > before_hansen[i] + 1e-5
        ][:30]
        progress(5)
        return RoadResult(
            before,
            after,
            after - before,
            (after / before - 1) * 100 if before else None,
            int(total),
            len(r.ids),
            2,
            r.normalization,
            monotonic() - started,
            affected,
            effect,
            "single_edge_delta",
            effects,
        )
