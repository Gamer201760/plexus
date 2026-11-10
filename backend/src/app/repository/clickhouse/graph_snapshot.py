from typing import Any, Literal

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_queries import ARRAYS, QUERIES
from app.usecase.dto.graph_snapshot import GraphParameters, GraphQuery


class ClickHouseGraphSnapshot:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        rows = reader.rows(
            "SELECT value FROM plexus_atlas.atlas_metadata WHERE key='graph_revision'", {}
        )
        if len(rows) != 1:
            raise DataUnavailable("Graph snapshot metadata is missing; import the dataset")
        self._revision = str(rows[0]["value"])

    @property
    def revision(self) -> str:
        return self._revision

    def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]:
        table = self.reader.arrow(ARRAYS[name], {})
        return {column: table[column].to_numpy() for column in table.column_names}

    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]:
        parameters = dict(parameters or {})
        if query in ("locations", "corridor_places"):
            needle = str(parameters.pop("query")).lower()
            parameters["pattern"] = (
                "%" + needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            )
        table = self.reader.arrow(QUERIES[query], parameters)
        return list(zip(*(table[c].to_pylist() for c in table.column_names), strict=True))
