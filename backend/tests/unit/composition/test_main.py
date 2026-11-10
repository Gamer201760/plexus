from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.settings import Settings


def test_app_wires_atlas_repository_from_settings(tmp_path: Path) -> None:
    app = create_app(Settings())

    assert isinstance(app.state.atlas, ClickHouseAtlasRepository)
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json() == {"status": "ok"}
    assert app.state.atlas.reader.url == "http://127.0.0.1:18123"


def test_environment_selects_clickhouse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLICKHOUSE_URL", "http://storage:8123")
    monkeypatch.delenv("GRAPH_DIR", raising=False)
    app = create_app()
    assert app.state.atlas.reader.url == "http://storage:8123"
