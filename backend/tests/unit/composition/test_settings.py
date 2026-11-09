from pathlib import Path

from app.settings import DEFAULT_DATA_DIR, Settings, load_settings


def test_empty_environment_uses_repository_atlas_export() -> None:
    assert load_settings({}) == Settings()
    assert (DEFAULT_DATA_DIR / "atlas.json").is_file()


def test_data_dir_comes_from_environment() -> None:
    assert load_settings({"DATA_DIR": "/srv/atlas"}).data_dir == Path("/srv/atlas")
    assert load_settings({"DATA_DIR": ""}).data_dir == DEFAULT_DATA_DIR
