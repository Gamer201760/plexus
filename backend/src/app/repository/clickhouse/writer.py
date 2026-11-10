from typing import Any
from urllib.request import Request, urlopen

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.arrow_rows import arrow_body
from app.repository.clickhouse.client import ClickHouseReader


class ClickHouseWriter:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        self.schemas: dict[str, Any] = {}

    def insert(self, table: str, row: dict[str, object]) -> None:
        allowed = {"road_jobs", "analysis_jobs", "analysis_details"}
        if table not in allowed:
            raise ValueError("Unknown state table")
        if table not in self.schemas:
            self.schemas[table] = self.reader.arrow(
                "SELECT * FROM plexus_state." + table + " LIMIT 0", {}
            ).schema
        body = ("INSERT INTO plexus_state." + table + " FORMAT ArrowStream\n").encode()
        body += arrow_body(self.schemas[table], [row])
        request = Request(
            self.reader.url + "/?precise_float_parsing=1", data=body, headers=self.reader.headers
        )
        try:
            with urlopen(request, timeout=30) as response:
                response.read()
        except OSError as error:
            raise DataUnavailable("Calculation storage is unavailable") from error
