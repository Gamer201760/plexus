from typing import Any

import numpy as np
from scipy.sparse.csgraph import floyd_warshall


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
