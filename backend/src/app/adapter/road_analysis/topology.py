from collections.abc import Callable
from typing import Any

import numpy as np
from scipy.sparse.csgraph import depth_first_order


def bridge_exposure(
    graph: Any, markets: Any, nodes: Any, populations: Any, progress: Callable[[], None]
) -> dict[tuple[int, int], float]:
    seen = np.zeros(graph.shape[0], dtype=bool)
    result: dict[tuple[int, int], float] = {}
    for root in markets:
        if seen[root]:
            continue
        progress()
        order, parents = depth_first_order(graph, int(root), directed=False)
        seen[order] = True
        rank = np.full(graph.shape[0], -1, dtype=np.int32)
        rank[order] = np.arange(len(order), dtype=np.int32)
        low = rank.copy()
        weight = np.zeros(graph.shape[0])
        valid = nodes >= 0
        np.add.at(weight, nodes[valid], populations[valid])
        targets = np.zeros(graph.shape[0], dtype=np.int32)
        targets[markets] = 1
        for offset, v in enumerate(order[::-1]):
            parent = int(parents[v])
            neighbors = graph.indices[graph.indptr[v] : graph.indptr[v + 1]]
            back = neighbors[(neighbors != parent) & (rank[neighbors] >= 0)]
            if len(back):
                low[v] = min(low[v], int(rank[back].min()))
            if parent >= 0:
                if low[v] > rank[parent] and targets[v] == 0 and weight[v] > 0:
                    result[(min(int(v), parent), max(int(v), parent))] = float(weight[v])
                low[parent] = min(low[parent], low[v])
                weight[parent] += weight[v]
                targets[parent] += targets[v]
            if offset % 100000 == 0:
                progress()
    return result
