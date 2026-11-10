import re
from threading import Lock
from uuid import uuid4

import numpy as np
from scipy.sparse.csgraph import connected_components

from app.adapter.road_corridor.blocks import corridor_pairs
from app.adapter.road_graph.jobs import RoadJobs
from app.adapter.road_graph.routing import minimum_csr
from app.domain.errors import InvalidQuery
from app.usecase.road_corridor import CorridorRegion, RoadCorridor
from app.usecase.road_graph import RoadChange, RoadJob


def normalized(value: str) -> str:
    return re.sub(r"[^a-zа-яё0-9]", "", value.casefold())


class CorridorResolver:
    def __init__(self, roads: RoadJobs) -> None:
        self.roads = roads
        self.resolved: dict[str, RoadCorridor] = {}
        self.lock = Lock()

    def resolve(self, road_name: str, origin: str, destination: str) -> RoadCorridor:
        data = self.roads.data
        with data.connect() as con:
            ways = con.execute(
                "select way_idx,way_id,name,ref,km from read_parquet(?) where ref is not null",
                [str(data.root / "graph_ru/ways.parquet")],
            ).fetchall()
            matches = {
                str(r[3])
                for r in ways
                if normalized(str(r[2] or "")) == normalized(road_name)
                or normalized(str(r[3])) == normalized(road_name)
            }
            if len(matches) != 1:
                raise InvalidQuery(
                    "Road reference is ambiguous or missing: " + ", ".join(sorted(matches)[:8])
                )
            reference = next(iter(matches))
            selected = {int(r[0]): r for r in ways if str(r[3]) == reference}
            endpoints = []
            for query in (origin, destination):
                locations = con.execute(
                    "select p.point_id,s.settlement,p.region,p.lon,p.lat from read_parquet(?) p join stg_settlements s on p.point_id=s.oktmo and s.object_level='Населенный пункт' where s.settlement ilike ?",
                    [str(data.root / "graph_ru/points.parquet"), "%" + query + "%"],
                ).fetchall()
                if len(locations) != 1:
                    raise InvalidQuery(
                        "Settlement is ambiguous: "
                        + query
                        + ": "
                        + ", ".join(str(p[1]) + ", " + str(p[2]) for p in locations[:8])
                    )
                endpoints.append(locations[0])
            edge_rows = con.execute(
                "select src,dst,way_idx from read_parquet(?) where way_idx in (select unnest(?))",
                [str(data.root / "graph_ru/edges.parquet"), list(selected)],
            ).fetchall()
            node_ids = sorted({int(n) for a, b, _ in edge_rows for n in (a, b)})
            node_rows = con.execute(
                "select node,lon,lat from read_parquet(?) where node in (select unnest(?)) order by node",
                [str(data.root / "graph_ru/nodes.parquet"), node_ids],
            ).fetchall()
            region_rows = con.execute(
                "select oktmo,region from stg_settlements where object_level='Регион' and region in (select unnest(?))",
                [[str(p[2]) for p in endpoints]],
            ).fetchall()
        coordinates = {int(n): (float(x), float(y)) for n, x, y in node_rows}
        xy = np.array([(x, y) for _, x, y in node_rows])
        distances = []
        for point in endpoints:
            x, y = float(point[3]), float(point[4])
            distances.append(
                np.hypot((xy[:, 0] - x) * np.cos(np.radians(y)), xy[:, 1] - y) * 111.195
            )
        ids = np.array([n for n, _, _ in node_rows])
        starts = np.searchsorted(ids, [a for a, _, _ in edge_rows])
        ends = np.searchsorted(ids, [b for _, b, _ in edge_rows])
        graph = minimum_csr(starts, ends, np.ones(len(starts)), len(ids))
        component_count, labels = connected_components(graph)
        corridor: set[tuple[int, int]] = set()
        attachments = []
        pairs = [(int(a), int(b)) for a, b, _ in edge_rows]
        for component in range(component_count):
            positions = np.flatnonzero(labels == component)
            a = int(positions[np.argmin(distances[0][positions])])
            b = int(positions[np.argmin(distances[1][positions])])
            if a == b or max(distances[0][a], distances[1][b]) > 20:
                continue
            corridor.update(corridor_pairs(pairs, int(ids[a]), int(ids[b])))
            attachments.append((float(distances[0][a]), float(distances[1][b])))
        offsets = [max((pair[i] for pair in attachments), default=0.0) for i in range(2)]
        if not corridor:
            raise InvalidQuery(
                "Named-road graph has no connected corridor between the requested cities; do not substitute a viewport fragment"
            )
        way_indices = {
            int(w)
            for a, b, w in edge_rows
            if (min(int(a), int(b)), max(int(a), int(b))) in corridor
        }
        full_pairs = {
            (min(int(a), int(b)), max(int(a), int(b)))
            for a, b, w in edge_rows
            if int(w) in way_indices
        }
        result = RoadCorridor(
            uuid4().hex,
            reference,
            str(endpoints[0][1]),
            str(endpoints[1][1]),
            sorted(int(selected[w][1]) for w in way_indices),
            sum(float(selected[w][4] or 0) for w in way_indices),
            offsets[0],
            offsets[1],
            [CorridorRegion(str(i), str(name)) for i, name in sorted(region_rows)],
            [[list(coordinates[a]), list(coordinates[b])] for a, b in sorted(full_pairs)],
        )
        with self.lock:
            self.resolved[result.id] = result
        return result

    def get(self, corridor_id: str) -> RoadCorridor:
        with self.lock:
            if corridor_id not in self.resolved:
                raise InvalidQuery("Resolve the named road corridor before closing it")
            return self.resolved[corridor_id]

    def close(self, corridor_id: str) -> list[RoadJob]:
        corridor = self.get(corridor_id)
        changes = [RoadChange(way, 0) for way in corridor.way_ids]
        return [
            self.roads.submit(region.id, region.name, "road", changes, queue=True)
            for region in corridor.regions
        ]
