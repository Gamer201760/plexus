from collections import defaultdict
from collections.abc import Iterator
from typing import Any

import numpy as np

from app.usecase.road_graph import RoadSegment


def chains(edges: set[tuple[int, int]]) -> Iterator[list[int]]:
    neighbors: dict[int, set[int]] = defaultdict(set)
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    remaining = edges.copy()

    def walk(start: int, following: int) -> list[int]:
        path = [start, following]
        remaining.discard((min(start, following), max(start, following)))
        previous, current = start, following
        while len(neighbors[current]) == 2:
            candidate = next(node for node in neighbors[current] if node != previous)
            edge = (min(current, candidate), max(current, candidate))
            if edge not in remaining:
                break
            remaining.remove(edge)
            path.append(candidate)
            previous, current = current, candidate
        return path

    for node, adjacent in neighbors.items():
        if len(adjacent) == 2:
            continue
        for following in adjacent:
            if (min(node, following), max(node, following)) in remaining:
                yield walk(node, following)
    while remaining:
        a, b = next(iter(remaining))
        yield walk(a, b)


def road_segments(
    positions: Any,
    edges: dict[str, Any],
    nodes: dict[str, Any],
    ways: dict[int, dict[str, Any]],
) -> list[RoadSegment]:
    grouped: dict[int, set[tuple[int, int]]] = defaultdict(set)
    for a, b, w in zip(
        edges["src"][positions].tolist(),
        edges["dst"][positions].tolist(),
        edges["way_idx"][positions].tolist(),
        strict=True,
    ):
        grouped[w].add((min(a, b), max(a, b)))
    segments = []
    for way_idx, pairs in grouped.items():
        for path in chains(pairs):
            coordinates = np.column_stack((nodes["lon"][path], nodes["lat"][path])).tolist()
            segments.append(
                RoadSegment(
                    **ways[way_idx],
                    source_node=path[0],
                    target_node=path[-1],
                    coordinates=coordinates,
                )
            )
    return segments
