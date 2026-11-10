from collections.abc import Callable
from time import monotonic

import numpy as np

from app.adapter.road_graph.jobs import RoadJobs
from app.domain.road_analysis import SettlementAccess, compare_access
from app.usecase.road_analysis import (
    AnalysisDetail,
    AnalysisJob,
    Candidate,
    ImpactLocation,
    VerifiedRoad,
)
from app.usecase.road_graph import RoadChange


class RoadEvaluation:
    def __init__(self, roads: RoadJobs) -> None:
        self.roads = roads

    def baseline(self, region: str) -> tuple[SettlementAccess, ...]:
        r = self.roads.delta.base.region(region)
        return tuple(
            SettlementAccess(
                p,
                int(r.population[i]),
                float(r.baseline_hansen[i] / r.normalization * 100),
                bool(np.isfinite(r.baseline_times[i]).any()),
            )
            for i, p in enumerate(r.ids)
        )

    def evaluate(
        self, job: AnalysisJob, candidate: Candidate, progress: Callable[[int], None]
    ) -> AnalysisDetail:
        start = monotonic()
        region = self.roads.data.region_name(job.region_id)
        before = self.baseline(region)
        factor = 0 if job.mode == "criticality" else 1 + job.percent / 100
        _, after = self.roads.routing.calculate_details(
            region, "road", [RoadChange(candidate.way_id, factor)], progress
        )
        effect = compare_access(before, after)
        tolerance = max(0.0001, abs(effect.before) * 0.00001)
        if (job.mode == "criticality" and effect.delta > tolerance) or (
            job.mode == "improvement" and effect.delta < -tolerance
        ):
            raise ValueError("monotonicity_violation")
        result = VerifiedRoad(
            candidate,
            effect.before,
            effect.after,
            effect.delta,
            effect.affected_population,
            effect.isolated_population,
            monotonic() - start,
        )
        data = self.roads.data
        locations = data.read("impact_places", {"region": region})
        lookup = {str(p[0]): p for p in locations}
        impacts = []
        for impact in effect.settlements:
            p = lookup.get(impact.point_id)
            if p is not None and impact.affected:
                impacts.append(ImpactLocation(impact, str(p[1]), float(p[2]), float(p[3])))
        impacts.sort(
            key=lambda p: (-int(p.impact.newly_isolated), -abs(p.impact.delta), p.impact.point_id)
        )
        way = data.indices_for([candidate.way_id])[candidate.way_id]
        e, n = data.edges, data.nodes
        pairs = {
            (min(int(e["src"][p]), int(e["dst"][p])), max(int(e["src"][p]), int(e["dst"][p])))
            for p in np.flatnonzero(e["way_idx"] == way)
        }
        lines = [
            [[float(n["lon"][a]), float(n["lat"][a])], [float(n["lon"][b]), float(n["lat"][b])]]
            for a, b in sorted(pairs)
        ]
        return AnalysisDetail(result, lines, impacts)
