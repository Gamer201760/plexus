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
        self.store = DeltaStore(data.root, data.revision)
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
        path = (
            BaselineCache(self.data.root, self.data.revision)
            .path("delta-road-graph-v1", "road")
            .with_suffix(".npz")
        )
        if path.exists():
            self.graph = load_npz(path)
            return
        e = self.data.edges
        keep = self.data.allowed_edges("road")
        count = len(self.data.nodes["lat"])
        if self.data.modern_model:
            count = max(count, max(int(city[1]) + 1 for city in self.data.read("cities")))
        self.graph = minimum_csr(e["src"][keep], e["dst"][keep], e["h"][keep], count)
        path.parent.mkdir(parents=True, exist_ok=True)
        save_npz(path, self.graph, compressed=False)

    def distances_from(self, node: int) -> Any:
        self.prepare()
        if not 0 <= node < self.graph.shape[0]:
            raise InvalidQuery("Unknown graph node")
        if node not in self.distances:
            self.distances[node] = dijkstra(
                self.graph, directed=True, indices=node,
                limit=np.inf if self.data.modern_model else 72.0,
            )
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
        points = self.data.read("delta_points", {"region": name})
        cities = self.data.read("delta_cities")
        times = self.data.read("delta_times", {"region": name})
        cc = self.data.read("city_times")
        trunk_rows = [] if self.data.modern_model else self.data.read("trunk")
        norms = self.data.read("normalization")
        expectations = self.data.read("expected", {"region": name, "season": "road"})
        norm_row = norms[0] if norms else None
        expected_row = expectations[0] if expectations else None
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
                nodes = np.array(
                    [row[0] for row in self.data.read("terminal_nodes")], dtype=np.int32
                )
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
