import os
import duckdb

from artifacts import ROOT, file_record, revision, write_json


DB = ROOT / "data" / "casechamp.duckdb"
REQUIRED = {
    "intercity": "*.parquet", "settlements": "*.parquet",
    "bdmo_no_regular_transport": "*.csv", "bdmo_roads_substandard": "*.csv",
    "bdmo_roads_length": "*.parquet", "bdmo_budget_spend": "*.parquet",
}


def main() -> None:
    os.chdir(ROOT)
    missing = [f"data/raw/{name}/{pattern}" for name, pattern in REQUIRED.items()
               if not list((ROOT / "data" / "raw" / name).glob(pattern))]
    if missing:
        raise FileNotFoundError("missing inputs: " + ", ".join(missing)
                                + "; restore with uv run python etl/download.py")
    DB.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB)) as con:
        con.execute("begin transaction")
        for path in sorted((ROOT / "sql").glob("*.sql")):
            print(f"run {path.name}", flush=True)
            con.execute(path.read_text())
        tables = {name: con.sql(f'SELECT count(*) FROM "{name}"').fetchone()[0]
                  for (name,) in con.sql("show tables").fetchall()}
        con.execute("commit")
    inputs = [file_record(path) for name, pattern in REQUIRED.items()
              for path in sorted((ROOT / "data" / "raw" / name).glob(pattern))]
    write_json(ROOT / "data" / "load-manifest.json", {
        "schema_version": 1, "code": revision(), "inputs": inputs,
        "sql": [file_record(path) for path in sorted((ROOT / "sql").glob("*.sql"))],
        "tables": tables, "database": file_record(DB),
    })
    for name, count in tables.items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
