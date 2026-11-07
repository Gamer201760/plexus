"""Ручные связи всех регионов → рёбра мультимодального графа РФ по сезонам.

Вход: data_manual/regions/<ОКТМО>.csv (+ tuva_links.csv), data_manual/regions/<ОКТМО>_remote.csv.
Выход (DuckDB):
  manual_links_ru — season (summer|winter), region_code, from_id, to_id, mode, kind, km, travel_h, wait_h, h,
                    freq_per_week, freq_assumed, confidence, source_url  (одна строка на связь и сезон)
  manual_remote   — н.п. без круглогодичной дороги (all_season_road = no) с источником.
                    Остальные строки _remote.csv (перечни для ККТ, выплат медикам и т.п.) отсутствие дороги
                    не доказывают и в модель не идут.

Правила:
  - season all → лето и зима; пустой season (неизвестен, confidence=low) → не используется.
  - ext:<Город> → н.п. с тем же названием (без «г.», «село»…), ближайший к другому концу связи;
    не найден (зарубежные пункты и т.п.) → связь отбрасывается, пишется в лог.
  - Переправа (ferry / ice_crossing / pontoon_bridge): подъезд по берегам + пересечение; km в CSV — ширина
    створа. Паром между н.п. дальше CROSSING_MAX_KM — линия (морской паром), считается как river.
  - Ожидание рейса (air, river, линейный паром) — половина интервала, не больше WAIT_CAP_H:
    поездку планируют под расписание, ждут не дольше суток. Частота не найдена → DEFAULT_FREQ, помечено.
"""
import csv
import os
import re
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "casechamp.duckdb"
MANUAL = ROOT / "data_manual"

# допущения модели — менять здесь и проверять чувствительность
MODE_KMH = {"air": 200, "winter_road": 30, "river": 20}            # как в multimodal_tuva.py
MODE_OVERHEAD_H = {"air": 1.0, "winter_road": 0.0, "river": 0.5}
DETOUR = {"air": 1.0, "winter_road": 1.25, "river": 1.3}           # км по маршруту / по прямой, если km нет
CROSSING_MAX_KM = 30.0
CROSSING_KMH = {"ferry": 10, "ice_crossing": 20, "pontoon_bridge": 20}
CROSSING_OVERHEAD_H = {"ferry": 0.5, "ice_crossing": 0.0, "pontoon_bridge": 0.0}
CROSSING_DEFAULT_KM = 1.0          # ширина створа, если не указана
APPROACH_KMH, APPROACH_DETOUR = 40, 1.3
DEFAULT_FREQ = 1.0                 # рейсов в неделю, если частота не найдена
WAIT_CAP_H = 24.0
SEASONS = ("summer", "winter")
TUVA_CODE = "93000000"


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


def base_name(name):
    """«г. Кызыл», «пгт Приобье», «деревня  Борцы» → «кызыл», «приобье», «борцы»."""
    s = re.sub(r"\s+", " ", str(name)).strip().replace("ё", "е").replace("Ё", "Е")
    parts = s.split(" ", 1)
    if len(parts) == 2 and (parts[0][:1].islower() or parts[0].endswith(".")):
        s = parts[1]
    return s.casefold()


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_raw():
    rows = []
    for p in sorted((MANUAL / "regions").glob("*.csv")):
        if re.fullmatch(r"\d{8}", p.stem):
            rows += [dict(r, region_code=p.stem) for r in read_csv(p)]
    rows += [dict(r, region_code=TUVA_CODE) for r in read_csv(MANUAL / "tuva_links.csv")]
    df = pd.DataFrame(rows)
    for c in ("km", "freq_per_week"):
        df[c] = pd.to_numeric(df[c].replace("", np.nan))
    return df


def resolve_ext(df, pts):
    """ext:<Город> → point_id: тот же базовый род названия, ближайший к другому концу связи."""
    by_name = pts.groupby("base").indices
    lat, lon = pts.lat.values, pts.lon.values
    pos = pd.Series(np.arange(len(pts)), index=pts.point_id)
    unresolved = []
    for end, other in (("from_id", "to_id"), ("to_id", "from_id")):
        for i in df.index[df[end].str.startswith("ext:")]:
            cand = by_name.get(base_name(df.at[i, end][4:]))
            o = df.at[i, other]
            if cand is None:
                unresolved.append(df.at[i, end]); df.at[i, end] = None
                continue
            if o in pos.index:
                k = pos[o]
                cand = cand[[np.argmin(haversine_km(lat[k], lon[k], lat[cand], lon[cand]))]]
            else:
                cand = cand[[np.argmax(pts.population.values[cand])]]
            df.at[i, end] = pts.point_id.values[cand[0]]
    return df, sorted(set(unresolved))


