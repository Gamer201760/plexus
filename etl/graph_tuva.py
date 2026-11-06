"""Дорожный граф Тывы из OSM и матрица времени в пути между н.п.

Вход:  data/raw/osm_tuva/{tuva,corridor}.json (Overpass, `out tags geom`), stg_settlements, stg_intercity.
Выход (DuckDB):
  road_edges     — рёбра графа на уровне участков OSM-way (для стресс-теста: отключаем way_id)
  tuva_points    — н.п. Тывы + внешние хабы с привязкой к графу
  od_road        — время/расстояние по дорогам между всеми точками (часы, км)

Модель скорости — по классу дороги и покрытию (ниже SPEED, UNPAVED_K).
Узлы графа — вершины геометрии; общие узлы ways совпадают по координатам.
"""
import json
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "osm_tuva"
DB = ROOT / "data" / "casechamp.duckdb"

# средняя скорость, км/ч — допущение модели, проверяется чувствительностью
SPEED = {
    # trunk/primary/secondary снижены под горный рельеф: калибровка Кызыл–Абакан к 6,3 ч (Точно)
    "motorway": 90, "trunk": 65, "primary": 60, "secondary": 55, "tertiary": 50,
    "unclassified": 40, "road": 35, "residential": 25, "living_street": 15, "track": 20,
}
UNPAVED = {"unpaved", "gravel", "dirt", "ground", "earth", "sand", "grass", "compacted", "fine_gravel", "mud"}
UNPAVED_K = 0.7          # грунт/гравий: −30% скорости
FERRY_KMH = 10           # паром, без учёта ожидания
SNAP_MAX_KM = 5.0        # дальше — н.п. считается без дороги в OSM
SNAP_KMH = 15            # «подъезд» от точки н.п. до ближайшего узла графа

# внешние хабы: ЖД (Абакан, Минусинск) и магистральная сеть
EXTERNAL_HUBS = ["Абакан", "Минусинск"]


def way_speed(tags: dict) -> tuple[float, str]:
    if tags.get("route") == "ferry":
        return FERRY_KMH, "ferry"
    hw = tags.get("highway", "road").replace("_link", "")
    v = SPEED.get(hw, 30)
    if tags.get("surface") in UNPAVED or (hw == "track" and tags.get("surface") is None):
        v *= UNPAVED_K
    return v, hw


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


def path_km(pred: np.ndarray, Gkm) -> np.ndarray:
    """Длина пути от корня дерева кратчайших путей до каждого узла (pointer jumping, O(n log depth))."""
    n = len(pred)
    has = pred >= 0
    acc = np.zeros(n)
    acc[has] = np.asarray(Gkm[pred[has], np.where(has)[0]]).ravel()
    p = np.where(has, pred, -1)
    while (p >= 0).any():
        m = p >= 0
        acc[m] += acc[p[m]]
        nxt = np.full(n, -1)
        nxt[m] = p[p[m]]
        p = nxt
    return acc


def load_ways() -> list[dict]:
    ways = {}
    for f in ("tuva.json", "corridor.json"):
        for el in json.loads((RAW / f).read_text())["elements"]:
            if el["type"] == "way" and el.get("geometry"):
                ways[el["id"]] = el
    return list(ways.values())


