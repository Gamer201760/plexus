from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from app.domain.errors import InvalidQuery

BETA_PER_H = float(np.log(2.0) / 2.0)
TRUNK_OVERHEAD_H = {"air": 2.5, "rail": 1.0, "road": 0.0}
SCHEDULED_TRUNK_MODES = frozenset({"air", "rail"})
WEEKLY_WAIT_H = 84.0
ASSUMED_FREQUENCY_PER_WEEK = 1
MAX_PAIR_CHANGES = 30


@dataclass(frozen=True, slots=True)
class MarketCity:
    id: str
    region: str
    population: float
    latitude: float
    longitude: float
    is_capital: bool


@dataclass(frozen=True, slots=True)
class ScenarioRegion:
    region_id: str
    name: str


@dataclass(frozen=True, slots=True)
class ScenarioCatalog:
    model_version: str
    artifact_version: str
    seasons: tuple[str, ...]
    cities: tuple[MarketCity, ...]
    regions: tuple[ScenarioRegion, ...]
    assumptions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScenarioModel:
    season: str
    model_version: str
    artifact_version: str
    normalization_base: float
    cities: tuple[MarketCity, ...]
    regions: tuple[ScenarioRegion, ...]
    road_h: NDArray[np.float32]
    best_h: NDArray[np.float32]
    city_best_h: NDArray[np.float64]
    population: NDArray[np.float64]
    region_idx: NDArray[np.int32]
    point_access: NDArray[np.float64]
    region_access: NDArray[np.float64]
    region_population: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class NewTrunkLink:
    from_city: str
    to_city: str
    mode: str
    travel_h: float
    frequency_per_week: int | None = None


@dataclass(frozen=True, slots=True)
class CityPairChange:
    from_city: str
    to_city: str
    baseline_h: float | None
    changed_h: float


@dataclass(frozen=True, slots=True)
class RegionImpact:
    region_id: str
    name: str
    population: float
    baseline_index: float
    changed_index: float
    delta_index: float


@dataclass(frozen=True, slots=True)
class ScenarioEvaluation:
    season: str
    model_version: str
    artifact_version: str
    links: tuple[NewTrunkLink, ...]
    assumptions: tuple[str, ...]
    national_baseline_index: float
    national_changed_index: float
    improved_city_pairs: int
    city_pairs: tuple[CityPairChange, ...]
    regions: tuple[RegionImpact, ...]


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
        notes = (*notes, f"assumed_frequency:{link.from_city}-{link.to_city}:{frequency}")
    elif type(frequency) is not int or not 1 <= frequency <= 28:
        raise InvalidQuery("Frequency must be an integer from 1 to 28")
    waiting = WEEKLY_WAIT_H / frequency
    return float(link.travel_h) + waiting + TRUNK_OVERHEAD_H[link.mode], notes


def changed_city_matrix(
    model: ScenarioModel, links: tuple[NewTrunkLink, ...]
) -> tuple[NDArray[np.float64], tuple[str, ...]]:
    position = {city.id: index for index, city in enumerate(model.cities)}
    matrix = model.city_best_h.copy()
    notes: list[str] = []
    for link in links:
        source, target = position.get(link.from_city), position.get(link.to_city)
        if source is None or target is None:
            raise InvalidQuery("Unknown market city")
        if source == target:
            raise InvalidQuery("Link endpoints must be distinct market cities")
        weight, link_notes = link_weight(link)
        matrix[source, target] = min(matrix[source, target], weight)
        matrix[target, source] = min(matrix[target, source], weight)
        notes.extend(link_notes)
    for k in range(len(model.cities)):
        np.minimum(matrix, matrix[:, k, None] + matrix[None, k, :], out=matrix)
    return matrix, tuple(sorted(set(notes)))


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
    matrix, notes = changed_city_matrix(model, links)
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
    scale = 100.0 / model.normalization_base
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
    )
