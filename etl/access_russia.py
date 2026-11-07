"""Время доступа от каждого н.п. России: райцентр, столица региона, 180 крупных городов (рынки).

Уровни сети:
  1. Дороги (data/graph_ru) — от н.п. до каждого города и до своего райцентра.
  2. Магистраль между городами (Точно, stg_intercity): ЖД и авиа с накладными расходами,
     пересадки — кратчайшие пути на графе городов (Флойд–Уоршелл).
  best(i, j) = min_k [ road(i, k) + city(k, j) ],  city(k, k) = 0  → включает и чисто дорожный путь.

Выход (DuckDB):
  np_access       — point_id, region, population, t_district_center_h, t_capital_h, t_capital_best_h,
                    nearest_city, t_nearest_city_h, on_road
  np_city_times   — point_id, city, road_h, best_h  (только best_h <= MAX_H)
Ожидание рейса (частоты) здесь не учитывается — магистральные рейсы считаются регулярными.
Поиск по дорогам — неориентированный: ошибки oneway в OSM иначе «запирают» отдельные н.п.
(пример: точка привязки Рыбинска только с исходящим ребром). На масштабе н.п.→город эффект oneway мал.
"""
import os
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.sparse.csgraph import dijkstra, floyd_warshall

sys.path.insert(0, str(Path(__file__).parent))
from graphlib import GRAPH, load_graph  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "casechamp.duckdb"

OVERHEAD_H = {"rail": 1.0, "air": 2.5}    # доезд до вокзала/аэропорта, регистрация, ожидание — допущение
SNAP_KMH = 15
MAX_H = 72.0                               # дальше — не храним (вес в индексе ~0)
DC_LIMIT_H = 24.0                          # радиус поиска райцентра
# у Московской области нет столицы в списке Точно; функциональный центр — Москва
CAPITAL_OVERRIDE = {"Московская область": "Москва"}
BATCH = 8                                  # источников дейкстры за вызов: 8 × узлы × 8 Б ≈ 1 ГБ


