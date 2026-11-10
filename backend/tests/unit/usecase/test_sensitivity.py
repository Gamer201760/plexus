import math

import pytest

from app.domain.errors import RegionNotFound
from app.domain.transport import NetworkMode, Season
from app.repository.files.atlas import JsonAtlasRepository
from app.settings import DEFAULT_DATA_DIR
from app.usecase.dto import IndexRecord
from app.usecase.sensitivity import AccessibilitySensitivity


def test_sensitivity_matches_independent_od_recalculation(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = JsonAtlasRepository(DEFAULT_DATA_DIR)
    times = ((0.0, 3.0), (2.0, 5.0))
    origins = (100.0, 200.0)
    markets = (1000.0, 2000.0)
    normalization = 1234.0

    def raw(scale: float) -> float:
        return sum(weight * sum(mass * 2 ** (-scale * time / 2)
                                for time, mass in zip(row, markets, strict=True))
                   for row, weight in zip(times, origins, strict=True)) / sum(origins)

    index = IndexRecord("18000000", "road_summer", raw(1) / normalization * 100,
                        hansen_1h=raw(2), hansen_2h=raw(1), hansen_4h=raw(0.5))
    monkeypatch.setattr(repository, "indices", lambda: [index])
    result = AccessibilitySensitivity(repository).evaluate("18000000", Season.SUMMER,
                                                           NetworkMode.ROAD)
    for point in result.points:
        assert math.isclose(point.hansen, raw(point.time_multiplier) / normalization * 100)
    assert not result.graph_recomputed
    assert result.points[0].hansen > result.baseline > result.points[2].hansen


def test_real_regional_baseline_matches_published_index() -> None:
    service = AccessibilitySensitivity(JsonAtlasRepository(DEFAULT_DATA_DIR))
    result = service.evaluate("18000000", Season.SUMMER, NetworkMode.ROAD)
    assert result.baseline == pytest.approx(61.55079117766899)
    assert result.points[1].hansen == pytest.approx(result.baseline)
    assert result.artifact_version
    with pytest.raises(RegionNotFound):
        service.evaluate("unknown", Season.SUMMER, NetworkMode.ROAD)
