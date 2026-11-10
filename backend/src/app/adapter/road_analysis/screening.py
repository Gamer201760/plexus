from collections.abc import Callable
from typing import Any

import numpy as np
from scipy.sparse.csgraph import dijkstra

from app.adapter.road_analysis.geometry import region_edges
from app.adapter.road_analysis.topology import bridge_exposure
from app.adapter.road_graph.delta_base import DeltaBase
from app.usecase.dto.atlas import BoundaryShape
from app.usecase.dto.road_analysis import AnalysisMode, Candidate


def interleave(first: list[Candidate], second: list[Candidate]) -> list[Candidate]:
    result, seen = [], set()
    for index in range(max(len(first), len(second))):
        for entries in (first, second):
            if index < len(entries) and entries[index].way_id not in seen:
                result.append(entries[index])
                seen.add(entries[index].way_id)
    return result


class CandidateScreening:
    def __init__(self, base: DeltaBase) -> None:
        self.base = base

    def candidates(
        self, boundary: BoundaryShape, mode: AnalysisMode, progress: Callable[[str, int, int], None]
    ) -> list[Candidate]:
        data = self.base.data
        self.base.prepare()
        e, n = data.edges, data.nodes
        progress("geography", 0, 1)
        positions, crossings = region_edges(
            n["lon"], n["lat"], e["src"], e["dst"], boundary.polygons
        )
        selected = np.unique(e["way_idx"][positions])
        cross = set(e["way_idx"][positions[crossings]].tolist())
        total_counts = np.bincount(e["way_idx"])
        inside_counts = np.bincount(
            e["way_idx"][positions[~crossings]], minlength=len(total_counts)
        )
        cross.update(int(w) for w in selected if inside_counts[w] < total_counts[w])
        region = self.base.region(data.region_name(boundary.id))
        rows = data.read("candidates", {"ids": selected.tolist()})
        allowed = {int(r[0]) for r in rows}
        scores = self.path_scores(region, allowed, progress)
        isolation: dict[int, float] = {}
        if mode == "criticality":
            progress("topology", 0, 1)
            bridges = bridge_exposure(
                self.base.graph,
                region.market_nodes,
                region.nodes,
                region.population,
                lambda: progress("topology", 0, 1),
            )
            pairs: dict[tuple[int, int], set[int]] = {}
            for p in positions:
                a, b = int(e["src"][p]), int(e["dst"][p])
                pair = (min(a, b), max(a, b))
                if pair in bridges:
                    pairs.setdefault(pair, set()).add(int(e["way_idx"][p]))
            for pair, ways in pairs.items():
                if len(ways) == 1:
                    w = next(iter(ways))
                    isolation[w] = max(isolation.get(w, 0), bridges[pair])
        candidates = [
            Candidate(
                int(wid),
                str(name),
                float(km or 0),
                scores.get(int(w), 0),
                isolation.get(int(w), 0),
                int(w) in cross,
            )
            for w, wid, name, km in rows
        ]
        main = sorted(candidates, key=lambda c: (-c.score, c.way_id))
        isolated = sorted(
            (c for c in candidates if c.isolation_score > 0),
            key=lambda c: (-c.isolation_score, c.way_id),
        )
        return interleave(main, isolated) if mode == "criticality" else main

    def path_scores(
        self, region: Any, allowed: set[int], progress: Callable[[str, int, int], None]
    ) -> dict[int, float]:
        e = self.base.data.edges
        pairs: dict[tuple[int, int], tuple[float, int]] = {}
        for p in np.flatnonzero(np.isin(e["way_idx"], list(allowed))):
            a, b, w = int(e["src"][p]), int(e["dst"][p]), int(e["way_idx"][p])
            pair = (min(a, b), max(a, b))
            candidate = (float(e["h"][p]), w)
            if pair not in pairs or candidate < pairs[pair]:
                pairs[pair] = candidate
        contribution = (
            np.exp(-np.log(2) / 2 * region.baseline_times) * region.population[:, None]
        ).sum(axis=0) * region.market_weights
        markets = np.argsort(-contribution, kind="stable")[:16]
        scores: dict[int, float] = {}
        for step, j in enumerate(markets):
            progress("screening", step, len(markets))
            distances, predecessors = dijkstra(
                self.base.graph,
                indices=int(region.market_nodes[j]),
                limit=72,
                return_predecessors=True,
            )
            for node, pop, snap in zip(region.nodes, region.population, region.snaps, strict=True):
                if node < 0 or pop <= 0 or not np.isfinite(distances[node]):
                    continue
                weight = float(
                    pop
                    * region.market_weights[j]
                    * np.exp(-np.log(2) / 2 * (distances[node] + snap + region.market_snaps[j]))
                )
                current = int(node)
                while predecessors[current] >= 0:
                    parent = int(predecessors[current])
                    found = pairs.get((min(current, parent), max(current, parent)))
                    if found:
                        hours, way = found
                        scores[way] = scores.get(way, 0) + weight * hours
                    current = parent
            progress("screening", step + 1, len(markets))
        return scores
