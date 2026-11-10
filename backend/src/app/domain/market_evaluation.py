from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from app.domain.errors import InvalidQuery
from app.domain.market_scenario import (
    ASSUMED_FREQUENCY_PER_WEEK,
    BETA_PER_H,
    MAX_PAIR_CHANGES,
    SCHEDULED_TRUNK_MODES,
    SETTLEMENT_LINK_NOTE,
    TRUNK_OVERHEAD_H,
    WEEKLY_WAIT_H,
    CityPairChange,
    NewTrunkLink,
    RegionImpact,
    ScenarioEvaluation,
    ScenarioModel,
    SettlementImpact,
)


def finite_hours(best: NDArray[np.float32] | NDArray[np.float64]) -> NDArray[np.float64]:
    hours = best.astype(np.float64)
    hours[~np.isfinite(hours)] = np.inf
    return hours


def point_access(
    best: NDArray[np.float32], market_population: NDArray[np.float64]
) -> NDArray[np.float64]:
    result: NDArray[np.float64] = np.exp(-BETA_PER_H * finite_hours(best)) @ market_population
    return result


def population_mean(
    values: NDArray[np.float64],
    population: NDArray[np.float64],
    region_idx: NDArray[np.int32],
    regions: int,
) -> NDArray[np.float64]:
    weights = np.bincount(region_idx, weights=population, minlength=regions)
    totals = np.bincount(region_idx, weights=population * values, minlength=regions)
    result: NDArray[np.float64] = totals / weights
    return result


def link_weight(link: NewTrunkLink) -> tuple[float, tuple[str, ...]]:
    if link.mode not in TRUNK_OVERHEAD_H:
        raise InvalidQuery("Unknown trunk mode")
    if not np.isfinite(link.travel_h) or link.travel_h <= 0:
        raise InvalidQuery("Travel time must be finite and positive")
    frequency = link.frequency_per_week
    if link.mode not in SCHEDULED_TRUNK_MODES:
        if frequency is not None:
            raise InvalidQuery("Frequency requires a scheduled link")
        return float(link.travel_h), ()
    notes: tuple[str, ...] = ("uniform_headways_random_need",)
    if frequency is None:
        frequency = ASSUMED_FREQUENCY_PER_WEEK
        notes = (*notes, f"assumed_frequency:{link.from_id}-{link.to_id}:{frequency}")
    elif type(frequency) is not int or not 1 <= frequency <= 28:
        raise InvalidQuery("Frequency must be an integer from 1 to 28")
    waiting = WEEKLY_WAIT_H / frequency
    return float(link.travel_h) + waiting + TRUNK_OVERHEAD_H[link.mode], notes


@dataclass(frozen=True, slots=True)
class ResolvedLink:
    from_point: int | None
    from_city: int | None
    to_point: int | None
    to_city: int | None
    weight: float


def resolve_links(
    model: ScenarioModel, links: tuple[NewTrunkLink, ...]
) -> tuple[tuple[ResolvedLink, ...], tuple[str, ...]]:
    position = {city.id: index for index, city in enumerate(model.cities)}
    resolved = []
    notes: list[str] = []
    for link in links:
        if link.from_id == link.to_id:
            raise InvalidQuery("Link endpoints must be distinct")
        ends: list[tuple[int | None, int | None]] = []
        for identifier in (link.from_id, link.to_id):
            city = position.get(identifier)
            if city is not None:
                ends.append((None, city))
                continue
            point = model.point_index.get(identifier)
            if point is None:
                raise InvalidQuery("Unknown market city or settlement")
            ends.append((point, None))
        weight, link_notes = link_weight(link)
        notes.extend(link_notes)
        resolved.append(ResolvedLink(ends[0][0], ends[0][1], ends[1][0], ends[1][1], weight))
    if any(item.from_point is not None or item.to_point is not None for item in resolved):
        notes.append(SETTLEMENT_LINK_NOTE)
    return tuple(resolved), tuple(sorted(set(notes)))


def changed_city_matrix(
    model: ScenarioModel, links: tuple[ResolvedLink, ...]
) -> NDArray[np.float64]:
    matrix = model.city_best_h.copy()
    for link in links:
        if link.from_city is None or link.to_city is None:
            continue
        source, target = link.from_city, link.to_city
        matrix[source, target] = min(matrix[source, target], link.weight)
        matrix[target, source] = min(matrix[target, source], link.weight)
    for k in range(len(model.cities)):
        np.minimum(matrix, matrix[:, k, None] + matrix[None, k, :], out=matrix)
    return matrix


