import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.calculation_tools import CalculationTools
from app.adapter.chat.map_tools import MapTools
from app.usecase.chat_artifacts import (
    ChatCell,
    ChatColumn,
    ChatComparisons,
    ChatTable,
    ComparisonMetric,
)
from app.usecase.links import LinkQueries
from app.usecase.reference import ReferenceQueries
from app.usecase.regions import RegionQueries
from app.usecase.search import Search
from app.usecase.settlements import SettlementQueries, SettlementQuery


class AtlasTools:
    def __init__(
        self,
        regions: RegionQueries,
        links: LinkQueries,
        settlements: SettlementQueries,
        search: Search,
        references: ReferenceQueries,
        calculations: CalculationTools,
    ) -> None:
        self._calculations = calculations
        self._regions = regions
        self._comparisons = ChatComparisons(regions)
        self._links = links
        self._settlements = settlements
        self._search = search
        self._references = references

    def register(self, agent: Agent[ChatRun, str]) -> None:
        MapTools(self._regions).register(agent)
        self._calculations.register(agent)
        agent.tool(sequential=True, description="List all regions with indices, coverage and data versions.")(
            self.list_regions
        )
        agent.tool(sequential=True, description="Read regional transport links with sources and frequencies.")(
            self.region_links
        )
        agent.tool(sequential=True, description="Read largest regional settlements or filter them by name.")(
            self.region_settlements
        )
        agent.tool(sequential=True, description="Find region and settlement identifiers by name.")(
            self.search_places
        )
        agent.tool(sequential=True, description="Read atlas sources and data periods.")(self.sources)
        agent.tool(sequential=True, 
            description="Compute a sorted regional comparison table from atlas data. "
            "Use for rankings and comparisons. Empty region_ids selects all regions."
        )(self.compare_regions)
        agent.tool(sequential=True, 
            description="Display a bar chart from an existing table_id and its columns. "
            "Never supply invented numbers; use compare_regions or region_settlements first."
        )(self.show_chart)

    def list_regions(self, ctx: RunContext[ChatRun]) -> str:
        rows = self._regions.summaries(ctx.deps.context.season, ctx.deps.context.network_mode)
        return json.dumps([asdict(row) for row in rows], ensure_ascii=False)

    def region_links(self, ctx: RunContext[ChatRun], region_id: str, offset: int = 0) -> str:
        rows = self._links.region_links(region_id, ctx.deps.context.season)
        start = max(0, offset)
        selected = rows[start : start + 30]
        values: tuple[dict[str, ChatCell], ...] = tuple(
            {
                "id": row.id,
                "origin": row.origin.name,
                "destination": row.destination.name,
                "mode": row.mode.value,
                "frequency": row.freq_per_week,
                "source_url": row.source_url,
                "source_date": row.source_date,
                "confidence": row.confidence,
                "frequency_note": row.freq_note,
                "frequency_assumed": int(row.freq_assumed),
                "season": row.season,
            }
            for row in selected
        )
        table = ChatTable(
            "",
            "links",
            (
                ChatColumn("origin"),
                ChatColumn("destination"),
                ChatColumn("mode"),
                ChatColumn("frequency", "number"),
            ),
            values,
            len(rows),
            start > 0 or len(rows) > 30,
            f"/api/v1/regions/{region_id}/links?season={ctx.deps.context.season}",
        )
        return ctx.deps.table(table)

    def region_settlements(self, ctx: RunContext[ChatRun], region_id: str, query: str = "") -> str:
        page = self._settlements.page(SettlementQuery(region_id, text=query, limit=30))
        values: tuple[dict[str, ChatCell], ...] = tuple(
            {
                "id": row.id,
                "name": row.name,
                "population": row.population,
                "companies": row.companies,
            }
            for row in page.items
        )
        return ctx.deps.table(
            ChatTable(
                "",
                "settlements",
                (
                    ChatColumn("name"),
                    ChatColumn("population", "integer"),
                    ChatColumn("companies", "integer"),
                ),
                values,
                page.total,
                page.total > len(values),
                f"/api/v1/regions/{region_id}/settlements",
            )
        )

    def search_places(self, ctx: RunContext[ChatRun], query: str) -> str:
        return json.dumps(asdict(self._search.run(query)), ensure_ascii=False)

    def sources(self, ctx: RunContext[ChatRun]) -> str:
        return json.dumps([asdict(row) for row in self._references.sources()], ensure_ascii=False)

    def compare_regions(
        self,
        ctx: RunContext[ChatRun],
        metric: ComparisonMetric,
        region_ids: list[str],
        limit: int = 8,
        descending: bool = False,
    ) -> str:
        try:
            table = self._comparisons.regions(
                ctx.deps.context.season,
                ctx.deps.context.network_mode,
                metric,
                region_ids,
                limit,
                descending,
            )
        except ValueError as error:
            raise ModelRetry(str(error)) from error
        return ctx.deps.table(table)

    def show_chart(self, ctx: RunContext[ChatRun], table_id: str, x: str, y: str) -> str:
        return ctx.deps.chart(table_id, x, y)
