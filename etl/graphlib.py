"""Загрузка графа data/graph_ru в scipy CSR.

Важно: coo→csr СУММИРУЕТ дубли (src, dst). Параллельные рёбра (разные way между теми же развилками)
должны давать минимум, поэтому перед сборкой матрицы оставляем быстрейшее ребро каждой пары.
"""
import os
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from scipy.sparse import csr_matrix

GRAPH = Path(os.environ.get("GRAPH_INPUT", str(Path(__file__).resolve().parent.parent / "data" / "graph_ru")))


def load_edges(season=None):
    e = pq.read_table(GRAPH / "edges.parquet")
    result = {c: e[c].to_numpy() for c in e.column_names}
    if season is not None:
        season = season.removeprefix("road_")
        ways = pq.read_table(GRAPH / "ways.parquet", columns=["operating_season"])
        allowed = ways["operating_season"].to_numpy()
        keep = allowed[result["way_idx"]] == "all"
        if season in {"summer", "winter"}:
            keep |= allowed[result["way_idx"]] == season
        elif season != "road":
            raise ValueError(f"unsupported season: {season}")
        result = {c: values[keep] for c, values in result.items()}
    return result


def build_csr(src, dst, w, n, drop_mask=None, *, undirected=False):
    """CSR с минимальным весом на пару (src, dst). drop_mask — рёбра, которые исключить (стресс-тест)."""
    if drop_mask is not None:
        keep = ~drop_mask
        src, dst, w = src[keep], dst[keep], w[keep]
    if undirected:
        src, dst, w = np.concatenate([src, dst]), np.concatenate([dst, src]), np.concatenate([w, w])
    order = np.lexsort((w, dst, src))            # по паре, внутри — по весу
    s, d, ww = src[order], dst[order], w[order]
    first = np.ones(len(s), dtype=bool)
    first[1:] = (s[1:] != s[:-1]) | (d[1:] != d[:-1])
    return csr_matrix((ww[first], (s[first], d[first])), shape=(n, n))


def load_graph(weight="h", season="road"):
    e = load_edges(season)
    n = pq.read_metadata(GRAPH / "nodes.parquet").num_rows
    return build_csr(e["src"], e["dst"], e[weight], n), e, n
