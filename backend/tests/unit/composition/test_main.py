from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repository.files.atlas import JsonAtlasRepository
from app.settings import Settings


def test_app_wires_atlas_repository_from_settings(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path))

    assert isinstance(app.state.atlas, JsonAtlasRepository)
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json() == {"status": "ok"}
        assert client.get("/api/v1/regions").json()["code"] == "data_unavailable"


def test_environment_selects_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    with TestClient(create_app()) as client:
        assert client.get("/api/v1/overview").status_code == 503
