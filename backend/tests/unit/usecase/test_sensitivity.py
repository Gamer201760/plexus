import math

import pytest
from tests.unit.usecase.test_atlas_usecases import FakeAtlas

from app.domain.transport import NetworkMode, Season
from app.usecase.dto.atlas import IndexRecord, RegionRecord
from app.usecase.sensitivity import AccessibilitySensitivity


def test_sensitivity_matches_independent_od_recalculation(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = FakeAtlas(region_rows=[RegionRecord("18000000", "Region", 1, 10)])
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
