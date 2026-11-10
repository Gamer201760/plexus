import json
from time import monotonic

from app.adapter.road_graph.delta_base import DeltaBase
from app.usecase.dto.road_graph import GRAPH_DATA_VERSION


def run(base: DeltaBase) -> None:
    started = monotonic()
    base.prepare()
    names = [str(row[0]) for row in base.data.read("regions")]
    errors = []
    for i, name in enumerate(names):
        value = base.region(name)
        errors.append(abs(value.baseline_index - value.expected))
        print(
            json.dumps(
                {
                    "completed": i + 1,
                    "total": len(names),
                    "region": name,
                    "error": errors[-1],
                    "elapsed": monotonic() - started,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    report = {
        "regions": names,
        "markets": 180,
        "max_baseline_error": max(errors),
        "elapsed_seconds": monotonic() - started,
        "method": "single_edge_delta",
        "snapshot": GRAPH_DATA_VERSION,
        "network": "road",
    }
    base.store.write_manifest(report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
