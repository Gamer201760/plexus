import gzip
import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, BinaryIO, cast
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pyarrow as pa
from pyarrow import ipc

from app.domain.errors import DataUnavailable

type QueryValue = str | float | int | list[int] | list[str]


def parameter(value: QueryValue) -> str | float | int:
    if not isinstance(value, list):
        return value
    entries = []
    for item in value:
        if isinstance(item, str):
            escaped = item.replace("\\", "\\\\").replace("'", "\\'")
            escaped = (
                escaped.replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
                .replace("\0", "\\0")
            )
            entries.append("'" + escaped + "'")
        else:
            entries.append(str(item))
    return "[" + ",".join(entries) + "]"


class ClickHouseReader:
    def __init__(self, url: str, user: str, password: str) -> None:
        self.url = url.rstrip("/")
        self.headers = {
            "X-ClickHouse-User": user,
            "X-ClickHouse-Key": password,
            "Accept-Encoding": "gzip",
        }

    @contextmanager
    def response(
        self, sql: str, parameters: Mapping[str, QueryValue], format_name: str
    ) -> Iterator[BinaryIO]:
        query = urlencode(
            {
                "readonly": 1,
                "max_execution_time": 120,
                "enable_http_compression": 1,
                "output_format_json_quote_64bit_integers": 0,
                **{"param_" + k: parameter(v) for k, v in parameters.items()},
            }
        )
        request = Request(
            self.url + "/?" + query,
            data=(sql + " FORMAT " + format_name).encode(),
            headers=self.headers,
        )
        try:
            with urlopen(request, timeout=150) as response:
                if response.headers.get("Content-Encoding") == "gzip":
                    with gzip.GzipFile(fileobj=response) as stream:
                        yield cast(BinaryIO, stream)
                else:
                    yield cast(BinaryIO, response)
        except (OSError, ValueError, KeyError) as error:
            raise DataUnavailable("Analytical storage is unavailable") from error

    def rows(self, sql: str, parameters: Mapping[str, QueryValue]) -> list[dict[str, Any]]:
        with self.response(sql, parameters, "JSON") as response:
            result: list[dict[str, Any]] = json.load(response)["data"]
            return result

    def arrow(self, sql: str, parameters: Mapping[str, QueryValue]) -> Any:
        with self.response(sql, parameters, "ArrowStream") as response:
            return ipc.open_stream(pa.input_stream(response)).read_all()
