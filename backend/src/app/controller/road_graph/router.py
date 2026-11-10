from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domain.road_economics import MoneyAssumptions
from app.usecase.road_graph import (
    GraphLocation,
    RoadAddition,
    RoadChange,
    RoadGraph,
    RoadJob,
    RoadView,
)


class RoadChangeInput(BaseModel):
    way_id: int = Field(ge=0)
    speed_factor: float = Field(ge=0, le=3)


class RoadScenarioInput(BaseModel):
    region_id: str = Field(min_length=1, max_length=64)
    scenario: Literal["road", "summer", "winter"] = "road"
    changes: list[RoadChangeInput] = Field(min_length=1, max_length=50)


class RoadAdditionInput(BaseModel):
    region_id: str = Field(min_length=1, max_length=64)
    source_node: int = Field(ge=0)
    target_node: int = Field(ge=0)
    travel_hours: float = Field(gt=0, le=72)
    money: MoneyAssumptions | None = None


def build_road_graph_router(graph: RoadGraph) -> APIRouter:
    router = APIRouter(tags=["road-graph"])

    @router.get("/road-graph/locations", response_model=list[GraphLocation])
    def locations(query: str, region_id: str | None = None) -> list[GraphLocation]:
        return graph.locations(query, region_id)

    @router.get("/road-graph", response_model=RoadView)
    def view(west: float, south: float, east: float, north: float, zoom: float = 8) -> RoadView:
        return graph.view(west, south, east, north, zoom)

    @router.post("/road-connections", response_model=RoadJob)
    def add_connection(body: RoadAdditionInput) -> RoadJob:
        return graph.add_connection(
            body.region_id,
            RoadAddition(body.source_node, body.target_node, body.travel_hours),
            body.money,
        )

    @router.get("/road-scenarios", response_model=list[RoadJob])
    def recent() -> list[RoadJob]:
        return graph.recent()

    @router.post("/road-scenarios", response_model=RoadJob)
    def submit(body: RoadScenarioInput) -> RoadJob:
        return graph.submit(
            body.region_id,
            body.scenario,
            [RoadChange(c.way_id, c.speed_factor) for c in body.changes],
        )

    @router.get("/road-scenarios/{job_id}", response_model=RoadJob)
    def job(job_id: str) -> RoadJob:
        return graph.job(job_id)

    @router.delete("/road-scenarios/{job_id}", response_model=RoadJob)
    def cancel(job_id: str) -> RoadJob:
        return graph.cancel(job_id)

    return router
