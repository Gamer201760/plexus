"""Собрать casechamp.duckdb из data/raw: прогнать sql/*.sql по порядку.

DuckDB закреплён на 1.2.2: у ВМ нет AVX, свежие сборки падают с SIGILL.
"""
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "casechamp.duckdb"

if __name__ == "__main__":
    os.chdir(ROOT)  # пути в sql/*.sql относительно корня проекта
    con = duckdb.connect(str(DB))
    for f in sorted((ROOT / "sql").glob("*.sql")):
        print(f"run {f.name}")
        con.execute(f.read_text())
    for (t,) in con.sql("select table_name from information_schema.tables order by 1").fetchall():
        print(f"  {t}: {con.sql(f'select count(*) from {t}').fetchone()[0]}")
