"""Мультимодальная матрица Тывы по сезонам: дороги (od_road) + ручные связи (data_manual/tuva_links.csv).

Граф на уровне точек: рёбра = кратчайшие дорожные пути между точками + авиа/зимник/река.
Время рейса = расстояние / скорость + накладные расходы (посадка, ожидание на площадке).
Ожидание рейса: вариант wait='headway' — половина интервала между рейсами (168 ч / частота / 2);
для рейсов без найденной частоты берётся AIR_DEFAULT_FREQ (допущение, помечено в справочнике).
Вариант wait='none' — без ожидания, верхняя граница доступности.

Выход: od_multimodal(season, wait, from_id, to_id, hours, km, uses_air, uses_seasonal) в DuckDB.
"""
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "casechamp.duckdb"

# допущения модели — менять здесь и проверять чувствительность
MODE_KMH = {"air": 200, "winter_road": 30, "river": 20}     # Ми-8 ~200 км/ч крейсерская
MODE_OVERHEAD_H = {"air": 1.0, "winter_road": 0.0, "river": 0.5}
SEASONS = ("summer", "winter")
WAITS = ("headway", "none")
AIR_DEFAULT_FREQ = 1.0   # рейсов в неделю, если частота не найдена — допущение


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


def main():
    os.chdir(ROOT)
    con = duckdb.connect(str(DB))
    pts = con.sql("select point_id, lat, lon from tuva_points").df()
    idx = {p: i for i, p in enumerate(pts.point_id)}
    n = len(pts)
    road = con.sql("select from_id, to_id, road_h as h, road_km as km from od_road").df()
    links = pd.read_csv(ROOT / "data_manual" / "tuva_links.csv", dtype={"from_id": str, "to_id": str})

    out = []
    for season in SEASONS:
      for wait in WAITS:
        e = road.assign(kind="road")
        lk = links[links.season.isin(["all", season])].copy()
        a, b = lk.from_id.map(idx), lk.to_id.map(idx)
        geo_km = haversine_km(pts.lat[a].values, pts.lon[a].values, pts.lat[b].values, pts.lon[b].values)
        lk["km"] = lk.km.fillna(pd.Series(geo_km, index=lk.index))
        lk["h"] = lk.km / lk["mode"].map(MODE_KMH) + lk["mode"].map(MODE_OVERHEAD_H)
        if wait == "headway":
            freq = lk.freq_per_week.fillna(AIR_DEFAULT_FREQ)
            lk["h"] += np.where(lk["mode"] == "air", 168 / freq / 2, 0)
        both = pd.concat([lk[["from_id", "to_id", "h", "km", "mode"]],
                          lk.rename(columns={"from_id": "to_id", "to_id": "from_id"})[["from_id", "to_id", "h", "km", "mode"]]])
        e = pd.concat([e, both.rename(columns={"mode": "kind"})], ignore_index=True)
        e = e.sort_values("h").drop_duplicates(["from_id", "to_id"])
        s, t = e.from_id.map(idx).values, e.to_id.map(idx).values
        G = coo_matrix((e.h.values, (s, t)), shape=(n, n)).tocsr()
        kind = {(i, j): k for i, j, k in zip(s, t, e.kind)}
        ekm = {(i, j): k for i, j, k in zip(s, t, e.km)}
        D, pred = dijkstra(G, directed=True, return_predecessors=True)
        for i in range(n):
            for j in range(n):
                if i == j or not np.isfinite(D[i, j]):
                    continue
                km, air, seas, cur = 0.0, False, False, j
                while cur != i:
                    p = pred[i, cur]; k = kind[(p, cur)]
                    km += ekm[(p, cur)]; air |= k == "air"; seas |= k in ("winter_road", "river"); cur = p
                out.append((season, wait, pts.point_id[i], pts.point_id[j], D[i, j], km, air, seas))

    od = pd.DataFrame(out, columns=["season", "wait", "from_id", "to_id", "hours", "km", "uses_air", "uses_seasonal"])
    con.register("od", pa.Table.from_pandas(od, preserve_index=False))
    con.execute("create or replace table od_multimodal as select * from od")
    con.register("lk", pa.Table.from_pandas(links, preserve_index=False))
    con.execute("create or replace table manual_links as select * from lk")
    print(con.sql("select season, wait, count(*) pairs, count(*) filter (uses_air) via_air, count(*) filter (uses_seasonal) via_seasonal from od_multimodal group by all order by all"))
    unreached = con.sql("""select p.name, p.population, s.season
        from tuva_points p cross join (select unnest(['summer','winter']) season) s
        where not exists (select 1 from od_multimodal o where o.season = s.season and o.wait = 'none' and o.to_id = p.point_id
                          and o.from_id = (select point_id from tuva_points where name = 'г. Кызыл'))
          and p.name <> 'г. Кызыл'""").df()
    print("недостижимы из Кызыла:\n", unreached.to_string(index=False))


if __name__ == "__main__":
    main()
