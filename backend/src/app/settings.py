from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    chat_enabled: bool = False
    graph_dir: Path | None = None
    clickhouse_url: str = "http://127.0.0.1:18123"
    clickhouse_user: str = "plexus"
    clickhouse_password: str = ""


def load_settings(env: Mapping[str, str]) -> Settings:
    return Settings(
        graph_dir=Path(env["GRAPH_DIR"]) if env.get("GRAPH_DIR") else None,
        chat_enabled=env.get("CHAT_ENABLED", "false").lower() == "true",
        clickhouse_url=env.get("CLICKHOUSE_URL") or "http://127.0.0.1:18123",
        clickhouse_user=env.get("CLICKHOUSE_USER", "plexus"),
        clickhouse_password=env.get("CLICKHOUSE_PASSWORD", ""),
    )
