import heapq
import math
from dataclasses import replace

from app.domain.errors import InvalidQuery
from app.domain.pilot import EdgeChange, Pilot, PilotEdge, PilotPair, PilotRoute

SCHEDULED_MODES = {"air", "river", "scheduled_ferry", "rail"}


def changed_edges(pilot: Pilot, changes: tuple[EdgeChange, ...]) -> tuple[PilotEdge, ...]:
    known = {edge.id: edge for edge in pilot.edges}
    selected: dict[str, EdgeChange] = {}
    for change in changes:
        edge = known.get(change.edge_id)
        if edge is None or not edge.editable or change.edge_id in selected:
            raise InvalidQuery("Unknown, repeated or noneditable link")
        if edge.frequency_per_week is not None and not 1 <= edge.frequency_per_week <= 28:
            raise InvalidQuery("Source frequency is outside the editable range")
        frequency = change.frequency_per_week
        if frequency is not None:
            if type(frequency) is not int or not 1 <= frequency <= 28:
                raise InvalidQuery("Frequency must be an integer from 1 to 28")
            if edge.mode not in SCHEDULED_MODES:
                raise InvalidQuery("Frequency requires a scheduled link")
        if change.enabled is not None and type(change.enabled) is not bool:
            raise InvalidQuery("Enabled must be boolean")
        selected[change.edge_id] = change
    result = []
    for edge in pilot.edges:
        override = selected.get(edge.id)
        if override is not None:
            if override.enabled is False:
                continue
            if override.frequency_per_week is not None:
                edge = replace(
                    edge,
                    frequency_per_week=float(override.frequency_per_week),
                    assumed_frequency_per_week=None,
                    headway_intervals_h=(),
                    assumptions=(
                        *edge.assumptions,
                        f"scenario_frequency:{edge.id}:{override.frequency_per_week}",
                    ),
                )
        result.append(edge)
    return tuple(result)


def route(
    edges: tuple[PilotEdge, ...], pair: PilotPair, season: str, include_wait: bool = True
) -> PilotRoute:
    adjacency: dict[str, list[tuple[str, PilotEdge, float, tuple[str, ...]]]] = {}
    for edge in edges:
        if season not in edge.seasons:
            continue
        if not math.isfinite(edge.travel_h) or edge.travel_h < 0:
            raise InvalidQuery("Stored travel time must be finite and nonnegative")
        waiting = 0.0
        assumptions = edge.assumptions
        if include_wait and edge.mode in SCHEDULED_MODES:
            frequency = edge.frequency_per_week
            if frequency is None:
                frequency = edge.assumed_frequency_per_week
                if frequency is not None:
                    assumptions = (*assumptions, f"assumed_frequency:{edge.id}:{frequency}")
            if frequency is None:
                continue
            if not math.isfinite(frequency) or frequency <= 0:
                raise InvalidQuery("Stored frequency must be finite and positive")
            waiting = 84 / frequency
            assumptions = (*assumptions, "uniform_headways_random_need")
            if edge.headway_intervals_h:
                assumptions = (*assumptions, "known_schedule_approximated")
        adjacency.setdefault(edge.from_id, []).append((edge.to_id, edge, waiting, assumptions))
        if edge.bidirectional:
            adjacency.setdefault(edge.to_id, []).append((edge.from_id, edge, waiting, assumptions))
    distance = {pair.from_id: 0.0}
    previous: dict[str, tuple[str, PilotEdge, float, tuple[str, ...]]] = {}
    pending = [(0.0, pair.from_id)]
    while pending:
        total, point = heapq.heappop(pending)
        if total != distance[point]:
            continue
        if point == pair.to_id:
            break
        for target, edge, waiting, assumptions in adjacency.get(point, []):
            candidate = total + edge.travel_h + waiting
            if candidate < distance.get(target, math.inf):
                distance[target] = candidate
                previous[target] = point, edge, waiting, assumptions
                heapq.heappush(pending, (candidate, target))
    if pair.to_id not in distance:
        status = "no_route"
        if include_wait and route(edges, pair, season, False).status == "found":
            status = "insufficient_data"
        return PilotRoute(status, None, None, None, (), (), ())
    edge_ids: list[str] = []
    points = [pair.to_id]
    notes: list[str] = []
    travel, waiting_total = 0.0, 0.0
    current = pair.to_id
    while current != pair.from_id:
        source, edge, waiting, assumptions = previous[current]
        edge_ids.append(edge.id)
        points.append(source)
        travel += edge.travel_h
        waiting_total += waiting
        notes.extend(assumptions)
        current = source
    warnings = unknown_alternatives(edges, pair, season, distance[pair.to_id])
    return PilotRoute(
        "found",
        distance[pair.to_id],
        travel,
        waiting_total,
        tuple(reversed(edge_ids)),
        tuple(reversed(points)),
        tuple(sorted(set(notes))),
        warnings,
        "incomplete_alternatives" if warnings else "within_model",
    )


def unknown_alternatives(
    edges: tuple[PilotEdge, ...], pair: PilotPair, season: str, known_total: float
) -> tuple[str, ...]:
    adjacency: dict[str, list[tuple[str, float]]] = {}
    for edge in edges:
        if season not in edge.seasons:
            continue
        weight = edge.travel_h
        if edge.mode in SCHEDULED_MODES and edge.frequency_per_week is not None:
            weight += 84 / edge.frequency_per_week
        adjacency.setdefault(edge.from_id, []).append((edge.to_id, weight))
        if edge.bidirectional:
            adjacency.setdefault(edge.to_id, []).append((edge.from_id, weight))
    distance = {pair.from_id: 0.0}
    pending = [(0.0, pair.from_id)]
    while pending:
        total, point = heapq.heappop(pending)
        if total != distance[point]:
            continue
        if point == pair.to_id:
            if total < known_total - 1e-9:
                return ("unknown_frequency_alternatives",)
            return ()
        for target, weight in adjacency.get(point, []):
            candidate = total + weight
            if candidate < distance.get(target, math.inf):
                distance[target] = candidate
                heapq.heappush(pending, (candidate, target))
    return ()
