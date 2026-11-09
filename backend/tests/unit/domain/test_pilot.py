import itertools
from dataclasses import replace

import pytest

from app.domain.errors import InvalidQuery
from app.domain.pilot import EdgeChange, Pilot, PilotEdge, PilotPair
from app.domain.pilot_routing import changed_edges, route
from app.domain.waiting import periodic_wait


def edge(
    identifier: str,
    source: str,
    target: str,
    hours: float,
    mode: str = "road",
    frequency: float | None = None,
) -> PilotEdge:
    return PilotEdge(
        identifier,
        source,
        target,
        mode,
        ("summer", "winter"),
        hours,
        frequency,
        None,
        "https://example.com/control",
        None,
        (),
    )


def pilot(edges: tuple[PilotEdge, ...]) -> Pilot:
    return Pilot("control", "Control", "v1", "hash", (), edges, (PilotPair("trip", "a", "c"),), ())


def test_frequency_variants_use_actual_route_and_separate_waiting() -> None:
    graph = pilot((edge("flight", "a", "c", 2.0, "air", 2.0),))
    pair = graph.pairs[0]
    baseline = route(graph.edges, pair, "summer")
    assert baseline.total_h == 44.0
    assert baseline.travel_h == 2.0
    assert baseline.waiting_h == 42.0
    for frequency, expected in ((4, 23.0), (7, 14.0)):
        modified = changed_edges(graph, (EdgeChange("flight", frequency_per_week=frequency),))
        result = route(modified, pair, "summer")
        assert result.total_h == expected
        assert result.edge_ids == ("flight",)
        assert result.point_ids == ("a", "c")
        assert result.total_h < baseline.total_h
    assert graph.edges[0].frequency_per_week == 2.0
    assert route(graph.edges, pair, "summer", False).total_h == 2.0


def test_closure_searches_alternative_and_season_filter_precedes_search() -> None:
    seasonal = replace(edge("winter", "a", "c", 1.0), seasons=("winter",))
    graph = pilot((edge("ab", "a", "b", 2.0), edge("bc", "b", "c", 3.0), seasonal))
    assert route(graph.edges, graph.pairs[0], "summer").total_h == 5.0
    assert route(graph.edges, graph.pairs[0], "winter").total_h == 1.0
    modified = changed_edges(graph, (EdgeChange("winter", enabled=False),))
    result = route(modified, graph.pairs[0], "winter")
    assert result.total_h == 5.0
    assert result.edge_ids == ("ab", "bc")
    assert len(graph.edges) == 3


def test_unknown_no_route_and_zero_are_distinct() -> None:
    pair = PilotPair("trip", "a", "c")
    assert route((), pair, "summer").status == "no_route"
    unknown = edge("flight", "a", "c", 2.0, "air")
    assert route((unknown,), pair, "summer").status == "insufficient_data"
    assumed = replace(unknown, assumed_frequency_per_week=1.0)
    result = route((assumed,), pair, "summer")
    assert result.total_h == 86.0
    assert "assumed_frequency:flight:1.0" in result.assumptions
    zero = route((), PilotPair("same", "a", "a"), "summer")
    assert zero.status == "found"
    assert zero.total_h == 0.0


@pytest.mark.parametrize("frequency", [0, 29, True, 1.5])
def test_domain_rejects_invalid_frequency(frequency: int) -> None:
    graph = pilot((edge("flight", "a", "c", 2.0, "air", 2.0),))
    with pytest.raises(InvalidQuery):
        changed_edges(graph, (EdgeChange("flight", frequency_per_week=frequency),))


def test_domain_rejects_unknown_repeated_and_noneditable_edges() -> None:
    graph = pilot((replace(edge("road", "a", "c", 2.0), editable=False),))
    for changes in ((EdgeChange("missing"),), (EdgeChange("road", enabled=False),)):
        with pytest.raises(InvalidQuery):
            changed_edges(graph, changes)
    graph = pilot((edge("road", "a", "c", 2.0),))
    with pytest.raises(InvalidQuery):
        changed_edges(graph, (EdgeChange("road"), EdgeChange("road")))
    with pytest.raises(InvalidQuery):
        changed_edges(graph, (EdgeChange("road", frequency_per_week=3),))


def test_optimum_matches_independent_simple_path_enumeration() -> None:
    graph = pilot(
        (
            edge("ab", "a", "b", 2.0),
            edge("bc", "b", "c", 3.0),
            edge("ad", "a", "d", 1.0),
            edge("dc", "d", "c", 8.0),
            edge("bd", "b", "d", 1.0),
        )
    )
    for disabled in (None, "ab", "bc", "ad", "dc", "bd"):
        edges = tuple(item for item in graph.edges if item.id != disabled)
        weights = {(item.from_id, item.to_id): item.travel_h for item in edges}
        weights.update({(b, a): weight for (a, b), weight in list(weights.items())})
        costs = []
        for count in range(3):
            for intermediate in itertools.permutations(("b", "d"), count):
                path = ("a", *intermediate, "c")
                segments = list(itertools.pairwise(path))
                if all(segment in weights for segment in segments):
                    costs.append(sum(weights[segment] for segment in segments))
        assert route(edges, graph.pairs[0], "summer").total_h == min(costs)
        assert min(costs) >= 5.0


def test_known_route_reports_incomplete_unknown_alternatives() -> None:
    graph = (edge("road", "a", "c", 10.0), edge("flight", "a", "c", 1.0, "air"))
    result = route(graph, PilotPair("trip", "a", "c"), "summer")
    assert result.status == "found"
    assert result.total_h == 10.0
    assert result.optimality == "incomplete_alternatives"
    assert "unknown_frequency_alternatives" in result.warnings


def test_out_of_range_source_frequency_is_preserved_and_noneditable() -> None:
    graph = pilot((edge("flight", "a", "c", 2.0, "air", 35.0),))
    assert route(graph.edges, graph.pairs[0], "summer").total_h == pytest.approx(4.4)
    for change in (EdgeChange("flight", enabled=False), EdgeChange("flight", frequency_per_week=7)):
        with pytest.raises(InvalidQuery):
            changed_edges(graph, (change,))
    assert graph.edges[0].frequency_per_week == 35.0


def test_irregular_schedule_wait_is_a_separate_control() -> None:
    assert periodic_wait((48.0, 120.0)) == pytest.approx(49.714285714285715)
    assert periodic_wait((84.0, 84.0)) == 42.0
    for intervals in ((), (48.0,), (0.0, 168.0), (-1.0, 169.0)):
        with pytest.raises(InvalidQuery):
            periodic_wait(intervals)
    flight = replace(edge("flight", "a", "c", 2.0, "air", 2.0), headway_intervals_h=(48.0, 120.0))
    baseline = route((flight,), PilotPair("trip", "a", "c"), "summer")
    assert baseline.waiting_h == 42.0
    assert "known_schedule_approximated" in baseline.assumptions
