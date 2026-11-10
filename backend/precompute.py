import argparse
import os
from pathlib import Path

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.precompute import run
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    config = load_settings(os.environ)
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    run(DeltaBase(GraphData(args.data_dir, ClickHouseGraphSnapshot(reader))))


if __name__ == "__main__":
    main()
