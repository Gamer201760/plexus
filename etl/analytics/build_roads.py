import argparse
from collections import defaultdict
from itertools import pairwise
from pathlib import Path
from time import perf_counter

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from app.adapter.road_graph.view_geometry import chains
from client import ClickHouse

ROOT = Path(__file__).resolve().parents[2]
DDL = """CREATE TABLE plexus_graph.road_lines__loading (
    way_id Int64, name String, highway LowCardinality(String), speed_kmh Float64,
    source_node Int64, target_node Int64, coordinates Array(Array(Float64)),
    rank UInt8, min_lon Float64, max_lon Float64, min_lat Float64, max_lat Float64,
    edge_count UInt32,
    INDEX bounds_lon_min min_lon TYPE minmax GRANULARITY 1,
    INDEX bounds_lon_max max_lon TYPE minmax GRANULARITY 1,
    INDEX bounds_lat_min min_lat TYPE minmax GRANULARITY 1,
    INDEX bounds_lat_max max_lat TYPE minmax GRANULARITY 1
) ENGINE=MergeTree ORDER BY (rank, floor(min_lon), floor(min_lat), way_id)
SETTINGS index_granularity=2048"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    started = perf_counter()
    root = args.root / "data/graph_ru"
    nodes = pq.read_table(root / "nodes.parquet", columns=["lon", "lat"])
    lon, lat = [nodes[name].to_numpy() for name in ["lon", "lat"]]
    edges = pq.read_table(root / "edges.parquet", columns=["src", "dst", "way_idx"])
    src, dst, way = [edges[name].to_numpy() for name in ["src", "dst", "way_idx"]]
    order = np.argsort(way, kind="stable")
    sorted_ways = way[order]
    ways = pq.ParquetFile(root / "ways.parquet")
    way_count = ways.metadata.num_rows
    cuts = np.searchsorted(sorted_ways, np.arange(way_count + 1, dtype=way.dtype))
    del sorted_ways
    print("Graph arrays loaded", flush=True)
    client = ClickHouse()
    client.request("CREATE DATABASE IF NOT EXISTS plexus_graph")
    client.request("DROP TABLE IF EXISTS plexus_graph.road_lines__loading")
    client.request(DDL)
    directory = args.root / "data/analytics-staging"
    directory.mkdir(exist_ok=True)
    total = 0
    for batch_number, batch in enumerate(
        ways.iter_batches(
            batch_size=30000,
            columns=["way_idx", "way_id", "name", "ref", "highway", "speed_kmh"],
        )
    ):
        rows = []
        for attrs in batch.to_pylist():
            w = attrs["way_idx"]
            first, last = cuts[w], cuts[w + 1]
            positions = order[first:last]
            if not len(positions):
                continue
            pairs = defaultdict(int)
            for a, b in zip(
                src[positions].tolist(), dst[positions].tolist(), strict=True
            ):
                pairs[(min(a, b), max(a, b))] += 1
            highway = attrs["highway"] or ""
            rank = {
                "motorway": 0,
                "trunk": 1,
                "primary": 2,
                "secondary": 3,
                "tertiary": 4,
            }.get(highway.replace("_link", ""), 5)
            for path in chains(set(pairs)):
                xs, ys = lon[path], lat[path]
                rows.append(
                    {
                        "way_id": attrs["way_id"],
                        "name": attrs["name"] or attrs["ref"] or str(attrs["way_id"]),
                        "highway": highway,
                        "speed_kmh": attrs["speed_kmh"],
                        "source_node": path[0],
                        "target_node": path[-1],
                        "coordinates": [
                            [float(x), float(y)] for x, y in zip(xs, ys, strict=True)
                        ],
                        "rank": rank,
                        "min_lon": float(xs.min()),
                        "max_lon": float(xs.max()),
                        "min_lat": float(ys.min()),
                        "max_lat": float(ys.max()),
                        "edge_count": sum(
                            pairs[(min(a, b), max(a, b))] for a, b in pairwise(path)
                        ),
                    }
                )
        if rows:
            path = directory / "road-lines.parquet"
            pq.write_table(pa.Table.from_pylist(rows), path, compression="zstd")
            client.parquet("plexus_graph.road_lines__loading", path)
            path.unlink()
            total += len(rows)
        print(
            f"ways={(batch_number + 1) * 30000}/{way_count} lines={total} seconds={perf_counter() - started:.1f}",
            flush=True,
        )
    actual = client.rows(
        "SELECT count() AS n, sum(edge_count) AS edges FROM plexus_graph.road_lines__loading"
    )[0]
    if int(actual["n"]) != total or int(actual["edges"]) != len(src):
        raise RuntimeError(
            f"Graph coverage mismatch: {actual}, expected {len(src)} directed edges"
        )
    exists = client.rows("EXISTS TABLE plexus_graph.road_lines")[0]["result"]
    if exists:
        client.request(
            "EXCHANGE TABLES plexus_graph.road_lines AND plexus_graph.road_lines__loading"
        )
        client.request("DROP TABLE plexus_graph.road_lines__loading")
    else:
        client.request(
            "RENAME TABLE plexus_graph.road_lines__loading TO plexus_graph.road_lines"
        )
    print(f"Complete: {total} lines represent {len(src)} directed edges", flush=True)


if __name__ == "__main__":
    main()
