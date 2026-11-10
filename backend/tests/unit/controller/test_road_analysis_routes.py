from typing import cast
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapter.log.stdlib import StdlibLogger
from app.controller.errors import ErrorHandlers
from app.controller.road_analysis.router import build_analysis_router
from app.usecase.dto import BoundaryShape, RegionRecord
from app.usecase.interface import AtlasRepository
from app.usecase.road_analysis import AnalysisJob, AnalysisPort, RoadAnalysis


@pytest.fixture
def atlas() -> AtlasRepository:
    repository = Mock(spec=AtlasRepository)
    repository.regions.return_value = [RegionRecord("18000000", "Region", 1, 10)]
    repository.boundaries.return_value = [BoundaryShape("18000000", "Region", (0, 0, 1, 1), [])]
    return cast(AtlasRepository, repository)


def test_analysis_contract_is_complete_and_validates_percentage(atlas: AtlasRepository) -> None:
    port = Mock(spec=AnalysisPort)
    port.submit.return_value = AnalysisJob("id", "18000000", "Region", "improvement", 20, "source")
    app = FastAPI()
    ErrorHandlers(StdlibLogger("test")).register(app)
    app.include_router(build_analysis_router(RoadAnalysis(cast(AnalysisPort, port), atlas)))
    with TestClient(app) as client:
        response = client.post(
            "/road-analyses", json={"region_id": "18000000", "mode": "improvement"}
        )
        assert response.status_code == 200
        assert response.json()["results"] == []
        assert response.json()["candidate_count"] == 0
        assert response.json()["compatible"] is True
        assert (
            client.post(
                "/road-analyses",
                json={"region_id": "18000000", "mode": "improvement", "percent": 201},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/road-analyses",
                json={"region_id": "18000000", "mode": "improvement", "percent": 1.5},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/road-analyses", json={"region_id": "18000000", "mode": "unknown"}
            ).status_code
            == 422
        )
    assert port.submit.call_count == 1


def test_missing_graph_is_honest_unavailable(atlas: AtlasRepository) -> None:
    app = FastAPI()
    ErrorHandlers(StdlibLogger("test")).register(app)
    app.include_router(build_analysis_router(RoadAnalysis(None, atlas)))
    with TestClient(app) as client:
        assert client.get("/road-analyses").status_code == 503
