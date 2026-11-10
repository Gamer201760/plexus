from collections.abc import Callable
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra, floyd_warshall

from app.adapter.road_graph.data import GraphData
from app.domain.road_analysis import SettlementAccess
from app.usecase.road_graph import RoadAddition, RoadChange


def minimum_csr(src: Any, dst: Any, weights: Any, count: int) -> Any:
    a, b = np.concatenate([src, dst]), np.concatenate([dst, src])
    w = np.concatenate([weights, weights])
    order = np.lexsort((w, b, a))
    a, b, w = a[order], b[order], w[order]
    keep = np.ones(len(a), dtype=bool)
    keep[1:] = (a[1:] != a[:-1]) | (b[1:] != b[:-1])
    return csr_matrix((w[keep].astype(np.float64), (a[keep], b[keep])), shape=(count, count))


class GraphRouting:
    def __init__(self, data: GraphData) -> None:
        self.data = data

    def calculate(
        self,
        region: str,
        scenario: str,
        changes: list[RoadChange],
        progress: Callable[[int], None],
        addition: RoadAddition | None = None,
    ) -> tuple[float, int, int, int, float]:
        result, _ = self.calculate_details(region, scenario, changes, progress, addition)
        return result

    def calculate_details(
        self,
        region: str,
        scenario: str,
        changes: list[RoadChange],
        progress: Callable[[int], None],
        addition: RoadAddition | None = None,
    ) -> tuple[tuple[float, int, int, int, float], tuple[SettlementAccess, ...]]:
        self.data.load()
        with self.data.connect() as con:
            points = con.execute(
                "select point_id, node, snap_km from read_parquet(?)",
                [str(self.data.root / "graph_ru/points.parquet")],
            ).fetchall()
            origins = con.execute(
                "select point_id, population from idx_np where season=? and region=?",
                [scenario, region],
            ).fetchall()
            cities = con.execute(
                "select city, node, snap_h, population from market_cities order by city"
            ).fetchall()
            trunk = con.execute(
                "select city_from, city_to, transport_type, distance_hr "
                "from stg_intercity where transport_type in ('rail','air') "
                "and distance_hr is not null"
            ).fetchall()
            manual = (
                []
                if scenario == "road"
                else con.execute(
                    "select from_id, to_id, h from manual_links_ru where season=?", [scenario]
                ).fetchall()
            )
            norm_row = con.execute(
                "select avg(hansen_2h/hansen_idx*100) from idx_np "
                "where season='road' and hansen_idx>0"
            ).fetchone()
            if norm_row is None or norm_row[0] is None:
                raise ValueError("Missing normalization")
            norm = float(norm_row[0])
        lookup = {p[0]: [int(p[1]), float(p[2]) / 15] for p in points}
        count = len(self.data.nodes["lat"])
        for a, b, _ in manual:
            for point in (a, b):
                if point in lookup and lookup[point][0] < 0:
                    lookup[point] = [count, 0.0]
                    count += 1
        ms, md, mw = [], [], []
        for a, b, h in manual:
            if a in lookup and b in lookup:
                left, right = lookup[a], lookup[b]
                ms.append(left[0])
                md.append(right[0])
                mw.append(h + left[1] + right[1])
        if addition:
            ms.append(addition.source_node)
            md.append(addition.target_node)
            mw.append(addition.travel_hours)
        edges = self.data.edges
        weights = edges["h"].copy()
        changed = 0
        ways = self.data.indices_for([c.way_id for c in changes]) if changes else {}
        for change in changes:
            mask = edges["way_idx"] == ways[change.way_id]
            changed += int(mask.sum())
            weights[mask] = weights[mask] / change.speed_factor if change.speed_factor else np.inf
        finite = np.isfinite(weights)
        graph = minimum_csr(
            np.concatenate([edges["src"][finite], ms]).astype(np.int32),
            np.concatenate([edges["dst"][finite], md]).astype(np.int32),
            np.concatenate([weights[finite], np.array(mw, dtype=np.float32)]),
            count,
        )
        progress(0)
        on = [
            (lookup[p][0], lookup[p][1], max(0, pop or 0))
            for p, pop in origins
            if p in lookup and lookup[p][0] >= 0
        ]
        nodes = np.array([p[0] for p in on], dtype=np.int32)
        snaps = np.array([p[1] for p in on])
        population = np.array([p[2] for p in on])
        total_pop = int(sum(max(0, p[1] or 0) for p in origins))
        city_nodes = np.array([c[1] for c in cities], dtype=np.int32)
        city_snaps = np.array([c[2] for c in cities], dtype=np.float64)
        road = np.empty((len(on), len(cities)), dtype=np.float32)
        city_road = np.empty((len(cities), len(cities)))
        for j, node in enumerate(city_nodes):
            distances = dijkstra(graph, directed=True, indices=int(node), limit=72.0)
            road[:, j] = distances[nodes].astype(np.float32) + snaps + city_snaps[j]
            city_road[j] = distances[city_nodes] + city_snaps[j] + city_snaps
            progress(j + 1)
        ci = {c[0]: j for j, c in enumerate(cities)}
        for source, target, mode, hours in trunk:
            a, b = ci[source], ci[target]
            city_road[a, b] = min(city_road[a, b], hours + (1 if mode == "rail" else 2.5))
        np.fill_diagonal(city_road, 0.0)
        transfers = floyd_warshall(city_road)
        hansen = np.zeros(len(on))
        reachable = np.zeros(len(on), dtype=bool)
        for j, city in enumerate(cities):
            best = np.min(road + transfers[:, j].astype(np.float32), axis=1)
            reachable |= np.isfinite(best)
            hansen += city[3] * np.exp(-np.log(2) / 2 * best.astype(np.float64))
        if total_pop <= 0:
            raise ValueError("Population must be positive")
        index = float(np.dot(hansen, population) / total_pop / norm * 100)
        connected_ids = [p for p, _ in origins if p in lookup and lookup[p][0] >= 0]
        values = {
            point_id: (float(hansen[i] / norm * 100), bool(reachable[i]))
            for i, point_id in enumerate(connected_ids)
        }
        details = tuple(
            SettlementAccess(str(p), max(0, pop or 0), *values.get(p, (0.0, False)))
            for p, pop in origins
        )
        return (index, total_pop, len(origins), changed, norm), details
