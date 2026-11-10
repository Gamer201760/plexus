from pathlib import Path
from typing import Any

from scipy.sparse import load_npz, save_npz

from app.repository.files.road_graph.baselines import BaselineCache


class FileGraphMatrixStore:
    def __init__(self, root: Path, revision: str = "[]") -> None:
        self.path = BaselineCache(root, revision).path("delta-road-graph-v1", "road").with_suffix(
            ".npz"
        )

    def read(self) -> Any | None:
        return load_npz(self.path) if self.path.exists() else None

    def write(self, graph: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        save_npz(self.path, graph, compressed=False)
