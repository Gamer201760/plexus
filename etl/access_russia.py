"""Время доступа от каждого н.п. России: райцентр, столица региона, 180 крупных городов (рынки).

Уровни сети:
  1. Дороги (data/graph_ru) — от н.п. до каждого города и до своего райцентра.
  2. Магистраль между городами (Точно, stg_intercity): ЖД и авиа с накладными расходами,
     пересадки — кратчайшие пути на графе городов (Флойд–Уоршелл).
  best(i, j) = min_k [ road(i, k) + city(k, j) ],  city(k, k) = 0  → включает и чисто дорожный путь.

Выход (DuckDB):
  np_access       — season, point_id, region, population, t_district_center_h, t_capital_h, t_capital_best_h,
                    nearest_city, t_nearest_city_h, on_road, manual_only, no_all_season_road
  np_city_times   — season, point_id, city, road_h, best_h  (только best_h <= MAX_H)
Сценарии (колонка season): road — только дороги; summer / winter — плюс ручные связи сезона
(manual_links_ru из etl/manual_links.py: местная авиация, зимники, реки, переправы). Н.п. без дороги
в радиусе привязки, но с ручной связью, получают свой узел (manual_only). Ожидание местного рейса — в весе
ребра (manual_links.py); магистральные рейсы Точно считаются регулярными.
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
from graphlib import GRAPH, build_csr, load_edges  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "casechamp.duckdb"

OVERHEAD_H = {"rail": 1.0, "air": 2.5}    # доезд до вокзала/аэропорта, регистрация, ожидание — допущение
SNAP_KMH = 15
MAX_H = 72.0                               # дальше — не храним (вес в индексе ~0)
DC_LIMIT_H = 24.0                          # радиус поиска райцентра
# у Московской области нет столицы в списке Точно; функциональный центр — Москва
CAPITAL_OVERRIDE = {"Московская область": "Москва"}
BATCH = 8                                  # источников дейкстры за вызов: 8 × узлы × 8 Б ≈ 1 ГБ
SCENARIOS = os.environ.get("SCENARIOS", "road,summer,winter").split(",")


def manual_edges(con, scenario, pts, n):
    """Рёбра ручных связей сценария + виртуальные узлы для н.п. без дороги. Возвращает (src, dst, w, pts, N)."""
    pts = pts.assign(manual_only=False)
    empty = np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64), np.empty(0, dtype=np.float32)
    if scenario == "road":
        return (*empty, pts, n)
    ml = con.sql("select from_id, to_id, h from manual_links_ru where season = ?", params=[scenario]).df()
    linked = pts.point_id.isin(set(ml.from_id) | set(ml.to_id))
    virt = (linked & ~pts.on_road).values
    pts.loc[virt, "node"] = n + np.arange(virt.sum())
    pts.loc[virt, "snap_h"] = 0.0
    pts.loc[virt, "manual_only"] = True
    p = pts.set_index("point_id")
    ml = ml[ml.from_id.isin(p.index[p.node >= 0]) & ml.to_id.isin(p.index[p.node >= 0])]
    a, b = p.loc[ml.from_id], p.loc[ml.to_id]
    w = ml.h.values + a.snap_h.values + b.snap_h.values
    print(f"[{scenario}] ручных рёбер {len(ml)}, новых узлов (н.п. без дороги) {int(virt.sum())}", flush=True)
    return a.node.values.astype(np.int64), b.node.values.astype(np.int64), w.astype(np.float32), pts, n + int(virt.sum())


def run(scenario, con, base, pts0, cities, T0, remote):
    """Доступ для одного сценария → (acc, times)."""
    src, dst, h, n = base
    ms, md, mw, pts, N = manual_edges(con, scenario, pts0, n)
    G = build_csr(np.concatenate([src, ms]), np.concatenate([dst, md]), np.concatenate([h, mw]), N).astype(np.float64)
    pts["in_graph"] = pts.node >= 0
    on = pts[pts.in_graph].reset_index(drop=True)
    on["node"] = on.node.astype(np.int64)
    C = len(cities)
    ci = {c: i for i, c in enumerate(cities.city)}

    # дороги (+ ручные связи): от каждого города по графу; храним только столбцы узлов н.п. и городов (лимит памяти ~11 ГБ)
    print(f"[{scenario}] dijkstra from cities ...", flush=True)
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
    T = np.minimum(T0, R_cc + cities.snap_h.values[:, None] + cities.snap_h.values[None, :])
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

    # --- свой райцентр: один многоисточниковый поиск от всех райцентров — ближайший райцентр для каждого узла
    # (2300 отдельных поисков на графе РФ — часы; ближайший почти всегда и есть свой — флаг dc_is_own)
    print(f"[{scenario}] dijkstra from district centers ...", flush=True)
    dcs = on[on.is_dc].drop_duplicates(["region", "mun_upper"])
    dc_nodes = dcs.node.values.astype(np.int64)
    d, _, src_dc = dijkstra(G, directed=False, indices=dc_nodes, min_only=True, return_predecessors=True, limit=DC_LIMIT_H)
    own = on.merge(dcs[["region", "mun_upper", "node"]].rename(columns={"node": "own_dc_node"}),
                   on=["region", "mun_upper"], how="left").own_dc_node.values
    dc_snap = pd.Series(dcs.snap_h.values, index=dcs.node.values)
    near_dc = src_dc[pnode]
    t_dc = d[pnode] + on.snap_h.values + dc_snap.reindex(near_dc).fillna(0).values
    t_dc[np.isinf(t_dc) | (near_dc < 0)] = np.nan
    dc_is_own = (near_dc == own)
    del d, src_dc, G

    acc = pd.DataFrame({
        "point_id": on.point_id, "t_district_center_h": t_dc, "dc_is_own": dc_is_own, "t_capital_h": np.where(np.isinf(t_cap), np.nan, t_cap),
        "t_capital_best_h": np.where(np.isinf(t_cap_best), np.nan, t_cap_best),
        "nearest_city": cities.city.values[near], "t_nearest_city_h": road[rows, near],
    })
    acc = pts[["point_id", "name", "region", "mun_upper", "population", "is_dc", "on_road", "manual_only", "snap_km"]].merge(acc, on="point_id", how="left")
    acc.insert(0, "season", scenario)
    acc["no_all_season_road"] = acc.point_id.isin(remote)
    for c in ("t_nearest_city_h",):
        acc[c] = acc[c].where(np.isfinite(acc[c]))

    ii, jj = np.nonzero(best <= MAX_H)
    times = pa.table({"point_id": on.point_id.values[ii],
                      "city": cities.city.values[jj], "road_h": road[ii, jj], "best_h": best[ii, jj]})
    return acc, times


def main():
    os.chdir(ROOT)
    e = load_edges()
    n = pq.read_metadata(GRAPH / "nodes.parquet").num_rows
    base = (e["src"].astype(np.int64), e["dst"].astype(np.int64), e["h"].astype(np.float32), n)
    del e
    nodes = pq.read_table(GRAPH / "nodes.parquet", columns=["lat", "lon"]).to_pandas()
    pts = pq.read_table(GRAPH / "points.parquet").to_pandas()
    con = duckdb.connect(str(DB))
    meta = con.sql("""select oktmo as point_id, settlement as name, region, mun_upper, population
                      from stg_settlements where object_level = 'Населенный пункт'""").df()
    pts = pts.drop(columns=["region", "population"], errors="ignore").merge(meta, on="point_id")
    pts["snap_h"] = pts.snap_km / SNAP_KMH
    pts["is_dc"] = pts.groupby(["region", "mun_upper"]).population.transform("max") == pts.population
    print(f"graph nodes={n}, points on road={int(pts.on_road.sum())}/{len(pts)}")
    has_manual = {"manual_links_ru", "manual_remote"} <= set(con.sql("show tables").df().name)
    if not has_manual and set(SCENARIOS) - {"road"}:
        sys.exit("нет manual_links_ru — сначала uv run python etl/manual_links.py")
    remote = set(con.sql("select point_id from manual_remote").df().point_id) if has_manual else set()

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
    del nodes
    C = len(cities)

    # --- магистраль между городами: ЖД/авиа с накладными (дороги добавляются в каждом сценарии)
    ic = con.sql("select city_from, city_to, transport_type, distance_hr from stg_intercity where distance_hr is not null").df()
    ci = {c: i for i, c in enumerate(cities.city)}
    T0 = np.full((C, C), np.inf); np.fill_diagonal(T0, 0)
    for mode, oh in OVERHEAD_H.items():
        s = ic[ic.transport_type == mode]
        a, b = s.city_from.map(ci).values, s.city_to.map(ci).values
        np.minimum.at(T0, (a, b), s.distance_hr.values + oh)

    con.execute("drop table if exists np_access"); con.execute("drop table if exists np_city_times")
    for scenario in SCENARIOS:
        acc, times = run(scenario, con, base, pts, cities, T0, remote)
        con.register("acc", pa.Table.from_pandas(acc, preserve_index=False))
        con.register("times", times)
        if scenario == SCENARIOS[0]:
            con.execute("create table np_access as select * from acc")
            con.execute("create table np_city_times as select ?::varchar as season, * from times", [scenario])
        else:
            con.execute("insert into np_access by name select * from acc")
            con.execute("insert into np_city_times select ?::varchar as season, * from times", [scenario])
        con.unregister("acc"); con.unregister("times")
        print(f"[{scenario}] np_city_times rows={times.num_rows}", flush=True)
        del acc, times
    con.register("cities", pa.Table.from_pandas(cities.drop(columns=["point_id", "on_road"]), preserve_index=False))
    con.execute("create or replace table market_cities as select * from cities")
    print(con.sql("""select season, count(t_district_center_h) dc, count(t_capital_h) cap,
                            count(*) filter (manual_only) manual_only,
                            round(median(t_district_center_h),2) med_dc, round(median(t_capital_best_h),2) med_cap_best,
                            sum(population) filter (t_capital_best_h is null) pop_no_capital
                     from np_access group by season order by season"""))


if __name__ == "__main__":
    main()
