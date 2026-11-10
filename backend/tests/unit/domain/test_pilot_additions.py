import pytest

from app.domain.errors import InvalidQuery
from app.domain.pilot import NewLink, Pilot, PilotEdge, PilotPair, PilotPoint
from app.domain.pilot_routing import added_edges, route


def edge(identifier: str, source: str, target: str, hours: float) -> PilotEdge:
    return PilotEdge(
        identifier,
        source,
        target,
        "road",
        ("summer", "winter"),
        hours,
        None,
        None,
        "https://example.com/control",
        None,
        (),
    )


def pilot() -> Pilot:
    points = tuple(PilotPoint(name, name.upper(), 51.0, 94.0) for name in ("a", "b", "c"))
    edges = (edge("ab", "a", "b", 2.0), edge("bc", "b", "c", 3.0))
    return Pilot(
        "control", "Control", "v1", "hash", points, edges, (PilotPair("trip", "a", "c"),), ()
    )


def test_added_road_link_shortens_route_and_keeps_baseline() -> None:
    graph = pilot()
    link = NewLink("a", "c", "road", 1.5, ("summer",))
    modified = graph.edges + added_edges(graph, (link,))
    result = route(modified, graph.pairs[0], "summer")
    assert result.total_h == 1.5
    assert result.edge_ids == ("added:0",)
    assert "user_added_link:added:0" in result.assumptions
    assert route(modified, graph.pairs[0], "winter").total_h == 5.0
    assert route(graph.edges, graph.pairs[0], "summer").total_h == 5.0


def test_added_air_link_includes_waiting_from_frequency() -> None:
    graph = pilot()
    link = NewLink("a", "c", "air", 1.0, ("summer", "winter"), 7)
    modified = graph.edges + added_edges(graph, (link,))
    result = route(modified, graph.pairs[0], "summer")
    assert result.total_h == 5.0
    assert result.edge_ids == ("ab", "bc")
    faster = NewLink("a", "c", "air", 1.0, ("summer",), 28)
    result = route(graph.edges + added_edges(graph, (faster,)), graph.pairs[0], "summer")
    assert result.total_h == 4.0
    assert result.waiting_h == 3.0


def test_added_one_way_link_is_directional() -> None:
    graph = pilot()
    link = NewLink("c", "a", "road", 1.0, ("summer",), bidirectional=False)
    modified = graph.edges + added_edges(graph, (link,))
    assert route(modified, graph.pairs[0], "summer").total_h == 5.0


@pytest.mark.parametrize(
    "link",
    [
        NewLink("a", "x", "road", 1.0, ("summer",)),
        NewLink("a", "a", "road", 1.0, ("summer",)),
        NewLink("a", "c", "teleport", 1.0, ("summer",)),
        NewLink("a", "c", "road", 0.0, ("summer",)),
        NewLink("a", "c", "road", float("inf"), ("summer",)),
        NewLink("a", "c", "road", 1.0, ()),
        NewLink("a", "c", "road", 1.0, ("spring",)),
        NewLink("a", "c", "air", 1.0, ("summer",)),
        NewLink("a", "c", "air", 1.0, ("summer",), 0),
        NewLink("a", "c", "air", 1.0, ("summer",), 29),
        NewLink("a", "c", "road", 1.0, ("summer",), 7),
    ],
)
def test_invalid_addition_is_rejected(link: NewLink) -> None:
    with pytest.raises(InvalidQuery):
        added_edges(pilot(), (link,))
