from dataclasses import dataclass
from typing import Literal

from app.domain.transport import NetworkMode, Season
from app.usecase.regions import RegionQueries

ChatCell = str | float | int | None
ComparisonMetric = Literal["hansen", "population", "links_season", "settlements", "companies"]


@dataclass(frozen=True, slots=True)
class ChatColumn:
    key: str
    format: Literal["text", "number", "integer", "percent"] = "text"


@dataclass(frozen=True, slots=True)
class ChatTable:
    id: str
    title: Literal["regions", "links", "settlements", "sensitivity"]
    columns: tuple[ChatColumn, ...]
    rows: tuple[dict[str, ChatCell], ...]
    total: int
    truncated: bool
    source: str


@dataclass(frozen=True, slots=True)
class ChatChart:
    table_id: str
    x: str
    y: str
    type: Literal["bar"] = "bar"


class ChatComparisons:
    def __init__(self, regions: RegionQueries) -> None:
        self._regions = regions

    def regions(
        self,
        season: Season,
        network: NetworkMode,
        metric: ComparisonMetric,
        region_ids: list[str],
        limit: int,
        descending: bool,
    ) -> ChatTable:
        if not 1 <= limit <= 30:
            raise ValueError("Limit must be between 1 and 30")
        rows = self._regions.summaries(season, network)
        known = {row.id for row in rows}
        if set(region_ids) - known:
            raise ValueError("Unknown region identifiers; search first")
        rows = [row for row in rows if not region_ids or row.id in region_ids]
        values = [(row, getattr(row, metric)) for row in rows]
        sign = -1 if descending else 1
        values.sort(key=lambda item: (item[1] is None, sign * (item[1] or 0), item[0].name))
        result: list[dict[str, ChatCell]] = []
        for row, value in values[:limit]:
            item: dict[str, ChatCell] = {"id": row.id, "name": row.name, metric: value}
            if metric == "hansen":
                item["coverage"] = row.index_population_coverage
                item["model_version"] = row.index_model_version
            result.append(item)
        columns = [
            ChatColumn("name"),
            ChatColumn(metric, "number" if metric == "hansen" else "integer"),
        ]
        if metric == "hansen":
            columns.append(ChatColumn("coverage", "percent"))
        return ChatTable(
            "",
            "regions",
            tuple(columns),
            tuple(result),
            len(rows),
            len(rows) > limit,
            f"/api/v1/regions?season={season}&network_mode={network}",
        )
