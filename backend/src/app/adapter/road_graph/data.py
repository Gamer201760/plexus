from pathlib import Path
from threading import Lock
from typing import Any

import duckdb
import numpy as np
import pyarrow.parquet as pq

from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.road_graph import GraphLocation, RoadSegment, RoadView

VERSION = "data-20261107"


class GraphData:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.lock = Lock()
        self.loaded = False
        self.edges: dict[str, Any] = {}
        self.nodes: dict[str, Any] = {}
        self.road_rank: Any = None

    def load(self) -> None:
        with self.lock:
            if self.loaded:
                return
            if not (self.root / "graph_ru/edges.parquet").exists():
                raise DataUnavailable("Graph files are missing")
            for name, target in [("edges", self.edges), ("nodes", self.nodes)]:
                table = pq.read_table(self.root / f"graph_ru/{name}.parquet")
                target.update({c: table[c].to_numpy() for c in table.column_names})
            with self.connect() as con:
                self.road_rank = (
                    con.execute(
                        "select case replace(highway, '_link', '') "
                        "when 'motorway' then 0 when 'trunk' then 1 when 'primary' then 2 "
                        "when 'secondary' then 3 when 'tertiary' then 4 else 5 end as rank "
                        "from read_parquet(?) order by way_idx",
                        [str(self.root / "graph_ru/ways.parquet")],
                    )
                    .fetchnumpy()["rank"]
                    .astype(np.uint8)
                )
            self.loaded = True

    def connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.root / "casechamp.duckdb"), read_only=True)

    def locations(self, query: str, region_id: str | None) -> list[GraphLocation]:
        self.load()
        region = self.region_name(region_id) if region_id else None
        with self.connect() as con:
            rows = con.execute(
                "select p.point_id, s.settlement, p.region, p.node, p.lon, p.lat, p.snap_km "
                "from read_parquet(?) p join stg_settlements s on p.point_id=s.oktmo "
                "and s.object_level='Населенный пункт' where s.settlement ilike ? "
                "and (? is null or p.region=?) order by p.population desc nulls last limit 20",
                [str(self.root / "graph_ru/points.parquet"), "%" + query + "%", region, region],
            ).fetchall()
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
        with self.connect() as con:
            row = con.execute(
                "select region from stg_settlements where object_level='Регион' and oktmo=?",
                [region_id],
            ).fetchone()
        if row is None:
            raise InvalidQuery("Region is missing from the graph snapshot")
        return str(row[0])

    def ways(self, ids: list[int]) -> dict[int, dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute(
                "select way_idx, way_id, name, ref, highway, speed_kmh "
                "from read_parquet(?) where way_idx in (select unnest(?))",
                [str(self.root / "graph_ru/ways.parquet"), ids],
            ).fetchall()
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
        with self.connect() as con:
            rows = con.execute(
                "select way_id, way_idx from read_parquet(?) where way_id in (select unnest(?))",
                [str(self.root / "graph_ru/ways.parquet"), ids],
            ).fetchall()
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
        segments = []
        seen = set()
        for p in positions:
            a, b, w = int(src[p]), int(dst[p]), int(self.edges["way_idx"][p])
            key = (min(a, b), max(a, b), w)
            if key in seen:
                continue
            seen.add(key)
            way = ways[w]
            segments.append(
                RoadSegment(
                    **way,
                    source_node=a,
                    target_node=b,
                    coordinates=[[float(lon[a]), float(lat[a])], [float(lon[b]), float(lat[b])]],
                )
            )
        return RoadView(
            segments,
            matched,
            level < requested,
            VERSION,
            ("motorway", "trunk", "primary", "secondary", "tertiary", "all")[level],
        )
