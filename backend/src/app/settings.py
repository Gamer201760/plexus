from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "frontend" / "atlas" / "public"


DEFAULT_SCENARIO_DIR = Path(__file__).resolve().parents[3] / "data" / "scenario_ru"


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path = DEFAULT_DATA_DIR
    scenario_dir: Path = DEFAULT_SCENARIO_DIR
    chat_enabled: bool = False
    graph_dir: Path | None = None


def load_settings(env: Mapping[str, str]) -> Settings:
    raw = env.get("DATA_DIR")
    return Settings(
        data_dir=Path(raw) if raw else DEFAULT_DATA_DIR,
        scenario_dir=Path(env["SCENARIO_DIR"]) if env.get("SCENARIO_DIR") else DEFAULT_SCENARIO_DIR,
        graph_dir=Path(env["GRAPH_DIR"]) if env.get("GRAPH_DIR") else None,
        chat_enabled=env.get("CHAT_ENABLED", "false").lower() == "true",
    )
