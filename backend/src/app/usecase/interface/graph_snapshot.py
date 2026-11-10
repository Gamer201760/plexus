from typing import Any, Literal, Protocol

from app.usecase.dto.graph_snapshot import GraphParameters, GraphQuery


class GraphSnapshot(Protocol):
    @property
    def revision(self) -> str: ...
    def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]: ...
    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]: ...
