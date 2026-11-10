from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class SettlementAccess:
    point_id: str
    population: int
    index: float
    reachable: bool


@dataclass(frozen=True)
class SettlementImpact:
    point_id: str
    population: int
    before: float
    after: float
    delta: float
    newly_isolated: bool
    affected: bool


@dataclass(frozen=True)
class AnalysisEffect:
    before: float
    after: float
    delta: float
    affected_population: int
    isolated_population: int
    settlements: tuple[SettlementImpact, ...]


def compare_access(
    before: tuple[SettlementAccess, ...], after: tuple[SettlementAccess, ...]
) -> AnalysisEffect:
    left = {p.point_id: p for p in before}
    right = {p.point_id: p for p in after}
    if len(left) != len(before) or len(right) != len(after) or left.keys() != right.keys():
        raise ValueError("Settlement populations must have matching unique identifiers")
    impacts = []
    for key in sorted(left):
        a, b = left[key], right[key]
        if a.population != b.population or a.population < 0:
            raise ValueError("Population must remain fixed and nonnegative")
        if not all(isfinite(v) and v >= 0 for v in (a.index, b.index)):
            raise ValueError("Accessibility must be finite and nonnegative")
        delta = b.index - a.index
        isolated = a.reachable and not b.reachable
        affected = abs(delta) > max(1e-6, abs(a.index) * 1e-7) or isolated
        impacts.append(
            SettlementImpact(key, a.population, a.index, b.index, delta, isolated, affected)
        )
    population = sum(p.population for p in impacts)
    if population <= 0:
        raise ValueError("Population must be positive")
    baseline = sum(p.before * p.population for p in impacts) / population
    changed = sum(p.after * p.population for p in impacts) / population
    return AnalysisEffect(
        baseline,
        changed,
        changed - baseline,
        sum(p.population for p in impacts if p.affected),
        sum(p.population for p in impacts if p.newly_isolated),
        tuple(impacts),
    )
