import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repository.files.scenario import FilesScenarioRepository
from app.settings import Settings

DATA = Path(__file__).resolve().parents[4] / "frontend" / "atlas" / "public"


def write_artifact(target: Path) -> None:
    road = np.array([[1.0, np.inf], [np.inf, 2.0], [4.0, 5.0]], dtype=np.float32)
    city = np.array([[0.0, 30.0], [30.0, 0.0]])
    best = (road[:, :, None].astype(np.float64) + city[None, :, :]).min(axis=1)
    for season in ("road", "summer"):
        directory = target / season
        directory.mkdir(parents=True)
        np.save(directory / "road_h.npy", road)
        np.save(directory / "best_h.npy", best.astype(np.float32))
        np.save(directory / "city_best_h.npy", city)
        np.save(directory / "population.npy", np.array([10.0, 20.0, 5.0]))
        np.save(directory / "region_idx.npy", np.array([0, 1, 1], dtype=np.int32))
    manifest = {
        "schema_version": 1,
        "model_version": "model-v1",
        "artifact_version": "artifact-1",
        "normalization_base": 1000.0,
        "assumptions": ["uniform_headways_random_need"],
        "seasons": {"road": {"points": 3}, "summer": {"points": 3}},
        "cities": [
            {
                "city": "X",
                "region": "Alpha",
                "population": 1000.0,
                "lat": 50.0,
                "lon": 40.0,
                "is_capital": True,
            },
            {
                "city": "Y",
                "region": "Beta",
                "population": 500.0,
                "lat": 51.0,
                "lon": 41.0,
                "is_capital": False,
            },
        ],
        "regions": [{"region_id": "01", "name": "Alpha"}, {"region_id": "02", "name": "Beta"}],
    }
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False))


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    write_artifact(tmp_path / "scenario")
    return TestClient(create_app(Settings(), scenario_repository=FilesScenarioRepository(tmp_path / "scenario")))


def test_catalog_lists_cities_and_versions(client: TestClient) -> None:
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    catalog = response.json()
    assert catalog["model_version"] == "model-v1"
    assert catalog["seasons"] == ["road", "summer"]
    assert [city["id"] for city in catalog["cities"]] == ["X", "Y"]
    assert catalog["regions"][0]["region_id"] == "01"


def test_evaluation_returns_region_and_pair_impacts(client: TestClient) -> None:
    request = {
        "season": "road",
        "model_version": "model-v1",
        "artifact_version": "artifact-1",
        "links": [
            {
                "from_city": "X",
                "to_city": "Y",
                "mode": "air",
                "travel_h": 1.0,
                "frequency_per_week": 28,
            }
        ],
    }
    response = client.post("/api/v1/scenarios/evaluate", json=request)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["improved_city_pairs"] == 1
    assert result["city_pairs"][0]["baseline_h"] == pytest.approx(30.0)
    assert result["city_pairs"][0]["changed_h"] == pytest.approx(6.5)
    assert len(result["regions"]) == 2
    assert result["national_changed_index"] > result["national_baseline_index"]
    deltas = {impact["region_id"]: impact["delta_index"] for impact in result["regions"]}
    assert all(delta >= 0 for delta in deltas.values())
    assert result["links"][0]["from_city"] == "X"


def test_stale_versions_unknown_city_and_bad_requests(client: TestClient) -> None:
    request = {
        "season": "road",
        "model_version": "model-v1",
        "artifact_version": "old",
        "links": [{"from_city": "X", "to_city": "Y", "mode": "road", "travel_h": 1.0}],
    }
    response = client.post("/api/v1/scenarios/evaluate", json=request)
    assert response.status_code == 409
    assert response.json()["code"] == "stale_scenario_version"
    request["artifact_version"] = "artifact-1"
    request["links"] = [{"from_city": "X", "to_city": "Q", "mode": "road", "travel_h": 1.0}]
    response = client.post("/api/v1/scenarios/evaluate", json=request)
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    request["links"] = []
    assert client.post("/api/v1/scenarios/evaluate", json=request).status_code == 422
    request["links"] = [
        {"from_city": "X", "to_city": "Y", "mode": "road", "travel_h": 1.0, "frequency_per_week": 7}
    ]
    assert client.post("/api/v1/scenarios/evaluate", json=request).status_code == 422
    request["season"] = "winter"
    request["links"] = [{"from_city": "X", "to_city": "Y", "mode": "road", "travel_h": 1.0}]
    assert client.post("/api/v1/scenarios/evaluate", json=request).status_code == 422


def test_missing_artifact_fails_honestly(tmp_path: Path) -> None:
    client = TestClient(create_app(Settings(), scenario_repository=FilesScenarioRepository(tmp_path / "empty")))
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 503
    assert response.json()["code"] == "data_unavailable"
