import argparse
import os
from pathlib import Path

from app.adapter.road_graph.precompute import run
from app.main import build_delta_base, build_reader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    reader = build_reader(load_settings(os.environ))
    run(build_delta_base(args.data_dir, ClickHouseGraphSnapshot(reader)))


if __name__ == "__main__":
    main()
