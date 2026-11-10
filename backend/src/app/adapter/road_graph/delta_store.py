import hashlib
import json
from dataclasses import fields
from pathlib import Path
from typing import Any

import numpy as np

from app.adapter.road_graph.baselines import BaselineCache
from app.adapter.road_graph.delta_model import DeltaRegion


class DeltaStore:
    def __init__(self, root: Path) -> None:
        key = BaselineCache(root).path("prepared-delta-v2", "road").stem
        self.folder = root / "scenario-cache" / key

    def path(self, region: str) -> Path:
        return self.folder / (hashlib.sha256(region.encode()).hexdigest() + ".npz")

    def read(self, region: str) -> DeltaRegion | None:
        path = self.path(region)
        if not path.exists():
            return None
        with np.load(path, allow_pickle=False) as data:
            values = {field.name: data[field.name] for field in fields(DeltaRegion)}
        for key in ("ids", "market_names"):
            values[key] = values[key].tolist()
        for key in ("normalization", "expected", "baseline_index"):
            values[key] = float(values[key])
        return DeltaRegion(**values)

    def write(self, region: str, value: DeltaRegion) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.path(region)
        temporary = path.with_suffix(".tmp.npz")
        np.savez(temporary, **{f.name: getattr(value, f.name) for f in fields(DeltaRegion)})
        temporary.replace(path)

    def names(self) -> list[str]:
        path = self.folder / "manifest.json"
        if not path.exists():
            return []
        names: list[str] = json.loads(path.read_text())["regions"]
        return names

    def read_terminal(self, node: int) -> tuple[Any, Any] | None:
        path = self.folder / f"node-{node}.npz"
        if not path.exists():
            return None
        with np.load(path, allow_pickle=False) as data:
            return data["nodes"], data["distances"]

    def write_terminal(self, node: int, nodes: Any, distances: Any) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"node-{node}.npz"
        temporary = path.with_suffix(".tmp.npz")
        np.savez(temporary, nodes=nodes, distances=distances)
        temporary.replace(path)
