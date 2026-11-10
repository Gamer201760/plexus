from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from app.repository.files.road_graph.baselines import BaselineCache
from app.repository.files.road_graph.delta import FileDeltaStore
from app.repository.files.road_graph.matrix import FileGraphMatrixStore
from app.usecase.dto.road_graph import DeltaRegion

REVISION = '["hansen-frequency-v2","fixture"]'


def region() -> DeltaRegion:
    return DeltaRegion(
        ["a", "b"],
        np.array([0, 1], dtype=np.int32),
        np.zeros(2),
        np.ones(2),
        np.ones((2, 1), dtype=np.float32),
        np.zeros((1, 1)),
        np.full((1, 1), np.inf),
        np.array([0], dtype=np.int32),
        np.zeros(1),
        np.ones(1),
        ["market"],
        2.0,
        50.0,
        np.ones((2, 1)),
        np.ones(2),
        50.0,
    )


def test_baseline_cache_round_trips_by_revision(tmp_path: Path) -> None:
    BaselineCache(tmp_path, REVISION).write("region", "road", 12.5)
    assert BaselineCache(tmp_path, REVISION).read("region", "road") == 12.5
    assert BaselineCache(tmp_path, "[]").read("region", "road") is None


def test_delta_store_round_trips_region_terminal_and_manifest(tmp_path: Path) -> None:
    store = FileDeltaStore(tmp_path, REVISION)
    store.write("region", region())
    store.write_terminal(3, np.array([1, 2]), np.array([0.5, 1.5]))
    store.write_manifest({"regions": ["region"]})
    loaded = store.read("region")
    terminal = store.read_terminal(3)
    assert loaded is not None and loaded.ids == ["a", "b"] and loaded.baseline_index == 50.0
    assert terminal is not None and terminal[1].tolist() == [0.5, 1.5]
    assert FileDeltaStore(tmp_path, REVISION).names() == ["region"]
    assert store.read("missing") is None


def test_graph_matrix_store_round_trips_sparse_graph(tmp_path: Path) -> None:
    store = FileGraphMatrixStore(tmp_path, REVISION)
    assert store.read() is None
    store.write(csr_matrix(np.array([[0.0, 1.0], [0.0, 0.0]])))
    loaded = store.read()
    assert loaded is not None and loaded.toarray().tolist() == [[0.0, 1.0], [0.0, 0.0]]
