"""Выгрузить н.п. каждого региона в data_manual/regions_input/<ОКТМО региона>.csv — вход для сбора ручных связей."""
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data_manual" / "regions_input"

if __name__ == "__main__":
    os.chdir(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "casechamp.duckdb"), read_only=True)
    regions = con.sql("select oktmo, region from stg_settlements where object_level = 'Регион'").fetchall()
    for code, region in regions:
        con.execute(f"""copy (
            select oktmo as point_id, settlement as name, mun_upper, population, latitude as lat, longitude as lon,
                   population = max(population) over (partition by mun_upper) as is_district_center
            from stg_settlements where region = ? and object_level = 'Населенный пункт'
            order by mun_upper, population desc) to '{OUT / (code + ".csv")}' (header)""", [region])
    print(f"{len(regions)} регионов -> {OUT}")
