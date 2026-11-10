import os

from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.repository.clickhouse.client import ClickHouseReader
from app.settings import Settings, load_settings


def settings() -> Settings:
    values = dict(os.environ)
    values.pop("GRAPH_DIR", None)
    if not values.get("CLICKHOUSE_URL") or not values.get("CLICKHOUSE_PASSWORD"):
        raise RuntimeError("Integration tests need CLICKHOUSE_URL and CLICKHOUSE_PASSWORD")
    return load_settings(values)


def atlas_repository() -> ClickHouseAtlasRepository:
    config = settings()
    return ClickHouseAtlasRepository(ClickHouseReader(config.clickhouse_url or "", config.clickhouse_user, config.clickhouse_password))
