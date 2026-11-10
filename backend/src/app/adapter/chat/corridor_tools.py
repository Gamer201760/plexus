import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError
from app.usecase.dto.chat import ChatEvent
from app.usecase.dto.road_corridor import CorridorCalculation
from app.usecase.road_corridor import RoadCorridors


class CorridorTools:
    def __init__(self, corridors: RoadCorridors) -> None:
        self.corridors = corridors

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Resolve a named highway between two settlements from the COMPLETE graph, independent of map viewport. Returns a server corridor ID, whole-way count, attachments and endpoint regions. Includes parallel named-road carriageways through block-cut connectivity, excludes dangling branches. Use this for 'close highway X between A and B'. Do not ask whether both directions or which endpoint region: default both directions and evaluate both endpoint regions. State whole-OSM-way and attachment scope briefly. Resolution errors identify genuine missing/ambiguous data; never substitute a partial viewport.",
        )(self.resolve_road_corridor)
        agent.tool(
            sequential=True,
            description="Close a previously resolved named-road corridor in both directions, leaving other ways unchanged, and queue exact Hansen calculations for BOTH endpoint regions. User's explicit request to close the named highway authorizes this model scenario; do not ask for repeated confirmation. Returns job IDs; results take minutes and are read with road_calculation_status. No source data is modified.",
        )(self.close_road_corridor)

    def resolve_road_corridor(
        self, ctx: RunContext[ChatRun], road_name: str, origin: str, destination: str
    ) -> str:
        try:
            corridor = self.corridors.resolve(road_name, origin, destination)
            result = asdict(corridor)
            result.pop("lines")
            result.pop("way_ids")
            result["way_count"] = len(corridor.way_ids)
            result["length_method"] = "sum_of_whole_way_lengths_including_parallel_carriageways"
            return json.dumps(result, ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def close_road_corridor(self, ctx: RunContext[ChatRun], corridor_id: str) -> str:
        try:
            jobs = self.corridors.close(corridor_id)
            ctx.deps.pending.append(ChatEvent(
                "calculation",
                calculation=CorridorCalculation(self.corridors.get(corridor_id), [j.id for j in jobs]),
            ))
            return json.dumps(
                [
                    {
                        "id": j.id,
                        "region": j.region,
                        "status": j.status,
                        "changed_ways": len(j.changes),
                    }
                    for j in jobs
                ],
                ensure_ascii=False,
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error
