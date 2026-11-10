from collections import OrderedDict
from typing import Any

import numpy as np
from scipy.sparse import load_npz, save_npz
from scipy.sparse.csgraph import dijkstra

from app.adapter.road_graph.baselines import BaselineCache
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta_model import DeltaRegion, access_times
from app.adapter.road_graph.delta_store import DeltaStore
from app.adapter.road_graph.routing import minimum_csr
from app.domain.errors import InvalidQuery


class DeltaBase:
    def __init__(self, data: GraphData) -> None:
        self.data = data
        self.graph: Any = None
        self.distances: OrderedDict[int, Any] = OrderedDict()
        self.store = DeltaStore(data.root)
        self.regions: OrderedDict[str, DeltaRegion] = OrderedDict()
        self.projected: OrderedDict[int, tuple[Any, Any]] = OrderedDict()
        for name in self.store.names():
            loaded = self.store.read(name)
            if loaded is not None:
                self.regions[name] = loaded

    def prepare(self) -> None:
        if self.graph is not None:
            return
        self.data.load()
        path = BaselineCache(self.data.root).path("delta-road-graph-v1", "road").with_suffix(".npz")
        if path.exists():
            self.graph = load_npz(path)
            return
        e = self.data.edges
        self.graph = minimum_csr(e["src"], e["dst"], e["h"], len(self.data.nodes["lat"]))
        path.parent.mkdir(exist_ok=True)
        save_npz(path, self.graph, compressed=False)

    def distances_from(self, node: int) -> Any:
        self.prepare()
        if not 0 <= node < self.graph.shape[0]:
            raise InvalidQuery("Unknown graph node")
        if node not in self.distances:
            self.distances[node] = dijkstra(self.graph, directed=True, indices=node, limit=72.0)
            while len(self.distances) > 8:
                self.distances.popitem(last=False)
        self.distances.move_to_end(node)
        return self.distances[node]

    def region(self, name: str) -> DeltaRegion:
        if name in self.regions:
            self.regions.move_to_end(name)
            return self.regions[name]
        stored = self.store.read(name)
        if stored is not None:
            self.regions[name] = stored
            return stored
        self.prepare()
        with self.data.connect() as con:
            points = con.execute(
                "select i.point_id, i.population, p.node, p.snap_km/15 "
                "from idx_np i left join read_parquet(?) p using(point_id) "
                "where i.season='road' and i.region=? order by i.point_id",
                [str(self.data.root / "graph_ru/points.parquet"), name],
            ).fetchall()
            cities = con.execute(
                "select city, oktmo, node, snap_h, population from market_cities order by city"
            ).fetchall()
            times = con.execute(
                "select t.point_id, t.city, t.road_h from np_city_times t "
                "join idx_np i on t.point_id=i.point_id and i.season=t.season "
                "where t.season='road' and i.region=?",
                [name],
            ).fetchall()
            cc = con.execute(
                "select t.point_id, t.city, t.road_h from np_city_times t "
                "join market_cities c on t.point_id=c.oktmo "
                "where t.season='road'"
            ).fetchall()
            trunk_rows = con.execute(
                "select city_from,city_to,transport_type,distance_hr "
                "from stg_intercity where transport_type in ('rail','air') "
                "and distance_hr is not null"
            ).fetchall()
            norm_row = con.execute(
                "select avg(hansen_2h/hansen_idx*100) from idx_np "
                "where season='road' and hansen_idx>0"
            ).fetchone()
            expected_row = con.execute(
                "select hansen_idx from idx_region where season='road' and region=?", [name]
            ).fetchone()
        if not points or norm_row is None or expected_row is None:
            raise InvalidQuery("Missing regional baseline")
        ids = [p[0] for p in points]
        pi = {p: i for i, p in enumerate(ids)}
        ci = {c[0]: i for i, c in enumerate(cities)}
        city_ids = {c[1]: i for i, c in enumerate(cities)}
        roads = np.full((len(points), len(cities)), np.inf, dtype=np.float32)
        for point, city, hours in times:
            roads[pi[point], ci[city]] = hours
        city_roads = np.full((len(cities), len(cities)), np.inf)
        represented = set()
        for point, city, hours in cc:
            city_roads[city_ids[point], ci[city]] = hours
            represented.add(city_ids[point])
        market_nodes = np.array([c[2] for c in cities], dtype=np.int32)
        market_snaps = np.array([c[3] for c in cities], dtype=np.float64)
        for i in set(range(len(cities))) - represented:
            city_roads[i] = (
                self.distances_from(int(market_nodes[i]))[market_nodes]
                + market_snaps[i]
                + market_snaps
            )
        trunk = np.full_like(city_roads, np.inf)
        for a, b, mode, hours in trunk_rows:
            trunk[ci[a], ci[b]] = min(
                trunk[ci[a], ci[b]], float(hours) + (1 if mode == "rail" else 2.5)
            )
        result = DeltaRegion(
            ids,
            np.array([p[2] if p[2] is not None else -1 for p in points], dtype=np.int32),
            np.array([p[3] or 0 for p in points], dtype=np.float64),
            np.array([max(0, p[1] or 0) for p in points], dtype=np.float64),
            roads,
            city_roads,
            trunk,
            market_nodes,
            market_snaps,
            np.array([c[4] for c in cities], dtype=np.float64),
            [c[0] for c in cities],
            float(norm_row[0]),
            float(expected_row[0]),
        )
        result.baseline_times = access_times(result.roads, result.city_roads, result.trunk)
        result.baseline_hansen = (
            np.exp(-np.log(2) / 2 * result.baseline_times.astype(np.float64))
            @ result.market_weights
        )
        result.baseline_index = float(
            result.baseline_hansen
            @ result.population
            / result.population.sum()
            / result.normalization
            * 100
        )
        if abs(result.baseline_index - result.expected) > max(
            0.0001, abs(result.expected) * 0.00001
        ):
            raise InvalidQuery("baseline_mismatch")
        self.store.write(name, result)
        self.regions[name] = result
        return result

    def terminal(self, node: int, region: DeltaRegion) -> tuple[Any, Any]:
        market = np.flatnonzero(region.market_nodes == node)
        if len(market):
            j = int(market[0])
            origins = region.roads[:, j].astype(np.float64) - region.snaps - region.market_snaps[j]
            cities = region.city_roads[j] - region.market_snaps[j] - region.market_snaps
            return np.maximum(0.0, origins), np.maximum(0.0, cities)
        if node not in self.projected:
            cached = self.store.read_terminal(node)
            if cached is None:
                with self.data.connect() as con:
                    nodes = con.execute(
                        "select distinct node from read_parquet(?) where node>=0 "
                        "union select node from market_cities order by node",
                        [str(self.data.root / "graph_ru/points.parquet")],
                    ).fetchnumpy()["node"]
                distances = self.distances_from(node)[nodes]
                cached = (nodes, distances)
                self.store.write_terminal(node, *cached)
            self.projected[node] = cached
            while len(self.projected) > 32:
                self.projected.popitem(last=False)
        self.projected.move_to_end(node)
        nodes, values = self.projected[node]
        origins = np.full(len(region.nodes), np.inf)
        valid = region.nodes >= 0
        origins[valid] = values[np.searchsorted(nodes, region.nodes[valid])]
        return origins, values[np.searchsorted(nodes, region.market_nodes)]
