"""Дорожный граф России из data/osm_ways/*.parquet с упрощением цепочек.

Упрощение без потери точности: промежуточные вершины way (без развилок) склеиваются в одно ребро,
время и длина суммируются. Неудаляемые узлы: концы way, общие узлы разных way (развилки),
точки привязки н.п. Каждое ребро лежит внутри одного way → стресс-тест может отключать way_id.

Выход в data/graph_ru/:
  nodes.parquet   — node (индекс), lat, lon, comp (компонента связности)
  edges.parquet   — src, dst, h, km, way_id  (ориентированные; двусторонние way дают 2 ребра)
  ways.parquet    — атрибуты way: highway, ref, name, speed_kmh, is_bridge, is_ferry, is_seasonal, km
  points.parquet  — н.п.: point_id, node, snap_km, comp
"""
import os
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "osm_ways"
OUT = ROOT / "data" / "graph_ru"
DB = ROOT / "data" / "casechamp.duckdb"

# те же допущения, что и для Тывы (etl/graph_tuva.py)
SPEED = {
    "motorway": 90, "trunk": 65, "primary": 60, "secondary": 55, "tertiary": 50,
    "unclassified": 40, "road": 35, "residential": 25, "living_street": 15, "track": 20, "ferry": 10,
}
UNPAVED = ["unpaved", "gravel", "dirt", "ground", "earth", "sand", "grass", "compacted", "fine_gravel", "mud"]
UNPAVED_K = 0.7
SNAP_MAX_KM = 5.0
SNAP_KMH = 15
MIN_COMP_NODES = 200   # привязывать н.п. только к компонентам не меньше этого (отсекаем обрывки)
R_EARTH = 6371.0


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(a))


def load_ways() -> pa.Table:
    t = pa.concat_tables([pq.read_table(f) for f in sorted(SRC.glob("*.parquet"))])
    # дубли на стыках округов: оставить первую копию way_id
    _, first = np.unique(t["way_id"].to_numpy(), return_index=True)
    t = t.take(pa.array(np.sort(first)))
    print(f"ways={t.num_rows}")
    return t


def way_speed(t: pa.Table) -> np.ndarray:
    hw = pc.replace_substring(t["highway"], "_link", "").to_numpy(zero_copy_only=False)
    v = np.array([SPEED.get(h, 30) for h in hw], dtype=float)
    surf = t["surface"].to_numpy(zero_copy_only=False)
    unpaved = np.isin(surf, UNPAVED) | ((hw == "track") & (surf == None))  # noqa: E711
    v[unpaved & (hw != "ferry")] *= UNPAVED_K
    return v


def contract(way_of_vertex, nid, lat, lon, is_junction, speed, oneway):
    """Рёбра между соседними неудаляемыми вершинами внутри каждого way."""
    seg = haversine_km(lat[:-1], lon[:-1], lat[1:], lon[1:])
    same_way = way_of_vertex[:-1] == way_of_vertex[1:]
    seg = np.where(same_way, seg, 0.0)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    j = np.flatnonzero(is_junction)
    a, b = j[:-1], j[1:]
    keep = way_of_vertex[a] == way_of_vertex[b]
    a, b = a[keep], b[keep]
    w = way_of_vertex[a]
    km = cum[b] - cum[a]
    h = km / speed[w]
    uniq, node = np.unique(nid[j], return_inverse=True)
    pos = np.empty(len(nid), dtype=np.int64); pos[j] = node
    src, dst = pos[a], pos[b]
    fwd = oneway[w] != "-1"
    bwd = ~np.isin(oneway[w], ["yes", "-1"])
    S = np.concatenate([src[fwd], dst[bwd]]); D = np.concatenate([dst[fwd], src[bwd]])
    H = np.concatenate([h[fwd], h[bwd]]); K = np.concatenate([km[fwd], km[bwd]]); W = np.concatenate([w[fwd], w[bwd]])
    # координаты узлов
    nlat = np.empty(len(uniq)); nlon = np.empty(len(uniq))
    nlat[pos[j]] = lat[j]; nlon[pos[j]] = lon[j]
    return uniq, pos, nlat, nlon, S, D, H, K, W


