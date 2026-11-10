from functools import cached_property

from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.road_graph import RoadSegment, RoadView

BOUNDS = """min_lon <= {east:Float64} AND max_lon >= {west:Float64}
    AND min_lat <= {north:Float64} AND max_lat >= {south:Float64}
    AND rank <= {level:UInt8}"""
COUNTS = (
    "SELECT rank, sum(edge_count) AS n FROM plexus_graph.road_lines WHERE "
    + BOUNDS
    + " GROUP BY rank"
)
LINES = (
    """SELECT way_id, name, highway, speed_kmh, source_node, target_node, coordinates
    FROM plexus_graph.road_lines WHERE """
    + BOUNDS
)
DETAILS = ("motorway", "trunk", "primary", "secondary", "tertiary", "all")


class ClickHouseRoadView:
    def __init__(self, url: str, user: str, password: str) -> None:
        self.reader = ClickHouseReader(url, user, password)

    @cached_property
    def version(self) -> str:
        rows = self.reader.rows(
            "SELECT value FROM plexus_atlas.atlas_metadata WHERE key='graph_version'", {}
        )
        return str(rows[0]["value"]) if rows else "data-20261107"

    def view(self, bounds: tuple[float, float, float, float], zoom: float) -> RoadView:
        west, south, east, north = bounds
        requested = 1 if zoom < 5 else 3 if zoom < 7 else 4 if zoom < 9 else 5
        parameters: dict[str, float | int] = {
            "west": west,
            "south": south,
            "east": east,
            "north": north,
            "level": requested,
        }
        counts = self.reader.rows(COUNTS, parameters)
        level = requested
        while level > 0 and sum(int(row["n"]) for row in counts if row["rank"] <= level) > 250000:
            level -= 1
        parameters["level"] = level
        segments = [
            RoadSegment(
                way_id=int(row["way_id"]),
                name=str(row["name"]),
                highway=str(row["highway"]),
                speed_kmh=float(row["speed_kmh"]),
                source_node=int(row["source_node"]),
                target_node=int(row["target_node"]),
                coordinates=row["coordinates"],
            )
            for row in self.reader.rows(LINES, parameters)
        ]
        return RoadView(
            segments,
            sum(int(row["n"]) for row in counts if row["rank"] <= level),
            level < requested,
            self.version,
            DETAILS[level],
        )
