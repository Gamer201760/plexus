from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "frontend" / "atlas" / "public"


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path = DEFAULT_DATA_DIR


def load_settings(env: Mapping[str, str]) -> Settings:
    raw = env.get("DATA_DIR")
    return Settings(data_dir=Path(raw) if raw else DEFAULT_DATA_DIR)
