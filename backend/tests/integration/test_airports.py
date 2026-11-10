from fastapi.testclient import TestClient
from tests.storage import settings as storage_settings

from app.main import create_app


def test_catalog_excludes_closed_sites_and_anchors_usinsk_to_airport() -> None:
    with TestClient(create_app(storage_settings())) as client:
        response = client.get("/api/v1/airports")
        assert response.status_code == 200
        catalog = response.json()
        assert catalog["source_url"].endswith("airports.csv")
        airports = {airport["id"]: airport for airport in catalog["airports"]}
        assert all(a["kind"] in {"medium_airport", "large_airport", "small_airport"}
                   for a in airports.values())
        usinsk = next(a for a in airports.values() if a["iata"] == "USK")
        assert 57.3 < usinsk["longitude"] < 57.5
        assert 66.0 < usinsk["latitude"] < 66.1
        assignments = catalog["assignments"]
        assert any(a["airport_id"] == usinsk["id"] for a in assignments)
        assert all(a["distance_km"] <= 150 and airports[a["airport_id"]]["scheduled"]
                   for a in assignments)
