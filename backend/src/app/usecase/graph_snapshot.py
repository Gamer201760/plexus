from typing import Any, Literal, Protocol

GraphQuery = Literal[
    "locations",
    "region_name",
    "ways",
    "way_indices",
    "points",
    "origins",
    "cities",
    "trunk",
    "manual",
    "normalization",
    "expected",
    "delta_points",
    "delta_cities",
    "delta_times",
    "city_times",
    "terminal_nodes",
    "references",
    "road_reference",
    "corridor_places",
    "corridor_edges",
    "corridor_nodes",
    "region_codes",
    "candidates",
    "impact_places",
    "regions",
    "model_version",
    "manual_v2",
]
type GraphParameters = dict[str, str | int | float | list[int] | list[str]]


class GraphSnapshot(Protocol):
    @property
    def revision(self) -> str: ...
    def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]: ...
    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]: ...
