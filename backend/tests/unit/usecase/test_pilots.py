from dataclasses import replace

import pytest

from app.domain.errors import InvalidQuery
from app.domain.pilot import EdgeChange, Pilot, PilotEdge, PilotPair
from app.usecase.pilots import PilotQueries, StalePilotVersion


class StoredPilot:
    def __init__(self) -> None:
        flight = PilotEdge(
            "flight",
            "a",
            "b",
            "air",
            ("summer", "winter"),
            2.0,
            2.0,
            None,
            "https://example.com/control",
            "2025",
            (),
            headway_intervals_h=(48.0, 120.0),
        )
        self.value = Pilot(
            "control",
            "Control",
            "v1",
            "hash1",
            (),
            (flight,),
            (PilotPair("trip", "a", "b"),),
            ("independent_transfer_waits",),
        )

    def get(self, pilot_id: str) -> Pilot:
        assert pilot_id == "control"
        return self.value

    def list(self) -> tuple[Pilot, ...]:
        return (self.value,)


def test_evaluation_compares_same_frequency_model_and_reports_schedule_sensitivity() -> None:
    repository = StoredPilot()
    query = PilotQueries(repository)
    result = query.evaluate(
        "control", "summer", "v1", "hash1", (EdgeChange("flight", frequency_per_week=4),)
    )
    assert result.pairs[0].baseline.total_h == 44.0
    assert result.pairs[0].changed.total_h == 23.0
    assert result.pairs[0].delta_h == -21.0
    assert result.waiting_sensitivity[0].periodic_wait_h == pytest.approx(49.714285714285715)
    assert result.waiting_sensitivity[0].uniform_wait_h == 42.0
    assert query.evaluate("control", "summer", "v1", "hash1", result.changes) == result
    assert repository.value.edges[0].frequency_per_week == 2.0


@pytest.mark.parametrize(("model", "artifact"), [("v0", "hash1"), ("v1", "hash0")])
def test_evaluation_rejects_stale_model_or_artifact(model: str, artifact: str) -> None:
    query = PilotQueries(StoredPilot())
    with pytest.raises(StalePilotVersion):
        query.evaluate("control", "summer", model, artifact, ())


def test_no_route_delta_is_not_invented_and_season_is_validated() -> None:
    repository = StoredPilot()
    query = PilotQueries(repository)
    result = query.evaluate("control", "summer", "v1", "hash1", (EdgeChange("flight", False),))
    assert result.pairs[0].changed.status == "no_route"
    assert result.pairs[0].delta_h is None
    repository.value = replace(repository.value, edges=())
    with pytest.raises(InvalidQuery):
        query.evaluate("control", "spring", "v1", "hash1", ())
