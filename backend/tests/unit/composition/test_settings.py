from pathlib import Path

from app.settings import Settings, load_settings


def test_empty_environment_uses_default_storage_settings() -> None:
    assert load_settings({}) == Settings()
    assert load_settings({"CLICKHOUSE_URL": "http://storage:8123"}).clickhouse_url == "http://storage:8123"


def test_cache_directory_comes_from_environment() -> None:
    assert load_settings({"GRAPH_DIR": "/srv/cache"}).graph_dir == Path("/srv/cache")
    assert load_settings({"GRAPH_DIR": ""}).graph_dir is None
