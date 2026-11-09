import glob
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from scipy.spatial import cKDTree

from inequality import gini, palma, theil
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "casechamp.duckdb"
R_EARTH = 6371.0

HALF_LIFE_H = (1, 2, 4)        # полупериод затухания Hansen; основной — 2 ч, остальные — чувствительность
HARRIS_T0_H = 0.5              # внутригородская поездка: без неё 1/t взрывается на t = 0
IDEAL_KMH = 90                 # скорость «по прямой» для эффективности сети
EFF_MIN_KM = 10                # ближе — отношение неустойчиво
ARIA_CLASSES = {"a": 250_000, "b": 48_000, "c": 18_000, "d": 5_000, "e": 1_000}
ARIA_BREAKS = [0.2, 2.4, 5.92, 10.53]
ARIA_LABELS = ["major_city", "inner_regional", "outer_regional", "remote", "very_remote"]
URBAN_PREFIX = ("г.", "город", "пгт", "рп", "кп", "гп", "дп")   # остальное — сельские н.п.
RAI_KM = 2.0
ALLSEASON_HW = ["motorway", "trunk", "primary", "secondary", "tertiary"]
UNPAVED = ["unpaved", "gravel", "dirt", "ground", "earth", "sand", "grass", "compacted", "fine_gravel", "mud",
           "ice", "snow", "wood"]
PAVED = ["asphalt", "paved", "concrete", "concrete:plates", "concrete:lanes", "paving_stones", "sett", "cobblestone"]
DENSIFY_KM = 0.25


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def allseason_vertices(path):
    """Вершины всесезонных дорог одного файла OSM, отрезки длиннее DENSIFY_KM дробятся."""
    t = pq.read_table(path, columns=["highway", "surface", "is_ferry", "is_seasonal", "lat", "lon"])
    hw = pc.replace_substring(t["highway"], "_link", "")
    surf = t["surface"]
    major = pc.and_(pc.is_in(hw, pa.array(ALLSEASON_HW)), pc.invert(pc.fill_null(pc.is_in(surf, pa.array(UNPAVED)), False)))
    paved = pc.fill_null(pc.is_in(surf, pa.array(PAVED)), False)
    keep = pc.and_(pc.or_(major, paved), pc.invert(pc.or_(pc.fill_null(t["is_ferry"], False), pc.fill_null(t["is_seasonal"], False))))
    t = t.filter(keep)
    lat = pc.list_flatten(t["lat"]).to_numpy(); lon = pc.list_flatten(t["lon"]).to_numpy()
    lens = pc.list_value_length(t["lat"]).to_numpy()
    wid = np.repeat(np.arange(len(lens)), lens)
    p = xyz(lat, lon)
    same = wid[1:] == wid[:-1]
    seg = np.linalg.norm(p[1:] - p[:-1], axis=1) * R_EARTH
    k = np.where(same, np.ceil(seg / DENSIFY_KM).astype(np.int64) - 1, 0)
    k = np.maximum(k, 0)
    if k.sum():
        i = np.repeat(np.arange(len(k)), k)
        f = (np.concatenate([np.arange(1, n + 1) for n in k[k > 0]]) / np.repeat(k[k > 0] + 1, k[k > 0]))[:, None]
        extra = p[i] + (p[i + 1] - p[i]) * f
        p = np.vstack([p, extra])
    return p


def rai(pts):
    """Расстояние (км) от н.п. до ближайшей всесезонной дороги: минимум по файлам округов."""
    q = xyz(pts.lat.values, pts.lon.values)
    best = np.full(len(pts), np.inf)
    for f in sorted(glob.glob(str(ROOT / "data" / "osm_ways" / "*.parquet"))):
        v = allseason_vertices(f)
        d, _ = cKDTree(v).query(q, distance_upper_bound=RAI_KM * 5 / R_EARTH)
        best = np.minimum(best, d * R_EARTH)
        print(f"  rai {Path(f).stem}: vertices {len(v)}", flush=True)
        del v
    return best


