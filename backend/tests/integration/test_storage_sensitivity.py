import pytest
from tests.storage import atlas_repository

from app.domain.errors import RegionNotFound
from app.domain.transport import NetworkMode, Season
from app.usecase.sensitivity import AccessibilitySensitivity


def test_real_regional_baseline_matches_published_index() -> None:
    service = AccessibilitySensitivity(atlas_repository())
    result = service.evaluate("18000000", Season.SUMMER, NetworkMode.ROAD)
    expected = next(r.hansen for r in atlas_repository().indices() if r.region_id == "18000000" and r.scenario == "road")
    assert result.baseline == pytest.approx(expected)
    assert result.points[1].hansen == pytest.approx(result.baseline)
    assert result.artifact_version
    with pytest.raises(RegionNotFound):
        service.evaluate("unknown", Season.SUMMER, NetworkMode.ROAD)
