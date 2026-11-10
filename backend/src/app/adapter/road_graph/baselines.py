import hashlib
import json
from pathlib import Path

from app.adapter.road_graph.data import VERSION


class BaselineCache:
    def __init__(self, root: Path, revision: str = "[]") -> None:
        self.root = root
        self.signature = json.loads(revision)

    def path(self, region: str, scenario: str) -> Path:
        key = hashlib.sha256(
            json.dumps([VERSION, "routing-v1", region, scenario, self.signature]).encode()
        )
        return self.root / "scenario-results" / f"baseline-{key.hexdigest()}.json"

    def read(self, region: str, scenario: str) -> float | None:
        path = self.path(region, scenario)
        if not path.exists():
            return None
        return float(json.loads(path.read_text())["value"])

    def write(self, region: str, scenario: str, value: float) -> None:
        path = self.path(region, scenario)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"region": region, "scenario": scenario, "value": value}))
        temporary.replace(path)