def main():
    os.chdir(ROOT)
    con = duckdb.connect(str(DB))
    con.execute("set threads = 4")
    con.execute("begin transaction")
    b = {f"b{h}": np.log(2) / h for h in HALF_LIFE_H}

    # --- рыночные индексы из np_city_times: всё в SQL (84 млн строк)
    aria_ab = " ,".join(f"min(t.best_h) filter (c.population >= {v}) as t_aria_{k}"
                        for k, v in ARIA_CLASSES.items() if k in "abc")
    con.execute(f"""
      create or replace temp table mk as
      select t.season, t.point_id, count(*) as reachable_markets,
             {", ".join(f"sum(c.population * exp(-{b[f'b{h}']} * cast(t.best_h as double))) as hansen_{h}h" for h in HALF_LIFE_H)},
             sum(c.population / (cast(t.best_h as double) + {HARRIS_T0_H})) as harris,
             {", ".join(f"sum(c.population) filter (t.best_h <= {h}) as cum_pop_{h}h" for h in (1, 2, 4))},
             min(t.road_h) filter (c.population >= 50000) as t_city50k_road_h,
             min(t.best_h) filter (c.population >= 50000) as t_city50k_best_h,
             {aria_ab}
      from np_city_times t join market_cities c using (city) group by all""")

    # --- эффективность сети: время по сети / время по прямой, по городам дальше EFF_MIN_KM
    con.execute(f"""
      create or replace temp table eff as
      with p as (select oktmo as point_id, latitude as lat, longitude as lon from stg_settlements
                 where object_level = 'Населенный пункт'),
      d as (select t.season, t.point_id, t.best_h, c.population,
                   2 * {R_EARTH} * asin(sqrt(pow(sin(radians(c.lat - p.lat) / 2), 2)
                     + cos(radians(p.lat)) * cos(radians(c.lat)) * pow(sin(radians(c.lon - p.lon) / 2), 2))) as km
            from np_city_times t join market_cities c using (city) join p using (point_id))
      select season, point_id, sum(best_h / (km / {IDEAL_KMH}) * population) / sum(population) as net_efficiency
      from d where km >= {EFF_MIN_KM} group by all""")

    acc = con.sql("""select a.*, s.latitude as lat, s.longitude as lon from np_access a
                     join stg_settlements s on s.oktmo = a.point_id and s.object_level = 'Населенный пункт'""").df()
    acc = acc[~acc.region.isin(["Москва", "Санкт-Петербург", "Севастополь"])]
    df = acc.merge(con.sql("select * from mk").df(), on=["season", "point_id"], how="left") \
            .merge(con.sql("select * from eff").df(), on=["season", "point_id"], how="left")
    df["reachable_markets"] = df.reachable_markets.fillna(0).astype(int)
    df["is_rural"] = ~df.name.str.split(" ", n=1).str[0].isin(URBAN_PREFIX)
    for c in [f"hansen_{h}h" for h in HALF_LIFE_H] + ["harris"] + [f"cum_pop_{h}h" for h in (1, 2, 4)]:
        df[c] = df[c].fillna(0.0)
    road = df[df.season == "road"]
    base = np.average(road.hansen_2h, weights=road.population.fillna(0).clip(lower=0))
    if not np.isfinite(base) or base <= 0:
        raise ValueError("positive population-weighted baseline is required")
    df["hansen_idx"] = df.hansen_2h / base * 100
    lh = np.log(df.harris.where(df.harris > 0))
    lr = np.log(road.harris[road.harris > 0])
    df["remoteness_ca"] = (1 - (lh - lr.min()) / (lr.max() - lr.min())).clip(0, 1).fillna(1.0)

    # --- ARIA+: классы A, B, C — города (с ЖД/авиа), C–E — ближайший н.п. по графу; C — минимум из двух
    df["t_aria_c"] = np.fmin(df.t_aria_c, df.t_centre_18k_h)
    df["t_aria_d"], df["t_aria_e"] = df.t_centre_5k_h, df.t_centre_1k_h
    aria = 0.0
    road = df[df.season == "road"]
    for k in ARIA_CLASSES:
        mean = road[f"t_aria_{k}"].mean()
        aria = aria + (df[f"t_aria_{k}"] / mean).clip(upper=3).fillna(3)
    df["aria"] = aria
    df["aria_class"] = pd.cut(df.aria, [-1, *ARIA_BREAKS, 16], labels=ARIA_LABELS).astype(str)

    df["oecd_remote"] = (df.t_city50k_road_h > 1) | df.t_city50k_road_h.isna()
    df["lancet_2h"] = df.t_district_center_h <= 2
    print("RAI: всесезонные дороги из OSM ...", flush=True)
    pts = df[df.season == "road"][["point_id", "lat", "lon"]]
    pts = pts.assign(km_allseason_road=rai(pts))
    df = df.merge(pts[["point_id", "km_allseason_road"]], on="point_id", how="left")
    df["rai_2km"] = df.km_allseason_road <= RAI_KM

    cols = ["reachable_markets", "season", "point_id", "name", "region", "mun_upper", "population", "is_rural", "is_dc", "on_road",
            "manual_only", "no_all_season_road", "hansen_1h", "hansen_2h", "hansen_4h", "hansen_idx", "harris",
            "remoteness_ca", "cum_pop_1h", "cum_pop_2h", "cum_pop_4h", "t_city50k_road_h", "t_city50k_best_h",
            "oecd_remote", "t_aria_a", "t_aria_b", "t_aria_c", "t_aria_d", "t_aria_e", "aria", "aria_class",
            "t_district_center_h", "lancet_2h", "km_allseason_road", "rai_2km", "net_efficiency", "t_capital_best_h"]
    out = df[cols]
    con.register("o", pa.Table.from_pandas(out, preserve_index=False))
    con.execute("create or replace table idx_np as select * from o")
    con.unregister("o")

    # --- сезонность и зависимость от ручных связей
    con.execute("""
      create or replace table idx_np_gap as
      with w as (pivot (select point_id, season, hansen_2h from idx_np) on season using first(hansen_2h))
      select n.point_id, n.name, n.region, n.mun_upper, n.population, w.road, w.summer, w.winter,
             1 - w.road / nullif(greatest(w.summer, w.winter), 0) as exposure_manual,
             1 - least(w.summer, w.winter) / nullif(greatest(w.summer, w.winter), 0) as seasonal_gap,
             case when w.summer >= w.winter then 'summer' else 'winter' end as better_season
      from w join idx_np n on n.point_id = w.point_id and n.season = 'road'""")

    # --- агрегаты МО и регионов
    agg = """sum(population) as population, count(*) as n_np,
             coalesce(sum(population) filter (reachable_markets > 0), 0) as covered_population,
             count(*) filter (reachable_markets > 0) as covered_settlements,
             sum(population * hansen_1h) / sum(population) as hansen_1h,
             sum(population * hansen_2h) / sum(population) as hansen_2h,
             sum(population * hansen_4h) / sum(population) as hansen_4h,
             sum(population * hansen_idx) / sum(population) as hansen_idx,
             sum(population * remoteness_ca) / sum(population) as remoteness_ca,
             sum(population * aria) / sum(population) as aria,
             sum(population * cum_pop_4h) / sum(population) as daily_access_pop,
             coalesce(sum(population) filter (oecd_remote), 0) / sum(population) as share_oecd_remote,
             coalesce(sum(population) filter (t_city50k_best_h > 1 or t_city50k_best_h is null), 0) / sum(population) as share_city50k_over_1h,
             coalesce(sum(population) filter (lancet_2h), 0) / sum(population) as share_lancet_2h,
             coalesce(sum(population) filter (is_rural and rai_2km), 0) / nullif(sum(population) filter (is_rural), 0) as rai,
             sum(population * net_efficiency) / nullif(sum(population) filter (net_efficiency is not null), 0) as net_efficiency,
             coalesce(sum(population) filter (aria_class in ('remote', 'very_remote')), 0) / sum(population) as share_aria_remote,
             coalesce(sum(population) filter (t_capital_best_h is null), 0) as pop_no_capital"""
    con.execute(f"create or replace table idx_mo as select season, region, mun_upper, {agg} from idx_np group by all")
    con.execute(f"create or replace table idx_region as select season, region, {agg} from idx_np group by all")

    # неравенство и порог достаточности
    rows, theils = [], []
    n = con.sql("select season, region, population, hansen_2h from idx_np where population > 0").df()
    g = n[n.season == "road"]
    o = np.argsort(g.hansen_2h.values); cw = np.cumsum(g.population.values[o]) / g.population.sum()
    med = g.hansen_2h.values[o][np.searchsorted(cw, 0.5)]              # медиана по жителям, road — общий порог
    for season, g in n.groupby("season"):
        x, w = g.hansen_2h.values, g.population.values.astype(float)
        T = theil(x, w)
        m = np.average(x, weights=w)
        between = 0.0
        for region, r in g.groupby("region"):
            xr, wr = r.hansen_2h.values, r.population.values.astype(float)
            mr = np.average(xr, weights=wr)
            between += wr.sum() / w.sum() * (mr / m) * np.log(mr / m) if mr > 0 else 0
            rows.append({"season": season, "region": region, "gini": gini(xr, wr), "palma": palma(xr, wr),
                         "theil": theil(xr, wr),
                         "access_poor_share": wr[xr < 0.5 * med].sum() / wr.sum()})
        theils.append({"season": season, "theil": T, "between_regions": between, "within_regions": T - between,
                       "gini": gini(x, w), "palma": palma(x, w), "access_poor_share": w[x < 0.5 * med].sum() / w.sum()})
    ineq = pd.DataFrame(rows)
    con.register("ineq", pa.Table.from_pandas(ineq, preserve_index=False))
    con.execute("create or replace table idx_region as select r.*, i.gini, i.palma, i.theil, i.access_poor_share, "
                "r.share_oecd_remote > 0.5 as oecd_remote_region from idx_region r left join ineq i using (season, region)")
    con.register("th", pa.Table.from_pandas(pd.DataFrame(theils), preserve_index=False))
    con.execute("create or replace table idx_theil as select * from th")

    print(con.sql("select * from idx_theil order by season"))
    print(con.sql("""select season, round(sum(population * hansen_idx) / sum(population), 1) hansen,
                            round(sum(population) filter (oecd_remote) / sum(population), 3) oecd_remote,
                            round(sum(population) filter (lancet_2h) / sum(population), 3) lancet,
                            round(sum(population) filter (is_rural and rai_2km) / sum(population) filter (is_rural), 3) rai,
                            round(sum(population * aria) / sum(population), 2) aria
                     from idx_np group by 1 order by 1"""))

    con.execute("create or replace table index_model_metadata as select ?::varchar as model_version, ?::double as normalization_base, 2 as half_life_h", ["hansen-frequency-v2", float(base)])
    con.execute("commit")


if __name__ == "__main__":
    main()