def main():
    os.chdir(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    t = load_ways()
    nodes_col = t["nodes"].combine_chunks()
    lens = pc.list_value_length(nodes_col).to_numpy()
    nid = pc.list_flatten(nodes_col).to_numpy()
    lat = pc.list_flatten(t["lat"].combine_chunks()).to_numpy()
    lon = pc.list_flatten(t["lon"].combine_chunks()).to_numpy()
    way_of_vertex = np.repeat(np.arange(t.num_rows), lens)
    speed = way_speed(t)
    oneway = np.array(t["oneway"].to_numpy(zero_copy_only=False), dtype=object)
    print(f"vertices={len(nid)}")

    # неудаляемые: концы way + узлы, встречающиеся в нескольких местах
    starts = np.concatenate([[0], np.cumsum(lens)[:-1]]); ends = np.cumsum(lens) - 1
    _, inv, cnt = np.unique(nid, return_inverse=True, return_counts=True)
    junction = cnt[inv] > 1
    junction[starts] = True; junction[ends] = True

    # проход 1: компоненты связности на упрощённом графе
    uniq, pos, nlat, nlon, S, D, H, K, W = contract(way_of_vertex, nid, lat, lon, junction, speed, oneway)
    n = len(uniq)
    G = coo_matrix((np.ones(len(S)), (S, D)), shape=(n, n)).tocsr()
    ncomp, comp = connected_components(G, directed=False)
    comp_size = np.bincount(comp)
    way_comp = comp[pos[starts]]
    print(f"pass1: nodes={n} edges={len(S)} components={ncomp} big={np.sum(comp_size >= MIN_COMP_NODES)}")

    # привязка н.п. к ближайшей вершине (любой, не только развилке) в крупных компонентах
    con = duckdb.connect(str(DB), read_only=True)
    pts = con.sql("""select oktmo as point_id, region, latitude as lat, longitude as lon, population
                     from stg_settlements where object_level = 'Населенный пункт' and latitude is not null""").df()
    con.close()
    ok_vertex = comp_size[way_comp[way_of_vertex]] >= MIN_COMP_NODES
    vtx = np.full(len(pts), -1, dtype=np.int64)
    chord = np.full(len(pts), np.inf)
    margin = 0.5  # градусов вокруг рамки региона
    for region, idx in pts.groupby("region").indices.items():
        plat, plon = pts.lat.values[idx], pts.lon.values[idx]
        m = ok_vertex & (lat >= plat.min() - margin) & (lat <= plat.max() + margin) \
            & (lon >= plon.min() - margin) & (lon <= plon.max() + margin)
        cand = np.flatnonzero(m)
        if len(cand) == 0:
            continue
        tree = cKDTree(xyz(lat[cand], lon[cand]).astype(np.float32))
        d, k = tree.query(xyz(plat, plon))
        vtx[idx], chord[idx] = cand[k], d
    pts["snap_km"] = 2 * R_EARTH * np.arcsin(np.clip(chord / 2, 0, 1))
    pts["on_road"] = pts.snap_km <= SNAP_MAX_KM
    junction[vtx[pts.on_road.values]] = True

    # проход 2: финальный граф с узлами привязки
    uniq, pos, nlat, nlon, S, D, H, K, W = contract(way_of_vertex, nid, lat, lon, junction, speed, oneway)
    n = len(uniq)
    G = coo_matrix((np.ones(len(S)), (S, D)), shape=(n, n)).tocsr()
    ncomp, comp = connected_components(G, directed=False)
    print(f"pass2: nodes={n} edges={len(S)} (вершин было {len(nid)}, сжатие {len(nid) / n:.1f}x)")

    pts["node"] = np.where(pts.on_road, pos[vtx], -1)
    pts["comp"] = np.where(pts.on_road, comp[np.maximum(pts.node, 0)], -1)

    pq.write_table(pa.table({"node": np.arange(n), "osm_node": uniq, "lat": nlat, "lon": nlon, "comp": comp}), OUT / "nodes.parquet")
    pq.write_table(pa.table({"src": S, "dst": D, "h": H, "km": K, "way_idx": W}), OUT / "edges.parquet")
    way_km = np.bincount(W, weights=K, minlength=t.num_rows) / np.where(np.isin(oneway, ["yes", "-1"]), 1, 2)
    pq.write_table(t.drop(["nodes", "lat", "lon"]).append_column("way_idx", pa.array(np.arange(t.num_rows)))
                   .append_column("speed_kmh", pa.array(speed)).append_column("km", pa.array(way_km)), OUT / "ways.parquet")
    pq.write_table(pa.Table.from_pandas(pts, preserve_index=False), OUT / "points.parquet")
    print(f"points={len(pts)} on_road={int(pts.on_road.sum())} "
          f"pop_on_road={pts.population[pts.on_road].sum() / pts.population.sum():.3f}")


if __name__ == "__main__":
    main()
