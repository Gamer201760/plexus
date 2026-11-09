import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings


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
    settings = Settings()
    rows = json.loads((settings.data_dir / "indices.json").read_text())
    expected = next(
        row for row in rows if row["region_id"] == "93000000" and row["season"] == scenario
    )
    with TestClient(create_app(settings)) as client:
        response = client.get(
            "/api/v1/regions/93000000", params={"season": season, "network_mode": mode}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["hansen"] == expected["hansen_idx"]
    assert body["index_population_coverage"] == pytest.approx(
        expected["covered_population"] / expected["population"]
    )
    assert body["index_settlement_coverage"] == pytest.approx(
        expected["covered_settlements"] / expected["n_np"]
    )
    assert body["index_model_version"] == "hansen-frequency-v2"
    assert body["index_artifact_version"] == expected["artifact_version"]
