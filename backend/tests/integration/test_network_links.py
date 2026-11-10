from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from tests.storage import settings as storage_settings

from app.main import create_app


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(create_app(storage_settings())) as test_client:
        yield test_client


def test_vladimir_rail_models_have_coordinates_and_unknown_frequency(client: TestClient) -> None:
    response = client.get("/api/v1/regions/17000000/links?mode=rail")
    assert response.status_code == 200
    links = response.json()
    assert len(links) == 501
    assert all(link["season"] is None for link in links)
    assert all(link["is_model"] for link in links)
    assert all(link["freq_per_week"] is None and not link["freq_assumed"] for link in links)
    assert all(link[end]["lat"] is not None for link in links for end in ("from", "to"))
    assert all(link[end]["lon"] is not None for link in links for end in ("from", "to"))
    assert all(link["source_url"] == "https://tochno.st/datasets/intercity_connectivity" for link in links)


def test_yakutia_real_chains_keep_unknown_calendar(client: TestClient) -> None:
    links = client.get("/api/v1/regions/98000000/links?mode=rail").json()
    assert len(links) == 2
    assert {link["to"]["name"] for link in links} == {"Тында", "Благовещенск"}
    assert all(not link["is_model"] and link["season"] is None for link in links)
    assert all(link["freq_per_week"] is None and link["km"] is None for link in links)
    assert client.get("/api/v1/regions/98000000/links?mode=rail&season=summer").json() == []
    included = client.get(
        "/api/v1/regions/98000000/links?mode=rail&season=summer&include_unknown=true"
    ).json()
    assert len(included) == 2


def test_airline_import_keeps_known_frequency_without_conflicting_flights(client: TestClient) -> None:
    links = client.get("/api/v1/regions/92000000/links?mode=air&season=winter&include_unknown=true").json()
    scheduled = [link for link in links if link["source_url"] == "https://www.uvtaero.ru/raspisanie"]
    assert scheduled
    assert all(not link["is_model"] and not link["freq_assumed"] for link in scheduled)
    assert all(0 < link["freq_per_week"] <= 7 for link in scheduled)
    assert not any("RT535" in link["freq_note"] or "RT536" in link["freq_note"] for link in scheduled)
    assert len({link["id"] for link in scheduled}) == len(scheduled)


def test_new_sources_are_available_in_source_catalog(client: TestClient) -> None:
    sources = {row["id"]: row for row in client.get("/api/v1/sources").json()}
    assert sources["network-model"]["rows"] == 33957
    assert sources["network-uvt"]["rows"] == 135
    assert sources["network-yakutia"]["rows"] == 4