def point_rows(
    model: ScenarioModel, matrix: NDArray[np.float64], links: tuple[ResolvedLink, ...]
) -> dict[int, NDArray[np.float64]]:
    rows: dict[int, NDArray[np.float64]] = {}
    for link in links:
        for point in (link.from_point, link.to_point):
            if point is not None and point not in rows:
                rows[point] = (finite_hours(model.road_h[point])[:, None] + matrix).min(axis=0)
    settlement_links = [
        link for link in links if link.from_point is not None or link.to_point is not None
    ]
    for _ in range(len(settlement_links) + 1):
        changed = False
        for link in settlement_links:
            sides = ((link.from_point, link.from_city), (link.to_point, link.to_city))
            for (target, _), (source_point, source_city) in (sides, sides[::-1]):
                if target is None:
                    continue
                if source_point is not None:
                    source_row = rows[source_point]
                else:
                    assert source_city is not None
                    source_row = matrix[source_city]
                candidate = link.weight + source_row
                if bool((candidate < rows[target] - 1e-9).any()):
                    rows[target] = np.minimum(rows[target], candidate)
                    changed = True
        if not changed:
            break
    return rows


def pair_changes(
    model: ScenarioModel, matrix: NDArray[np.float64], improved: NDArray[np.bool_]
) -> tuple[int, tuple[CityPairChange, ...]]:
    upper = np.triu(improved, k=1)
    sources, targets = np.nonzero(upper)
    before = model.city_best_h[sources, targets]
    after = matrix[sources, targets]
    gain = np.where(np.isfinite(before), before - after, np.inf)
    order = np.argsort(-gain, kind="stable")[:MAX_PAIR_CHANGES]
    changes = tuple(
        CityPairChange(
            model.cities[int(sources[i])].id,
            model.cities[int(targets[i])].id,
            float(before[i]) if np.isfinite(before[i]) else None,
            float(after[i]),
        )
        for i in order
    )
    return len(sources), changes


def evaluate(model: ScenarioModel, links: tuple[NewTrunkLink, ...]) -> ScenarioEvaluation:
    if not links:
        raise InvalidQuery("At least one new link is required")
    resolved, notes = resolve_links(model, links)
    matrix = changed_city_matrix(model, resolved)
    improved = matrix < model.city_best_h - 1e-9
    market_population = np.array([city.population for city in model.cities], dtype=np.float64)
    access = model.point_access.copy()
    for j in np.flatnonzero(improved.any(axis=0)):
        hubs = np.flatnonzero(improved[:, j])
        candidate = np.full(len(access), np.inf)
        for start in range(0, len(hubs), 16):
            chunk = hubs[start : start + 16]
            roads = finite_hours(model.road_h[:, chunk]) + matrix[chunk, j]
            np.minimum(candidate, roads.min(axis=1), out=candidate)
        baseline_j = finite_hours(model.best_h[:, j])
        changed_j = np.minimum(baseline_j, candidate)
        access += market_population[j] * (
            np.exp(-BETA_PER_H * changed_j) - np.exp(-BETA_PER_H * baseline_j)
        )
    settlements = []
    scale = 100.0 / model.normalization_base
    rows = point_rows(model, matrix, resolved)
    point_labels = {row: name for name, row in model.point_index.items()} if rows else {}
    for point, row in rows.items():
        access[point] = float(np.exp(-BETA_PER_H * row) @ market_population)
        settlements.append(
            SettlementImpact(
                point_labels[point],
                float(model.point_access[point] * scale),
                float(access[point] * scale),
                float((access[point] - model.point_access[point]) * scale),
            )
        )
    region_access = population_mean(access, model.population, model.region_idx, len(model.regions))
    regions = tuple(
        RegionImpact(
            reference.region_id,
            reference.name,
            float(model.region_population[index]),
            float(model.region_access[index] * scale),
            float(region_access[index] * scale),
            float((region_access[index] - model.region_access[index]) * scale),
        )
        for index, reference in enumerate(model.regions)
    )
    regions = tuple(sorted(regions, key=lambda impact: -impact.delta_index))
    improved_pairs, changes = pair_changes(model, matrix, improved)
    return ScenarioEvaluation(
        model.season,
        model.model_version,
        model.artifact_version,
        links,
        notes,
        float(np.average(model.point_access, weights=model.population) * scale),
        float(np.average(access, weights=model.population) * scale),
        improved_pairs,
        changes,
        regions,
        tuple(sorted(settlements, key=lambda impact: -impact.delta_index)),
    )
