import argparse
import hashlib
import json
import platform
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.sparse.csgraph import floyd_warshall

from app.domain.pilot import EdgeChange
from app.repository.files.pilots import JsonPilotRepository
from app.usecase.pilots import PilotQueries
from artifacts import ROOT, file_record, revision, write_json


SCHEDULED = {"air", "river", "scheduled_ferry", "rail"}


def independent_times(pilot, season, changes):
    points = {point.id: index for index, point in enumerate(pilot.points)}
    matrix = np.full((len(points), len(points)), np.inf)
    np.fill_diagonal(matrix, 0.)
    overrides = {change.edge_id: change for change in changes}
    for edge in pilot.edges:
        change = overrides.get(edge.id)
        if season not in edge.seasons or change is not None and change.enabled is False:
            continue
        frequency = edge.frequency_per_week
        if change is not None and change.frequency_per_week is not None:
            frequency = change.frequency_per_week
        if frequency is None:
            frequency = edge.assumed_frequency_per_week
        waiting = 0.
        if edge.mode in SCHEDULED:
            if frequency is None:
                continue
            waiting = 84 / frequency
        a, b = points[edge.from_id], points[edge.to_id]
        matrix[a, b] = min(matrix[a, b], edge.travel_h + waiting)
        if edge.bidirectional:
            matrix[b, a] = min(matrix[b, a], edge.travel_h + waiting)
    result = floyd_warshall(matrix, directed=True)
    return {pair.id: result[points[pair.from_id], points[pair.to_id]] for pair in pilot.pairs}


def main(directory: Path, output: Path) -> None:
    repository = JsonPilotRepository(directory)
    query = PilotQueries(repository)
    pilot = repository.get("tuva")
    source = directory / "pilots" / "tuva.json"
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    variants = {"baseline": (), "frequency_4": (EdgeChange("manual:0", frequency_per_week=4),),
                "frequency_7": (EdgeChange("manual:0", frequency_per_week=7),),
                "seasonal_closure": (EdgeChange("manual:5", enabled=False),
                                     EdgeChange("manual:6", enabled=False))}
    results, assertions = [], 0
    for season in ("summer", "winter"):
        for variant, changes in variants.items():
            result = query.evaluate(pilot.id, season, pilot.model_version, pilot.artifact_version, changes)
            expected = independent_times(pilot, season, changes)
            for pair in result.pairs:
                actual = pair.changed.total_h
                reference = expected[pair.pair_id]
                if np.isfinite(reference):
                    assert actual is not None and abs(actual - reference) < 1e-8, (variant, pair)
                else:
                    assert actual is None and pair.changed.status == "no_route", (variant, pair)
                assertions += 1
            assert result == query.evaluate(pilot.id, season, pilot.model_version,
                                            pilot.artifact_version, changes)
            results.append({"variant": variant, **asdict(result)})
    timings = []
    for index in range(200):
        started = time.perf_counter()
        query.evaluate(pilot.id, "summer" if index % 2 else "winter", pilot.model_version,
                       pilot.artifact_version, variants["frequency_7"])
        timings.append(time.perf_counter() - started)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original
    p95 = float(np.percentile(timings, 95))
    assert p95 <= 2., p95
    report = {"measured_at": datetime.now(timezone.utc).isoformat(), "status": "calculation_verified_not_http_or_browser", "code": revision(),
              "artifact": file_record(source), "model_version": pilot.model_version,
              "independent_method": "dense Floyd-Warshall versus production Dijkstra",
              "pair_comparisons": assertions, "repeated_inputs_identical": True,
              "input_unchanged": True, "benchmark": {"samples": len(timings), "p95_s": p95,
                  "scope": "cached in-process use case, excludes HTTP and initial load",
                  "platform": platform.platform(), "machine": platform.machine()},
              "implementation": [file_record(path) for path in (
                  ROOT / "backend/src/app/domain/pilot.py",
                  ROOT / "backend/src/app/domain/pilot_routing.py",
                  ROOT / "backend/src/app/domain/waiting.py",
                  ROOT / "backend/src/app/usecase/pilots.py",
                  ROOT / "backend/src/app/repository/files/pilots.py",
                  ROOT / "etl/validate_pilot.py")],
              "results": results}
    write_json(output, report)
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "frontend" / "atlas" / "public")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/results/pilot-validation.json")
    args = parser.parse_args()
    main(args.data_dir, args.output)
