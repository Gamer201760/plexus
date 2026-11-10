from app.adapter.road_corridor.blocks import corridor_pairs


def test_both_parallel_carriageways_are_kept_but_side_loop_is_not() -> None:
    pairs = [(0, 1), (1, 3), (0, 2), (2, 3), (1, 4), (4, 5), (5, 1), (3, 6)]
    assert corridor_pairs(pairs, 0, 3) == {(0, 1), (1, 3), (0, 2), (2, 3)}


def test_disconnected_endpoints_do_not_create_partial_closure() -> None:
    assert not corridor_pairs([(0, 1), (2, 3)], 0, 3)


def test_chain_keeps_whole_topological_path() -> None:
    assert corridor_pairs([(0, 1), (1, 2), (1, 4), (2, 3)], 0, 3) == {(0, 1), (1, 2), (2, 3)}
