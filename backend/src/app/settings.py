from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "frontend" / "atlas" / "public"
DEFAULT_SCENARIO_DIR = Path(__file__).resolve().parents[3] / "data" / "scenario_ru"


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path = DEFAULT_DATA_DIR
    scenario_dir: Path = DEFAULT_SCENARIO_DIR


def load_settings(env: Mapping[str, str]) -> Settings:
    data = env.get("DATA_DIR")
    scenario = env.get("SCENARIO_DIR")
    return Settings(
        data_dir=Path(data) if data else DEFAULT_DATA_DIR,
        scenario_dir=Path(scenario) if scenario else DEFAULT_SCENARIO_DIR,
    )
