from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings

ALTAI = "01000000"


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(create_app(Settings())) as test_client:
        yield test_client


def test_overview_reports_dataset_totals(client: TestClient) -> None:
    body = client.get("/api/v1/overview").json()

    assert (body["regions"], body["settlements"], body["links"]) == (82, 155412, 997)
    assert sum(body["links_by_mode"].values()) == 997
    assert body["links_by_season"] == {"summer": 360, "winter": 263, "all": 307, "unknown": 67}
    assert body["index"]["status"] == "ready"


def test_region_list_is_sorted_and_season_aware(client: TestClient) -> None:
    regions = client.get("/api/v1/regions", params={"season": "winter"}).json()

    assert len(regions) == 82
    assert [item["name"] for item in regions] == sorted(item["name"] for item in regions)
    altai = next(item for item in regions if item["id"] == ALTAI)
    assert (altai["links"], altai["links_season"]) == (8, 5)
    assert altai["hansen"] > 0
    assert 0 <= altai["index_population_coverage"] <= 1


def test_region_detail_has_geometry_and_economy(client: TestClient) -> None:
    body = client.get(f"/api/v1/regions/{ALTAI}").json()

    assert body["path"].startswith("M") and len(body["bbox"]) == 4
    assert body["economy"]["company_rows"] == 35815
    crimea = client.get("/api/v1/regions/35000000").json()
    assert (crimea["has_geometry"], crimea["path"], crimea["bbox"]) == (False, None, None)


def test_region_links_serialize_endpoints_as_from_and_to(client: TestClient) -> None:
    links = client.get(f"/api/v1/regions/{ALTAI}/links", params={"mode": "river"}).json()

    assert {item["mode"] for item in links} == {"river"}
    first = links[0]
    assert first["from"]["name"] == "г. Барнаул" and first["from"]["x"] is not None
    assert first["km"] == 22.0 and first["freq_assumed"] is False
    assert client.get("/api/v1/links/0").json() == first


def test_routes_list_every_link_with_coordinates(client: TestClient) -> None:
    routes = client.get("/api/v1/links").json()

    assert 0 < len(routes) <= 997
    assert {"id", "mode", "season", "from_name", "to_name", "x1", "y1", "x2", "y2"} == set(
        routes[0]
    )
    assert {item["mode"] for item in routes} >= {"air", "river", "winter_road"}


def test_settlements_page_sorts_by_population(client: TestClient) -> None:
    body = client.get(f"/api/v1/regions/{ALTAI}/settlements", params={"limit": 3}).json()

    assert body["total"] == 1605
    assert body["items"][0]["name"] == "г. Барнаул"
    populations = [item["population"] for item in body["items"]]
    assert populations == sorted(populations, reverse=True)


def test_search_is_case_and_yo_insensitive(client: TestClient) -> None:
    upper = client.get("/api/v1/search", params={"q": "СЕМЁНОВКА"}).json()
    lower = client.get("/api/v1/search", params={"q": "семеновка"}).json()

    assert upper == lower and len(upper["settlements"]) == 8
    regions = client.get("/api/v1/search", params={"q": "алтай"}).json()["regions"]
    assert {item["id"] for item in regions} >= {ALTAI}


def test_reference_lists(client: TestClient) -> None:
    roads = client.get("/api/v1/seasons/winter-roads").json()
    sources = client.get("/api/v1/sources").json()
    geo = client.get("/api/v1/geo/regions").json()

    assert len(roads) == 18 and roads[0]["closure_date"] is None
    assert {"atlas-links", "rfsd"} <= {item["id"] for item in sources}
    assert geo["view_box"] == "0 0 1000 620"
    assert geo["missing"] == [{"id": "35000000", "name": "Республика Крым"}]


@pytest.mark.parametrize(
    ("path", "status", "code"),
    [
        ("/api/v1/regions/00000000", 404, "region_not_found"),
        ("/api/v1/regions/00000000/links", 404, "region_not_found"),
        ("/api/v1/regions/00000000/settlements", 404, "region_not_found"),
        ("/api/v1/links/nope", 404, "link_not_found"),
        ("/api/v1/regions?season=spring", 422, "validation_error"),
        ("/api/v1/regions/01000000/links?mode=bus", 422, "validation_error"),
        ("/api/v1/search?q=a", 422, "validation_error"),
        ("/api/v1/search?q=%20%D0%B0%20", 422, "validation_error"),
        ("/api/v1/regions/01000000/settlements?limit=0", 422, "validation_error"),
    ],
)
def test_errors_use_envelope(client: TestClient, path: str, status: int, code: str) -> None:
    response = client.get(path)

    assert response.status_code == status
    assert response.json()["code"] == code and set(response.json()) == {"code", "message"}


def test_missing_data_dir_returns_unavailable(tmp_path_factory: pytest.TempPathFactory) -> None:
    settings = Settings(data_dir=tmp_path_factory.mktemp("empty"))
    with TestClient(create_app(settings)) as empty:
        response = empty.get("/api/v1/overview")

    assert response.status_code == 503
    assert response.json()["code"] == "data_unavailable"


def test_openapi_documents_link_aliases(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert "/api/v1/regions/{region_id}/settlements" in schema["paths"]
    link = schema["components"]["schemas"]["LinkResponse"]["properties"]
    assert {"from", "to"} <= set(link)
