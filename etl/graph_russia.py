"""Дорожный граф России из data/osm_ways/*.parquet с упрощением цепочек.

Упрощение без потери точности: промежуточные вершины way (без развилок) склеиваются в одно ребро,
время и длина суммируются. Неудаляемые узлы: концы way, общие узлы разных way (развилки),
точки привязки н.п. Каждое ребро лежит внутри одного way → стресс-тест может отключать way_idx.

Память: у сессии лимит cgroup ~11 ГБ, поэтому глобально держим только массивы вершин (~60 млн),
а сжатие цепочек идёт пачками ways (CHUNK_VERTICES вершин за раз).

Выход в data/graph_ru/:
  nodes.parquet   — node (индекс), osm_node, lat, lon, comp (компонента связности)
  edges.parquet   — src, dst, h, km, way_idx  (ориентированные; двусторонние way дают 2 ребра)
  ways.parquet    — атрибуты way: highway, ref, name, surface, ..., speed_kmh, km, way_idx
  points.parquet  — н.п.: point_id, region, population, lat, lon, snap_km, on_road, node, comp
"""
import gc
import os
import resource
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
OUT = Path(os.environ.get("GRAPH_OUTPUT", str(ROOT / "data" / "graph_ru")))
DB = ROOT / "data" / "casechamp.duckdb"

# те же допущения, что и для Тывы (etl/graph_tuva.py)
SPEED = {
    "motorway": 90, "trunk": 65, "primary": 60, "secondary": 55, "tertiary": 50,
    "unclassified": 40, "road": 35, "residential": 25, "living_street": 15, "track": 20, "ferry": 10,
}
UNPAVED = ["unpaved", "gravel", "dirt", "ground", "earth", "sand", "grass", "compacted", "fine_gravel", "mud"]
UNPAVED_K = 0.7
SNAP_MAX_KM = 5.0
MIN_COMP_NODES = 200   # привязывать н.п. только к компонентам не меньше этого (отсекаем обрывки)
CHUNK_VERTICES = 5_000_000
R_EARTH = 6371.0


def log(msg):
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576
    print(f"{msg}  [peak RSS {rss:.1f} GB]", flush=True)


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(a))


def load_ways() -> pa.Table:
    files = sorted(SRC.glob(os.environ.get("OSM_GLOB", "*.parquet")))   # OSM_GLOB — для тестов на одном округе
    t = pa.concat_tables([pq.read_table(f) for f in files])
    # дубли на стыках округов: оставить первую копию way_id
    _, first = np.unique(t["way_id"].to_numpy(), return_index=True)
    t = t.take(pa.array(np.sort(first)))
    log(f"ways={t.num_rows}")
    return t


def way_speed(t: pa.Table) -> np.ndarray:
    hw = pc.replace_substring(t["highway"], "_link", "").to_numpy(zero_copy_only=False)
    v = np.array([SPEED.get(h, 30) for h in hw], dtype=np.float64)
    surf = t["surface"].to_numpy(zero_copy_only=False)
    unpaved = np.isin(surf, UNPAVED) | ((hw == "track") & (surf == None))  # noqa: E711
    v[unpaved & (hw != "ferry")] *= UNPAVED_K
    return v


def contract(V, junction, speed, oneway):
    """Сжатие цепочек пачками. V — dict глобальных массивов вершин. Возвращает узлы и рёбра."""
    nid, lat, lon, wov, starts, ends = V["nid"], V["lat"], V["lon"], V["wov"], V["starts"], V["ends"]
    uniq = np.unique(nid[junction])                       # osm_node → индекс узла через searchsorted
    n = len(uniq)
    nlat = np.empty(n); nlon = np.empty(n)
    parts = {k: [] for k in ("S", "D", "H", "K", "W")}
    nways = len(starts)
    w0 = 0
    while w0 < nways:
        v0 = starts[w0]
        w1 = int(np.searchsorted(ends, v0 + CHUNK_VERTICES, side="right"))
        w1 = max(w1, w0 + 1)
        v1 = ends[w1 - 1] + 1                             # пачка — целые ways [w0, w1)
        la, lo, wv, jn = lat[v0:v1], lon[v0:v1], wov[v0:v1], junction[v0:v1]
        seg = haversine_km(la[:-1], lo[:-1], la[1:], lo[1:])
        seg[wv[:-1] != wv[1:]] = 0.0
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        j = np.flatnonzero(jn)
        node = np.searchsorted(uniq, nid[v0:v1][j]).astype(np.int32)
        nlat[node] = la[j]; nlon[node] = lo[j]
        a, b = np.arange(len(j) - 1), np.arange(1, len(j))
        keep = wv[j[a]] == wv[j[b]]
        a, b = a[keep], b[keep]
        w = wv[j[a]]
        km = cum[j[b]] - cum[j[a]]
        h = km / speed[w]
        ow = oneway[w]
        fwd, bwd = ow != 2, ow != 1
        src, dst = node[a], node[b]
        parts["S"] += [src[fwd], dst[bwd]]; parts["D"] += [dst[fwd], src[bwd]]
        parts["H"] += [h[fwd].astype(np.float32), h[bwd].astype(np.float32)]
        parts["K"] += [km[fwd].astype(np.float32), km[bwd].astype(np.float32)]
        parts["W"] += [w[fwd], w[bwd]]
        w0 = w1
    E = {k: np.concatenate(v) for k, v in parts.items()}
    return uniq, nlat, nlon, E


def components(E, n):
    G = coo_matrix((np.ones(len(E["S"]), dtype=np.int8), (E["S"], E["D"])), shape=(n, n)).tocsr()
    return connected_components(G, directed=False)


