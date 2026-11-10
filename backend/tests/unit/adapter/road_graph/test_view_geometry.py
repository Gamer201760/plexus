from itertools import pairwise

from app.adapter.road_graph.view_geometry import chains


def represented_edges(paths: list[list[int]]) -> set[tuple[int, int]]:
    return {(min(a, b), max(a, b)) for path in paths for a, b in pairwise(path)}


def test_join_preserves_branches_cycles_and_disconnected_parts() -> None:
    edges = {(0, 1), (1, 2), (2, 3), (2, 4), (5, 6), (6, 7), (5, 7), (8, 9)}
    paths = list(chains(edges))
    assert represented_edges(paths) == edges
    assert sum(len(path) - 1 for path in paths) == len(edges)
    assert len(paths) == 5


def test_long_chain_becomes_one_feature_without_losing_vertices() -> None:
    edges = {(i, i + 1) for i in range(1000)}
    paths = list(chains(edges))
    assert len(paths) == 1
    assert len(paths[0]) == 1001
    assert represented_edges(paths) == edges


def test_loop_and_empty_graph_terminate() -> None:
    assert list(chains(set())) == []
    assert list(chains({(1, 1)})) == [[1, 1]]
