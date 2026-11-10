import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.usecase.chat import ChatEvent
from app.usecase.chat_map import ChatMap, MapAction
from app.usecase.regions import RegionQueries


class MapTools:
    def __init__(self, regions: RegionQueries) -> None:
        self._map = ChatMap(regions)

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Control the visible map when the user requests it. Focus highlights and "
            "frames 1-30 atlas region IDs; one ID also selects its summary. Reset shows the country "
            "and clears selection. Zoom_in and zoom_out change scale one step. Non-focus actions "
            "require empty region_ids. Resolve names using search_places/list_regions first.",
        )(self.control_map)

    def control_map(
        self, ctx: RunContext[ChatRun], action: MapAction, region_ids: list[str]
    ) -> str:
        try:
            command = self._map.command(action, region_ids)
        except ValueError as error:
            raise ModelRetry(str(error)) from error
        ctx.deps.pending.append(ChatEvent("map", map=command))
        return json.dumps(asdict(command))