def main():
    os.chdir(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    t = load_ways()
    nodes_col = t["nodes"].combine_chunks()
    lens = pc.list_value_length(nodes_col).to_numpy()
    V = {"nid": pc.list_flatten(nodes_col).to_numpy().copy()}
    del nodes_col
    V["lat"] = pc.list_flatten(t["lat"].combine_chunks()).to_numpy().copy()
    V["lon"] = pc.list_flatten(t["lon"].combine_chunks()).to_numpy().copy()
    V["wov"] = np.repeat(np.arange(t.num_rows, dtype=np.int32), lens)
    V["starts"] = np.concatenate([[0], np.cumsum(lens)[:-1]]).astype(np.int64)
    V["ends"] = (np.cumsum(lens) - 1).astype(np.int64)
    speed = way_speed(t)
    ow_raw = t["oneway"].to_numpy(zero_copy_only=False)
    oneway = np.where(ow_raw == "-1", 2, np.where(np.isin(ow_raw, ["yes", "true", "1"]), 1, 0)).astype(np.int8)
    del ow_raw
    t = t.drop(["nodes", "lat", "lon"])
    gc.collect()
    log(f"vertices={len(V['nid'])}")

    # неудаляемые: концы way + узлы, встречающиеся больше одного раза (развилки)
    order = np.argsort(V["nid"], kind="stable")
    sn = V["nid"][order]
    eq = sn[1:] == sn[:-1]
    del sn
    junction = np.zeros(len(order), dtype=bool)
    junction[order[1:][eq]] = True; junction[order[:-1][eq]] = True
    del order, eq
    junction[V["starts"]] = True; junction[V["ends"]] = True
    gc.collect()
    log(f"junctions={int(junction.sum())}")

    # проход 1: компоненты связности, чтобы не привязывать н.п. к оторванным обрывкам
    uniq, _, _, E = contract(V, junction, speed, oneway)
    ncomp, comp = components(E, len(uniq))
    comp_size = np.bincount(comp)
    way_big = comp_size[comp[np.searchsorted(uniq, V["nid"][V["starts"]])]] >= MIN_COMP_NODES
    del E, uniq, comp
    gc.collect()
    log(f"pass1: components={ncomp} big={int(np.sum(comp_size >= MIN_COMP_NODES))}")

    # привязка н.п. к ближайшей вершине (любой) в крупных компонентах, по регионам
    con = duckdb.connect(str(DB), read_only=True)
    pts = con.sql("""select oktmo as point_id, region, latitude as lat, longitude as lon, population
                     from stg_settlements where object_level = 'Населенный пункт' and latitude is not null""").df()
    if region := os.environ.get("POINT_REGION"):
        pts = pts[pts.region == region].reset_index(drop=True)
    con.close()
    lat, lon = V["lat"], V["lon"]
    vtx = np.full(len(pts), -1, dtype=np.int64)
    chord = np.full(len(pts), np.inf)
    margin = 0.5
    for region, idx in pts.groupby("region").indices.items():
        plat, plon = pts.lat.values[idx], pts.lon.values[idx]
        m = (lat >= plat.min() - margin) & (lat <= plat.max() + margin)
        m &= (lon >= plon.min() - margin) & (lon <= plon.max() + margin)
        cand = np.flatnonzero(m)
        del m
        cand = cand[way_big[V["wov"][cand]]]
        if len(cand) == 0:
            continue
        tree = cKDTree(xyz(lat[cand], lon[cand]))
        d, k = tree.query(xyz(plat, plon))
        vtx[idx], chord[idx] = cand[k], d
        del tree, cand
    pts["snap_km"] = 2 * R_EARTH * np.arcsin(np.clip(chord / 2, 0, 1))
    pts["on_road"] = pts.snap_km <= SNAP_MAX_KM
    junction[vtx[pts.on_road.values]] = True
    gc.collect()
    log(f"snapped: on_road={int(pts.on_road.sum())}/{len(pts)}")

    # проход 2: финальный граф с узлами привязки
    uniq, nlat, nlon, E = contract(V, junction, speed, oneway)
    n = len(uniq)
    ncomp, comp = components(E, n)
    log(f"pass2: nodes={n} edges={len(E['S'])} (вершин {len(V['nid'])}, сжатие {len(V['nid']) / n:.1f}x)")

    node_of_pt = np.searchsorted(uniq, V["nid"][np.maximum(vtx, 0)]).astype(np.int64)
    pts["node"] = np.where(pts.on_road, node_of_pt, -1)
    pts["comp"] = np.where(pts.on_road, comp[np.maximum(pts.node.values, 0)], -1)

    pq.write_table(pa.table({"node": np.arange(n, dtype=np.int32), "osm_node": uniq, "lat": nlat, "lon": nlon,
                             "comp": comp.astype(np.int32)}), OUT / "nodes.parquet")
    pq.write_table(pa.table({"src": E["S"], "dst": E["D"], "h": E["H"], "km": E["K"], "way_idx": E["W"]}),
                   OUT / "edges.parquet")
    way_km = np.bincount(E["W"], weights=E["K"], minlength=t.num_rows) / np.where(oneway > 0, 1, 2)
    pq.write_table(t.append_column("way_idx", pa.array(np.arange(t.num_rows, dtype=np.int32)))
                   .append_column("speed_kmh", pa.array(speed)).append_column("km", pa.array(way_km)),
                   OUT / "ways.parquet")
    pq.write_table(pa.Table.from_pandas(pts, preserve_index=False), OUT / "points.parquet")
    log(f"points={len(pts)} on_road={int(pts.on_road.sum())} "
        f"pop_on_road={pts.population[pts.on_road].sum() / pts.population.sum():.3f}")


if __name__ == "__main__":
    main()
