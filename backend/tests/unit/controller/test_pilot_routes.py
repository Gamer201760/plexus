import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings

DATA = Path(__file__).resolve().parents[4] / "frontend" / "atlas" / "public"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings(DATA)))


def payload(client: TestClient) -> dict[str, object]:
    detail = client.get("/api/v1/pilots/tuva")
    assert detail.status_code == 200
    pilot = detail.json()
    return {
        "season": "summer",
        "model_version": pilot["model_version"],
        "artifact_version": pilot["artifact_version"],
        "changes": [{"edge_id": "manual:0", "frequency_per_week": 7}],
    }


def test_real_pilot_round_trip_with_frequency_closure_and_unchanged_input(
    client: TestClient,
) -> None:
    source = DATA / "pilots" / "tuva.json"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    summary = client.get("/api/v1/pilots")
    assert summary.status_code == 200
    assert summary.json()[0]["pair_count"] == 3
    request = payload(client)
    response = client.post("/api/v1/pilots/tuva/evaluate", json=request)
    assert response.status_code == 200, response.text
    result = response.json()
    trip = result["pairs"][0]
    assert trip["baseline"]["total_h"] == pytest.approx(18.095108680328025)
    assert trip["changed"]["waiting_h"] == 12.0
    assert trip["delta_h"] == pytest.approx(-3.8517782134321834)
    assert result["waiting_sensitivity"][0]["periodic_wait_h"] == pytest.approx(49.714285714285715)
    request["changes"] = [{"edge_id": "manual:0", "frequency_per_week": 4}]
    assert (
        client.post("/api/v1/pilots/tuva/evaluate", json=request).json()["pairs"][0]["delta_h"]
        == 0.0
    )
    request["season"] = "winter"
    request["changes"] = [{"edge_id": "manual:5", "enabled": False}]
    closure = client.post("/api/v1/pilots/tuva/evaluate", json=request).json()
    assert closure["pairs"][2]["changed"]["status"] == "no_route"
    assert closure["pairs"][2]["delta_h"] is None
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("frequency", [0, 29, True, 1.5, "7"])
def test_invalid_frequency_is_rejected(client: TestClient, frequency: object) -> None:
    request = payload(client)
    request["changes"] = [{"edge_id": "manual:0", "frequency_per_week": frequency}]
    response = client.post("/api/v1/pilots/tuva/evaluate", json=request)
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_versions_unknown_links_and_missing_pilots(client: TestClient) -> None:
    request = payload(client)
    request["artifact_version"] = "old"
    response = client.post("/api/v1/pilots/tuva/evaluate", json=request)
    assert response.status_code == 409
    assert response.json()["code"] == "stale_pilot_version"
    request = payload(client)
    request["changes"] = [{"edge_id": "unknown", "enabled": False}]
    assert client.post("/api/v1/pilots/tuva/evaluate", json=request).status_code == 422
    assert client.get("/api/v1/pilots/unknown").status_code == 404


def test_missing_artifact_fails_honestly(tmp_path: Path) -> None:
    client = TestClient(create_app(Settings(tmp_path)))
    response = client.get("/api/v1/pilots")
    assert response.status_code == 503
    assert response.json()["code"] == "data_unavailable"


def test_added_link_changes_route_and_is_echoed(client: TestClient) -> None:
    request = payload(client)
    request["changes"] = []
    addition: dict[str, object] = {
        "from_id": "93643425101",
        "to_id": "93701000001",
        "mode": "air",
        "travel_h": 1.2,
        "seasons": ["summer", "winter"],
        "frequency_per_week": 14,
    }
    request["additions"] = [addition]
    response = client.post("/api/v1/pilots/tuva/evaluate", json=request)
    assert response.status_code == 200, response.text
    result = response.json()
    trip = result["pairs"][0]
    assert trip["changed"]["total_h"] == pytest.approx(7.2)
    assert trip["changed"]["edge_ids"] == ["added:0"]
    assert trip["delta_h"] < 0
    assert result["additions"][0]["from_id"] == "93643425101"
    addition["frequency_per_week"] = None
    assert client.post("/api/v1/pilots/tuva/evaluate", json=request).status_code == 422
    addition["frequency_per_week"] = 14
    addition["to_id"] = "unknown"
    assert client.post("/api/v1/pilots/tuva/evaluate", json=request).status_code == 422
