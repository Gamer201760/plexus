from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.sparse.csgraph import floyd_warshall


@dataclass
class DeltaRegion:
    ids: list[str]
    nodes: Any
    snaps: Any
    population: Any
    roads: Any
    city_roads: Any
    trunk: Any
    market_nodes: Any
    market_snaps: Any
    market_weights: Any
    market_names: list[str]
    normalization: float
    expected: float
    baseline_times: Any = None
    baseline_hansen: Any = None
    baseline_index: float = 0.0


def access_times(roads: Any, city_roads: Any, trunk: Any) -> Any:
    connections = np.minimum(city_roads, trunk)
    np.fill_diagonal(connections, 0.0)
    transfers = floyd_warshall(connections)
    return np.stack(
        [
            np.min(roads + transfers[:, j].astype(np.float32), axis=1)
            for j in range(len(connections))
        ],
        axis=1,
    )
