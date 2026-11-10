import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError
from app.domain.road_economics import MoneyAssumptions
from app.usecase.road_graph import RoadAddition, RoadChange, RoadGraph


class RoadTools:
    def __init__(self, graph: RoadGraph) -> None:
        self.graph = graph

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Find real settlements and graph attachment node IDs. "
            "Use before adding a connection; never invent node IDs. A null node is unanchored.",
        )(self.find_graph_locations)
        agent.tool(
            sequential=True,
            description="Add ONE hypothetical bidirectional connection between "
            "existing graph nodes, with user-specified travel_hours between these nodes. "
            "Does not modify source data. Exact two-terminal road update on the snapshot BASE "
            "network; cold graph preparation may take a minute, repeated endpoints are cached. "
            "Not for closures, seasonal links, or multiple interacting additions. Find node "
            "IDs with find_graph_locations/read_road_graph. Return job and poll later. "
            "Optional money assumptions value saved time on ONE origin settlement to market "
            "OD pair: trips_per_year, rub_per_hour, capital_cost_rub, annual_operating_cost_rub. "
            "Ask for missing assumptions; never infer revenue/GDP from Hansen. All ruble "
            "outputs are conditional time savings, not actual revenue or fiscal returns.",
        )(self.add_graph_connection)
        agent.tool(
            sequential=True,
            description="Read real road graph segments in a bounding box. "
            "Returns OSM way IDs for scenario changes. Coordinates are contracted endpoints. "
            "Use small bounds near the requested settlement; sampled view is not all roads.",
        )(self.read_road_graph)
        agent.tool(
            sequential=True,
            description="Start a real asynchronous Hansen recalculation for "
            "an explicit user scenario. Changes use OSM way_id and speed_factor: 1 unchanged, "
            "1.2 speed +20%, 0 closure. Entire OSM way changes, not only visible segment. "
            "Do not invent road IDs. Snapshot road baseline also includes intercity rail/air; "
            "summer/winter add local seasonal links. Baseline is checked against the same DB. "
            "Return job ID and poll later; never invent final results.",
        )(self.recalculate_road_index)
        agent.tool(
            sequential=True,
            description="Read recalculation progress and actual before/after "
            "indices; pending is not a result. Do not busy-poll during one chat turn.",
        )(self.road_calculation_status)

    def read_road_graph(
        self,
        ctx: RunContext[ChatRun],
        west: float,
        south: float,
        east: float,
        north: float,
        zoom: float = 10,
    ) -> str:
        try:
            view = self.graph.view(west, south, east, north, zoom)
            result = asdict(view)
            result["segments"] = result["segments"][:60]
            result["tool_limited"] = len(view.segments) > 60
            return json.dumps(result, ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def recalculate_road_index(
        self, ctx: RunContext[ChatRun], region_id: str, scenario: str, changes: list[RoadChange]
    ) -> str:
        try:
            return json.dumps(
                asdict(self.graph.submit(region_id, scenario, changes)), ensure_ascii=False
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def road_calculation_status(self, ctx: RunContext[ChatRun], job_id: str) -> str:
        try:
            return json.dumps(asdict(self.graph.job(job_id)), ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def find_graph_locations(
        self, ctx: RunContext[ChatRun], query: str, region_id: str | None = None
    ) -> str:
        try:
            return json.dumps(
                [asdict(p) for p in self.graph.locations(query, region_id)], ensure_ascii=False
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def add_graph_connection(
        self,
        ctx: RunContext[ChatRun],
        region_id: str,
        source_node: int,
        target_node: int,
        travel_hours: float,
        money: MoneyAssumptions | None = None,
    ) -> str:
        try:
            result = self.graph.add_connection(
                region_id, RoadAddition(source_node, target_node, travel_hours), money
            )
            return json.dumps(asdict(result), ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error