def main():
    os.chdir(ROOT)
    G, e, n = load_graph("h")
    G = G.astype(np.float64)   # scipy иначе конвертирует граф заново в каждом вызове dijkstra
    del e
    nodes = pq.read_table(GRAPH / "nodes.parquet", columns=["lat", "lon"]).to_pandas()
    pts = pq.read_table(GRAPH / "points.parquet").to_pandas()
    con = duckdb.connect(str(DB))
    meta = con.sql("""select oktmo as point_id, settlement as name, region, mun_upper, population
                      from stg_settlements where object_level = 'Населенный пункт'""").df()
    pts = pts.drop(columns=["region", "population"], errors="ignore").merge(meta, on="point_id")
    pts["snap_h"] = pts.snap_km / SNAP_KMH
    pts["is_dc"] = pts.groupby(["region", "mun_upper"]).population.transform("max") == pts.population
    on = pts[pts.on_road].reset_index(drop=True)
    print(f"graph nodes={n}, points on road={len(on)}/{len(pts)}")

    # --- города: привязка к ближайшему н.п. с тем же ОКТМО, иначе — ближайший узел по координатам
    cities = con.sql("""select distinct city_from as city, oktmo_from as oktmo, region_from as region,
                               is_capital_from as is_capital, population_from as population, lat_from as lat, lon_from as lon
                        from stg_intercity""").df()
    cities = cities.merge(pts[["point_id", "node", "on_road", "snap_h"]], left_on="oktmo", right_on="point_id", how="left")
    miss = cities.node.isna() | ~cities.on_road.fillna(False).astype(bool)
    if miss.any():
        from scipy.spatial import cKDTree
        tree = cKDTree(np.c_[nodes.lat, nodes.lon])
        _, k = tree.query(np.c_[cities.lat[miss], cities.lon[miss]])
        cities.loc[miss, "node"] = k; cities.loc[miss, "snap_h"] = 0.0
    cities["node"] = cities.node.astype(np.int64)
    C = len(cities)

    # --- матрица городов: ЖД/авиа с накладными + дороги (из графа), пересадки — Флойд–Уоршелл
    ic = con.sql("select city_from, city_to, transport_type, distance_hr from stg_intercity where distance_hr is not null").df()
    ci = {c: i for i, c in enumerate(cities.city)}
    T = np.full((C, C), np.inf); np.fill_diagonal(T, 0)
    for mode, oh in OVERHEAD_H.items():
        s = ic[ic.transport_type == mode]
        a, b = s.city_from.map(ci).values, s.city_to.map(ci).values
        np.minimum.at(T, (a, b), s.distance_hr.values + oh)

    # дороги: от каждого города по графу; храним только столбцы узлов н.п. и городов (лимит памяти ~11 ГБ)
    print("dijkstra from cities ...", flush=True)
    cnode = cities.node.values
    pnode = on.node.values
    R_pts = np.empty((C, len(on)), dtype=np.float32)
    R_cc = np.empty((C, C), dtype=np.float64)
    for b0 in range(0, C, BATCH):
        idx = cnode[b0:b0 + BATCH]
        d = np.atleast_2d(dijkstra(G, directed=False, indices=idx, limit=MAX_H))
        R_pts[b0:b0 + len(idx)] = d[:, pnode]
        R_cc[b0:b0 + len(idx)] = d[:, cnode]
        del d
        print(f"  cities {b0 + len(idx)}/{C}", flush=True)
    T = np.minimum(T, R_cc + cities.snap_h.values[:, None] + cities.snap_h.values[None, :])
    np.fill_diagonal(T, 0)
    F = floyd_warshall(T)

    # дорога н.п. → город: граф неориентирован почти везде; берём путь город → н.п. (односторонки — малая погрешность)
    road = (R_pts.T + on.snap_h.values[:, None] + cities.snap_h.values[None, :]).astype(np.float32)
    del R_pts
    best = np.empty_like(road)
    for j in range(C):                         # min_k road(i,k) + F(k,j)
        best[:, j] = np.min(road + F[:, j][None, :].astype(np.float32), axis=1)

    # --- столица региона и ближайший крупный город
    cap = cities[cities.is_capital].drop_duplicates("region").set_index("region")
    for region, city in CAPITAL_OVERRIDE.items():
        cap.loc[region, "city"] = city
    cap_idx = on.region.map(lambda r: ci.get(cap.city.get(r)) if r in cap.index else None)
    rows = np.arange(len(on))
    has_cap = cap_idx.notna().values
    t_cap = np.full(len(on), np.nan); t_cap_best = np.full(len(on), np.nan)
    t_cap[has_cap] = road[rows[has_cap], cap_idx[has_cap].astype(int)]
    t_cap_best[has_cap] = best[rows[has_cap], cap_idx[has_cap].astype(int)]
    near = np.argmin(road, axis=1)

    # --- свой райцентр: дейкстра от каждого райцентра с ограничением радиуса
    print("dijkstra from district centers ...", flush=True)
    # один многоисточниковый поиск от всех райцентров: ближайший райцентр для каждого узла
    # (2300 отдельных поисков на графе РФ — часы; ближайший почти всегда и есть свой — флаг dc_is_own)
    dcs = on[on.is_dc].drop_duplicates(["region", "mun_upper"])
    dc_nodes = dcs.node.values.astype(np.int64)
    d, _, src = dijkstra(G, directed=False, indices=dc_nodes, min_only=True, return_predecessors=True, limit=DC_LIMIT_H)
    own = on.merge(dcs[["region", "mun_upper", "node"]].rename(columns={"node": "own_dc_node"}),
                   on=["region", "mun_upper"], how="left").own_dc_node.values
    dc_snap = pd.Series(dcs.snap_h.values, index=dcs.node.values)
    near_dc = src[pnode]
    t_dc = d[pnode] + on.snap_h.values + dc_snap.reindex(near_dc).fillna(0).values
    t_dc[np.isinf(t_dc) | (near_dc < 0)] = np.nan
    dc_is_own = (near_dc == own)
    del d, src

    acc = pd.DataFrame({
        "point_id": on.point_id, "t_district_center_h": t_dc, "dc_is_own": dc_is_own, "t_capital_h": np.where(np.isinf(t_cap), np.nan, t_cap),
        "t_capital_best_h": np.where(np.isinf(t_cap_best), np.nan, t_cap_best),
        "nearest_city": cities.city.values[near], "t_nearest_city_h": road[rows, near],
    })
    acc = pts[["point_id", "name", "region", "mun_upper", "population", "is_dc", "on_road", "snap_km"]].merge(acc, on="point_id", how="left")

    ii, jj = np.nonzero(best <= MAX_H)
    times = pa.table({"point_id": on.point_id.values[ii], "city": cities.city.values[jj],
                      "road_h": road[ii, jj], "best_h": best[ii, jj]})
    con.register("acc", pa.Table.from_pandas(acc, preserve_index=False))
    con.execute("create or replace table np_access as select * from acc")
    con.register("times", times)
    con.execute("create or replace table np_city_times as select * from times")
    con.register("cities", pa.Table.from_pandas(cities.drop(columns=["point_id", "on_road"]), preserve_index=False))
    con.execute("create or replace table market_cities as select * from cities")
    print(con.sql("""select count(*) n, count(t_district_center_h) dc, count(t_capital_h) cap,
                            round(median(t_district_center_h),2) med_dc, round(median(t_capital_h),2) med_cap
                     from np_access"""))
    print(f"np_city_times rows={times.num_rows}")


if __name__ == "__main__":
    main()
