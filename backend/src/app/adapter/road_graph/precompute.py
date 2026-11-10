import argparse
import json
from pathlib import Path
from time import monotonic

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta_base import DeltaBase


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    started = monotonic()
    base = DeltaBase(GraphData(args.data_dir))
    base.prepare()
    with base.data.connect() as con:
        names = [
            str(row[0])
            for row in con.execute(
                "select region from idx_region where season='road' order by region"
            ).fetchall()
        ]
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
        "snapshot": "data-20261107",
        "network": "road",
    }
    path = base.store.folder / "manifest.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    temporary.replace(path)
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