def link_hours(df, pts):
    p = pts.set_index("point_id")
    a, b = p.loc[df.from_id], p.loc[df.to_id]
    geo = haversine_km(a.lat.values, a.lon.values, b.lat.values, b.lon.values)
    # дальний паром — линия; понтон/лёд дальше порога — неточная привязка н.п., но всё равно переправа
    crossing = df["mode"].isin(list(CROSSING_KMH)).values & ((df["mode"] != "ferry").values | (geo <= CROSSING_MAX_KM))
    line_mode = df["mode"].where(df["mode"].isin(list(MODE_KMH)), "river")      # морской паром — как линия
    km_line = df.km.fillna(pd.Series(geo * line_mode.map(DETOUR).values, index=df.index)).values
    travel_line = km_line / line_mode.map(MODE_KMH).values + line_mode.map(MODE_OVERHEAD_H).values
    cross_km = df.km.fillna(CROSSING_DEFAULT_KM).values
    approach_km = geo * APPROACH_DETOUR
    cm = df["mode"].map(CROSSING_KMH).fillna(1).values
    co = df["mode"].map(CROSSING_OVERHEAD_H).fillna(0).values
    travel_cross = approach_km / APPROACH_KMH + cross_km / cm + co
    scheduled = ~crossing & (df["mode"] != "winter_road").values
    freq = df.freq_per_week.where(df.freq_per_week > 0)
    wait = np.where(scheduled, np.minimum(168 / freq.fillna(DEFAULT_FREQ).values / 2, WAIT_CAP_H), 0.0)
    return df.assign(kind=np.where(crossing, "crossing", "line"),
                     km=np.where(crossing, approach_km + cross_km, km_line),
                     travel_h=np.where(crossing, travel_cross, travel_line), wait_h=wait,
                     h=np.where(crossing, travel_cross, travel_line) + wait,
                     freq_assumed=scheduled & freq.isna().values)


def main():
    os.chdir(ROOT)
    con = duckdb.connect(str(DB))
    pts = con.sql("""select oktmo as point_id, settlement as name, population, latitude as lat, longitude as lon
                     from stg_settlements where object_level = 'Населенный пункт' and latitude is not null""").df()
    pts["base"] = pts.name.map(base_name)
    raw = load_raw()
    n0 = len(raw)
    df = raw[raw.season.isin(["all", *SEASONS])].copy()
    n_noseason = n0 - len(df)
    df, unresolved = resolve_ext(df, pts)
    known = set(pts.point_id)
    bad = df.from_id.isna() | df.to_id.isna() | ~df.from_id.isin(known) | ~df.to_id.isin(known) | (df.from_id == df.to_id)
    n_bad = int(bad.sum())
    df = link_hours(df[~bad].reset_index(drop=True), pts)
    df = pd.concat([df[df.season.isin(["all", s])].assign(season=s) for s in SEASONS], ignore_index=True)
    cols = ["season", "region_code", "from_id", "to_id", "mode", "kind", "km", "travel_h", "wait_h", "h",
            "freq_per_week", "freq_assumed", "confidence", "source_url"]
    out = df[cols]
    con.register("ml", pa.Table.from_pandas(out, preserve_index=False))
    con.execute("create or replace table manual_links_ru as select * from ml")

    rem = []
    for p in sorted((MANUAL / "regions").glob("*_remote.csv")):
        rem += [dict(r, region_code=p.stem[:8]) for r in read_csv(p) if r["all_season_road"] == "no"]
    rem = pd.DataFrame(rem, columns=["point_id", "name", "status", "all_season_road", "note", "source_url", "region_code"])
    rem = rem[rem.point_id.isin(known)].drop_duplicates("point_id")
    con.register("rem", pa.Table.from_pandas(rem[["point_id", "region_code", "status", "note", "source_url"]], preserve_index=False))
    con.execute("create or replace table manual_remote as select * from rem")

    print(f"связей в CSV {n0}: без сезона {n_noseason}, не сопоставлено {n_bad}; ext не найдены: {', '.join(unresolved)}")
    print(con.sql("""select season, mode, kind, count(*) n, count(*) filter (freq_assumed) freq_assumed,
                            round(median(h), 1) med_h from manual_links_ru group by all order by all"""))
    print(f"manual_remote: {len(rem)} н.п. без круглогодичной дороги")


if __name__ == "__main__":
    sys.exit(main())
