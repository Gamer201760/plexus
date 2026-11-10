import argparse
import hashlib
import json
import shutil
from pathlib import Path
from time import perf_counter

import duckdb
from catalog import identifier, table_ddl
from client import ClickHouse

ROOT = Path(__file__).resolve().parents[2]


def export_table(con: duckdb.DuckDBPyConnection, query: str, target: Path) -> None:
    columns = con.execute("DESCRIBE (" + query + ")").fetchall()
    fields = ",".join(
        f"CAST({identifier(row[0])} AS VARCHAR) AS {identifier(row[0])}"
        if row[1] == "DATE"
        else f"to_json({identifier(row[0])}) AS {identifier(row[0])}"
        if row[1].endswith("[]")
        else identifier(row[0])
        for row in columns
    )
    con.sql("SELECT " + fields + " FROM (" + query + ")").write_parquet(
        str(target), compression="zstd"
    )


def verify_nulls(
    client: ClickHouse,
    con: duckdb.DuckDBPyConnection,
    query: str,
    table: str,
    columns: list[tuple],
) -> None:
    expressions = ",".join(
        f"count(*)-count({identifier(row[0])}) AS {identifier(row[0])}"
        for row in columns
    )
    expected = con.execute("SELECT " + expressions + " FROM (" + query + ")").fetchone()
    actual_nulls = client.rows("SELECT " + expressions + " FROM " + table)[0]
    actual = tuple(int(actual_nulls[row[0]]) for row in columns)
    if expected != actual:
        raise RuntimeError(f"NULL count mismatch for {table}")


def import_table(
    client: ClickHouse,
    con: duckdb.DuckDBPyConnection,
    database: str,
    name: str,
    query: str,
    directory: Path,
    parquet_path: Path | None = None,
    reuse: bool = False,
) -> dict:
    started = perf_counter()
    table = identifier(database) + "." + identifier(name)
    columns = con.execute("DESCRIBE (" + query + ")").fetchall()
    count = con.execute("SELECT count(*) FROM (" + query + ")").fetchone()[0]
    exists = client.rows(f"EXISTS TABLE {table}")[0]["result"]
    current = (
        int(client.rows(f"SELECT count() AS n FROM {table}")[0]["n"])
        if exists and reuse
        else -1
    )
    if current != count:
        required = (
            1_000_000_000 + parquet_path.stat().st_size * 4
            if parquet_path
            else 3_000_000_000
        )
        if shutil.disk_usage(ROOT).free < required:
            raise RuntimeError(f"Import needs {required} free bytes including reserve")
        staging = identifier(database) + "." + identifier(name + "__loading")
        client.request(f"DROP TABLE IF EXISTS {staging}")
        client.request(table_ddl(staging, name, columns))
        path = parquet_path or directory / (database + "-" + name + ".parquet")
        if parquet_path is None:
            export_table(con, query, path)
        client.parquet(staging, path)
        actual = int(client.rows(f"SELECT count() AS n FROM {staging}")[0]["n"])
        if actual != count:
            raise RuntimeError(f"Row count mismatch for {table}: {actual} != {count}")
        verify_nulls(client, con, query, staging, columns)
        if exists:
            client.request(f"EXCHANGE TABLES {table} AND {staging}")
            client.request(f"DROP TABLE {staging}")
        else:
            client.request(f"RENAME TABLE {staging} TO {table}")
        if parquet_path is None:
            path.unlink()
    verify_nulls(client, con, query, table, columns)
    result = {
        "table": database + "." + name,
        "rows": count,
        "columns": len(columns),
        "null_counts_match": True,
        "seconds": round(perf_counter() - started, 3),
    }
    print(json.dumps(result), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    client = ClickHouse()
    directory = args.root / "data/analytics-staging"
    directory.mkdir(exist_ok=True)
    manifest = args.root / "data/analytics-import.json"
    previous = json.loads(manifest.read_text()) if manifest.exists() else {}
    fingerprints = previous.get("fingerprints", {})
    results = {row["table"]: row for row in previous.get("tables", [])}

    def fingerprint(path: Path) -> str:
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    def record(result: dict, digest: str) -> None:
        results[result["table"]] = result
        fingerprints[result["table"]] = digest
        temporary = manifest.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"tables": list(results.values()), "fingerprints": fingerprints},
                indent=2,
            )
        )
        temporary.replace(manifest)

    for name in ["casechamp", "additional"]:
        database = "plexus_" + name
        source = args.root / "data" / (name + ".duckdb")
        digest = fingerprint(source)
        client.request(f"CREATE DATABASE IF NOT EXISTS {identifier(database)}")
        with duckdb.connect(str(source), read_only=True) as con:
            con.execute("SET memory_limit='512MB'")
            con.execute("SET threads=3")
            tables = con.execute("SHOW TABLES").fetchall()
            for (table,) in tables:
                result = import_table(
                    client,
                    con,
                    database,
                    table,
                    "SELECT * FROM " + identifier(table),
                    directory,
                    reuse=fingerprints.get(database + "." + table) == digest,
                )
                record(result, digest)
    client.request("CREATE DATABASE IF NOT EXISTS plexus_graph")
    with duckdb.connect() as con:
        con.execute("SET memory_limit='512MB'")
        con.execute("SET threads=3")
        for path in sorted((args.root / "data/graph_ru").glob("*.parquet")):
            digest = fingerprint(path)
            con.from_parquet(str(path)).create_view("source", replace=True)
            result = import_table(
                client,
                con,
                "plexus_graph",
                path.stem,
                "SELECT * FROM source",
                directory,
                path,
                reuse=fingerprints.get("plexus_graph." + path.stem) == digest,
            )
            record(result, digest)


if __name__ == "__main__":
    main()
