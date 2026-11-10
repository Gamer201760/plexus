from typing import Protocol

from app.domain.errors import DomainError, InvalidQuery
from app.domain.pilot import EdgeChange, PairComparison, Pilot, PilotEvaluation, WaitingSensitivity
from app.domain.pilot_routing import changed_edges, route
from app.domain.waiting import periodic_wait


class PilotNotFound(DomainError):
    code = "pilot_not_found"
    message = "Pilot not found"


class StalePilotVersion(DomainError):
    code = "stale_pilot_version"
    message = "Reload the current pilot version"


class PilotRepository(Protocol):
    def list(self) -> tuple[Pilot, ...]: ...

    def get(self, pilot_id: str) -> Pilot: ...


class PilotQueries:
    def __init__(self, repository: PilotRepository) -> None:
        self._repository = repository

    def list(self) -> tuple[Pilot, ...]:
        return self._repository.list()

    def get(self, pilot_id: str) -> Pilot:
        return self._repository.get(pilot_id)

    def evaluate(
        self,
        pilot_id: str,
        season: str,
        model_version: str,
        artifact_version: str,
        changes: tuple[EdgeChange, ...],
    ) -> PilotEvaluation:
        if season not in {"summer", "winter"}:
            raise InvalidQuery("Season must be summer or winter")
        pilot = self._repository.get(pilot_id)
        if model_version != pilot.model_version or artifact_version != pilot.artifact_version:
            raise StalePilotVersion()
        modified = changed_edges(pilot, changes)
        comparisons = []
        for pair in pilot.pairs:
            baseline = route(pilot.edges, pair, season)
            changed = route(modified, pair, season)
            delta = None
            if baseline.total_h is not None and changed.total_h is not None:
                delta = changed.total_h - baseline.total_h
            comparisons.append(
                PairComparison(
                    pair.id,
                    baseline,
                    changed,
                    route(pilot.edges, pair, season, False),
                    route(modified, pair, season, False),
                    delta,
                )
            )
        sensitivity = []
        for edge in pilot.edges:
            if edge.headway_intervals_h:
                scheduled = periodic_wait(edge.headway_intervals_h)
                frequency = edge.frequency_per_week
                uniform = 84 / frequency if frequency is not None and frequency > 0 else None
                sensitivity.append(
                    WaitingSensitivity(
                        edge.id,
                        edge.headway_intervals_h,
                        scheduled,
                        uniform,
                        scheduled - uniform if uniform is not None else None,
                    )
                )
        return PilotEvaluation(
            pilot.id,
            season,
            pilot.model_version,
            pilot.artifact_version,
            changes,
            tuple(comparisons),
            pilot.assumptions,
            tuple(sensitivity),
        )
