import argparse
import hashlib
import http.client
import json
import re
from pathlib import Path
from urllib.parse import urlencode

from client import ClickHouse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--include-staging", action="store_true")
    parser.add_argument("--table")
    parser.add_argument("--database-prefix", default="plexus_")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", args.database_prefix):
        raise SystemExit("Invalid database prefix")
    manifest = json.loads((args.directory / "manifest.json").read_text())
    tables = [
        table
        for table in manifest["tables"]
        if (args.include_staging or not table["staging"])
        and (args.table is None or table["table"] == args.table)
    ]
    if not tables:
        raise SystemExit("No matching tables")
    client = ClickHouse()
    for table in tables:
        name = table["table"].replace("plexus_", args.database_prefix, 1)
        if not re.fullmatch(r"[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+", name):
            raise SystemExit("Invalid table name")
        if client.rows(f"EXISTS TABLE {name}")[0]["result"]:
            raise SystemExit(
                f"Target table already exists: {name}; restore into an empty database"
            )
        path = args.directory / table["asset"]
        if path.parent != args.directory or path.stat().st_size != table["bytes"]:
            raise SystemExit(f"Invalid asset: {path.name}")
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != table["sha256"]:
                raise SystemExit(f"SHA-256 mismatch: {path.name}")
    for table in tables:
        name = table["table"].replace("plexus_", args.database_prefix, 1)
        database = name.split(".")[0]
        client.request(f"CREATE DATABASE IF NOT EXISTS {database}")
        client.request(table["schema"].replace(table["table"], name, 1))
        path = args.directory / table["asset"]
        connection_type = (
            http.client.HTTPSConnection
            if client.url.scheme == "https"
            else http.client.HTTPConnection
        )
        connection = connection_type(client.url.hostname, client.url.port, timeout=1800)
        try:
            with path.open("rb") as stream:
                connection.request(
                    "POST",
                    "/?" + urlencode({"query": f"INSERT INTO {name} FORMAT Native"}),
                    body=stream,
                    headers={
                        **client.headers,
                        "Content-Encoding": "gzip",
                        "Content-Length": str(path.stat().st_size),
                    },
                )
                response = connection.getresponse()
                message = response.read()
                if response.status != 200:
                    raise RuntimeError(
                        f"Restore failed for {name}: {message.decode()[:1000]}"
                    )
        finally:
            connection.close()
        actual = int(client.rows(f"SELECT count() AS n FROM {name}")[0]["n"])
        if actual != table["rows"]:
            raise SystemExit(
                f"Row count mismatch for {name}: {actual} != {table['rows']}"
            )
        print(f"Restored {name}: {actual} rows", flush=True)


if __name__ == "__main__":
    main()