def build_graph(ways):
    node_idx: dict[tuple, int] = {}
    coords = []
    src, dst, length, hours, way_ids = [], [], [], [], []
    meta = []

    def nid(lat, lon):
        k = (round(lat, 7), round(lon, 7))
        i = node_idx.get(k)
        if i is None:
            i = node_idx[k] = len(coords)
            coords.append(k)
        return i

    for w in ways:
        t = w.get("tags", {})
        v, cls = way_speed(t)
        g = w["geometry"]
        lat = np.array([p["lat"] for p in g]); lon = np.array([p["lon"] for p in g])
        seg = haversine_km(lat[:-1], lon[:-1], lat[1:], lon[1:])
        ids = [nid(a, b) for a, b in zip(lat, lon)]
        oneway = t.get("oneway") == "yes"
        for i in range(len(seg)):
            for a, b in ((ids[i], ids[i + 1]),) if oneway else ((ids[i], ids[i + 1]), (ids[i + 1], ids[i])):
                src.append(a); dst.append(b); length.append(seg[i]); hours.append(seg[i] / v); way_ids.append(w["id"])
        meta.append({
            "way_id": w["id"], "class": cls, "ref": t.get("ref"), "name": t.get("name"),
            "surface": t.get("surface"), "speed_kmh": v, "length_km": float(seg.sum()),
            "is_bridge": t.get("bridge") not in (None, "no"),
            "is_ferry": cls == "ferry",
            "is_seasonal": t.get("ice_road") == "yes" or t.get("winter_road") == "yes" or t.get("seasonal") not in (None, "no"),
            "lat_mid": float(lat[len(lat) // 2]), "lon_mid": float(lon[len(lon) // 2]),
        })
    coords = np.array(coords)
    edges = pd.DataFrame({"src": src, "dst": dst, "km": length, "h": hours, "way_id": way_ids})
    return coords, edges, pd.DataFrame(meta)


def main():
    os.chdir(ROOT)
    con = duckdb.connect(str(DB))
    ways = load_ways()
    coords, edges, meta = build_graph(ways)
    n = len(coords)
    print(f"ways={len(ways)} nodes={n} directed_edges={len(edges)}")

    # дубли рёбер (одна пара узлов из разных ways) — оставить быстрейшее
    best = edges.sort_values("h").drop_duplicates(["src", "dst"])
    G = coo_matrix((best.h, (best.src, best.dst)), shape=(n, n)).tocsr()
    Gkm = coo_matrix((best.km, (best.src, best.dst)), shape=(n, n)).tocsr()

    ncomp, label = connected_components(G, directed=False)
    main_comp = np.bincount(label).argmax()
    print(f"components={ncomp}, main component nodes={np.sum(label == main_comp)}")

    # точки: н.п. Тывы + внешние хабы
    pts = con.sql("""
        select oktmo as point_id, settlement as name, mun_upper, population, latitude as lat, longitude as lon,
               'np' as kind
        from stg_settlements where region = 'Республика Тыва' and object_level = 'Населенный пункт'
    """).df()
    pts["is_district_center"] = pts.groupby("mun_upper").population.transform("max") == pts.population
    hubs = con.sql(f"""
        select distinct 'hub:' || city_from as point_id, city_from as name, region_from as mun_upper,
               population_from as population, lat_from as lat, lon_from as lon, 'hub' as kind, false as is_district_center
        from stg_intercity where city_from in ({','.join(repr(h) for h in EXTERNAL_HUBS)})
    """).df()
    pts = pd.concat([pts, hubs], ignore_index=True)

    # привязка к ближайшему узлу главной компоненты (плоская проекция, ок для ~5 км)
    k = np.cos(np.radians(51.5))
    main_nodes = np.where(label == main_comp)[0]
    tree = cKDTree(np.c_[coords[main_nodes, 0], coords[main_nodes, 1] * k])
    _, j = tree.query(np.c_[pts.lat, pts.lon * k])
    pts["node"] = main_nodes[j]
    pts["snap_km"] = haversine_km(pts.lat.values, pts.lon.values, coords[pts.node, 0], coords[pts.node, 1])
    pts["on_road"] = pts.snap_km <= SNAP_MAX_KM

    # кратчайшие пути по времени; км — вдоль того же пути
    ok = pts[pts.on_road].reset_index(drop=True)
    D, pred = dijkstra(G, directed=True, indices=ok.node.values, return_predecessors=True)
    snap_h = (ok.snap_km / SNAP_KMH).values
    tgt = ok.node.values
    rows = []
    for a in range(len(ok)):
        km = path_km(pred[a], Gkm)[tgt]
        h = D[a, tgt]
        for b in np.where(np.isfinite(h))[0]:
            if a != b:
                rows.append((ok.point_id[a], ok.point_id[b], h[b] + snap_h[a] + snap_h[b], km[b] + ok.snap_km[a] + ok.snap_km[b]))
    od = pd.DataFrame(rows, columns=["from_id", "to_id", "road_h", "road_km"])

    # рёбра на уровне way + узлы концов (для стресс-теста)
    # через Arrow: DuckDB 1.2.2 не понимает строковый dtype pandas 3
    for name, df in (("meta", meta), ("pts", pts.drop(columns=["node"])), ("od", od)):
        con.register(name, pa.Table.from_pandas(df, preserve_index=False))
    con.execute("create or replace table road_ways as select * from meta")
    con.execute("create or replace table tuva_points as select * from pts")
    con.execute("create or replace table od_road as select * from od")
    np.save(ROOT / "data" / "tuva_graph_coords.npy", coords)
    edges.to_parquet(ROOT / "data" / "tuva_graph_edges.parquet")
    pts[["point_id", "node"]].to_parquet(ROOT / "data" / "tuva_graph_points.parquet")

    print(f"points={len(pts)} on_road={pts.on_road.sum()} od_pairs={len(od)}")
    print(pts[~pts.on_road][["name", "mun_upper", "population", "snap_km"]].to_string(index=False))


if __name__ == "__main__":
    main()
