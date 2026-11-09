import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "frontend" / "atlas" / "public"


def test_shipped_pilot_matches_verified_snapshot_and_supports_real_scenario() -> None:
    report = json.loads((ROOT / "docs" / "results" / "pilot-validation.json").read_text())
    artifact = DATA / "pilots" / "tuva.json"
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == report["artifact"]["sha256"]
    assert report["pair_comparisons"] == 24
    client = TestClient(create_app(Settings(DATA)))
    pilot = client.get("/api/v1/pilots/tuva").json()
    request = {
        "season": "summer",
        "model_version": pilot["model_version"],
        "artifact_version": pilot["artifact_version"],
        "changes": [{"edge_id": "manual:0", "frequency_per_week": 7}],
    }
    response = client.post("/api/v1/pilots/tuva/evaluate", json=request)
    assert response.status_code == 200
    result = response.json()
    assert result["pairs"][0]["changed"]["waiting_h"] == 12.0
    assert result["pairs"][0]["delta_h"] < 0
    assert client.get("/api/v1/overview").json()["regions"] == 82
