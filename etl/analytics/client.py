import http.client
import json
import os
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlencode, urlsplit


class ClickHouse:
    def __init__(self) -> None:
        self.url = urlsplit(os.environ.get("CLICKHOUSE_URL", "http://127.0.0.1:18123"))
        self.headers = {
            "X-ClickHouse-User": os.environ.get("CLICKHOUSE_USER", "plexus"),
            "X-ClickHouse-Key": os.environ["CLICKHOUSE_PASSWORD"],
        }

    def request(
        self, sql: str, body: bytes | BinaryIO | None = None, size: int = 0
    ) -> bytes:
        connection = http.client.HTTPConnection(
            self.url.hostname, self.url.port, timeout=600
        )
        if self.url.scheme == "https":
            connection = http.client.HTTPSConnection(
                self.url.hostname, self.url.port, timeout=600
            )
        payload = sql.encode() if body is None else body
        headers = {
            **self.headers,
            "Content-Length": str(len(payload) if isinstance(payload, bytes) else size),
        }
        path = "/?" + urlencode({"precise_float_parsing": 1, **({"query": sql} if body is not None else {})})
        try:
            connection.request("POST", path, body=payload, headers=headers)
            response = connection.getresponse()
            result = response.read()
            if response.status != 200:
                raise RuntimeError(
                    f"ClickHouse HTTP {response.status}: {result.decode()[:2000]}"
                )
            return result
        finally:
            connection.close()

    def rows(self, sql: str) -> list[dict]:
        return [
            json.loads(line)
            for line in self.request(sql + " FORMAT JSONEachRow").splitlines()
        ]

    def parquet(self, table: str, path: Path) -> None:
        with path.open("rb") as stream:
            self.request(
                f"INSERT INTO {table} FORMAT Parquet", stream, path.stat().st_size
            )
