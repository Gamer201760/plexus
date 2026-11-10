
import pytest
from fastapi.testclient import TestClient
from tests.storage import atlas_repository
from tests.storage import settings as storage_settings

from app.main import create_app


@pytest.mark.parametrize(
    ("season", "mode", "scenario"),
    [
        ("all", "road", "road"),
        ("summer", "road", "road_summer"),
        ("winter", "road", "road_winter"),
        ("summer", "multimodal", "summer"),
        ("winter", "multimodal", "winter"),
    ],
)
def test_api_selects_exported_scenario_and_coverage(
    season: str, mode: str, scenario: str
) -> None:
    settings = storage_settings()
    rows = atlas_repository().indices()
    if mode == "road" and any(row.model_version == "hansen-release-20261107" for row in rows):
        scenario = "road"
    expected = next(
        row for row in rows if row.region_id == "93000000" and row.scenario == scenario
    )
    with TestClient(create_app(settings)) as client:
        response = client.get(
            "/api/v1/regions/93000000", params={"season": season, "network_mode": mode}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["hansen"] == expected.hansen
    assert body["index_population_coverage"] == pytest.approx(
        (expected.covered_population or 0) / (expected.total_population or 1)
    )
    assert body["index_settlement_coverage"] == pytest.approx(
        (expected.covered_settlements or 0) / (expected.total_settlements or 1)
    )
    assert body["index_model_version"] == expected.model_version
    assert body["index_artifact_version"] == expected.artifact_version
