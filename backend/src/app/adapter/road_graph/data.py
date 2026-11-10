import hashlib
from functools import cached_property
from threading import Lock
from typing import Any

import numpy as np

from app.adapter.road_graph.view_geometry import road_segments
from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.dto.graph_snapshot import GraphParameters, GraphQuery
from app.usecase.dto.road_graph import GRAPH_DATA_VERSION, GraphLocation, RoadView
from app.usecase.interface.graph_snapshot import GraphSnapshot


class GraphData:
    def __init__(self, snapshot: GraphSnapshot | None = None) -> None:
        self.snapshot = snapshot
        self.lock = Lock()
        self.loaded = False
        self.edges: dict[str, Any] = {}
        self.nodes: dict[str, Any] = {}
        self.road_rank: Any = None
        self.road_seasons: Any = None

    @cached_property
    def modern_model(self) -> bool:
        rows = self.read("model_version")
        return bool(rows and rows[0][0] == "hansen-frequency-v2")

    @property
    def revision(self) -> str:
        return self.snapshot.revision if self.snapshot else "[]"

    @cached_property
    def version(self) -> str:
        if not self.modern_model:
            return GRAPH_DATA_VERSION
        return "road-" + hashlib.sha256(self.revision.encode()).hexdigest()[:16]

    def load(self) -> None:
        with self.lock:
            if self.loaded:
                return
            if self.snapshot is None:
                raise DataUnavailable("Graph storage is not configured")
            self.edges.update(self.snapshot.arrays("edges"))
            self.nodes.update(self.snapshot.arrays("nodes"))
            self.road_rank = self.snapshot.arrays("ranks")["rank"].astype(np.uint8)
            if self.modern_model:
                self.road_seasons = self.snapshot.arrays("seasons")["season"]
            self.loaded = True

    def allowed_edges(self, scenario: str) -> Any:
        if not self.modern_model:
            return np.ones(len(self.edges["src"]), dtype=bool)
        seasons = self.road_seasons[self.edges["way_idx"]]
        allowed = seasons == 0
        season = scenario.removeprefix("road_")
        if season in {"summer", "winter"}:
            allowed |= seasons == (1 if season == "summer" else 2)
        return allowed

    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]:
        if self.snapshot is None:
            raise DataUnavailable("Graph storage is not configured")
        return self.snapshot.read(query, parameters)

    def locations(self, query: str, region_id: str | None) -> list[GraphLocation]:
        region = self.region_name(region_id) if region_id else ""
        rows = self.read("locations", {"query": query, "region": region})
        return [
            GraphLocation(
                str(p[0]),
                str(p[1]),
                str(p[2]),
                int(p[3]) if p[3] >= 0 else None,
                float(p[4]),
                float(p[5]),
                float(p[6]),
            )
            for p in rows
        ]

    def region_name(self, region_id: str) -> str:
        rows = self.read("region_name", {"region_id": region_id})
        if not rows:
            raise InvalidQuery("Region is missing from the graph snapshot")
        return str(rows[0][0])

    def ways(self, ids: list[int]) -> dict[int, dict[str, Any]]:
        rows = self.read("ways", {"ids": ids})
        return {
            int(r[0]): {
                "way_id": int(r[1]),
                "name": r[2] or r[3] or str(r[1]),
                "highway": r[4],
                "speed_kmh": r[5],
            }
            for r in rows
        }

    def indices_for(self, ids: list[int]) -> dict[int, int]:
        rows = self.read("way_indices", {"ids": ids})
        if len(rows) != len(ids):
            raise InvalidQuery("Unknown OSM way identifier")
        return {int(r[0]): int(r[1]) for r in rows}

    def view(self, bounds: tuple[float, float, float, float], zoom: float) -> RoadView:
        self.load()
        west, south, east, north = bounds
        lat, lon = self.nodes["lat"], self.nodes["lon"]
        src, dst = self.edges["src"], self.edges["dst"]
        intersects = (
            (np.minimum(lon[src], lon[dst]) <= east)
            & (np.maximum(lon[src], lon[dst]) >= west)
            & (np.minimum(lat[src], lat[dst]) <= north)
            & (np.maximum(lat[src], lat[dst]) >= south)
        )
        positions = np.flatnonzero(intersects)
        requested = 1 if zoom < 5 else 3 if zoom < 7 else 4 if zoom < 9 else 5
        level = requested
        ranks = self.road_rank[self.edges["way_idx"][positions]]
        while level > 0 and np.count_nonzero(ranks <= level) > 250000:
            level -= 1
        positions = positions[ranks <= level]
        matched = len(positions)
        ways = self.ways(np.unique(self.edges["way_idx"][positions]).tolist())
        segments = road_segments(positions, self.edges, self.nodes, ways)
        return RoadView(
            segments,
            matched,
            level < requested,
            self.version,
            ("motorway", "trunk", "primary", "secondary", "tertiary", "all")[level],
        )
