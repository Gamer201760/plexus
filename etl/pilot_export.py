import csv
import hashlib
import json
from dataclasses import asdict

import duckdb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.sparse.csgraph import dijkstra

from app.domain.pilot import Pilot, PilotEdge, PilotPair, PilotPoint
from artifacts import ROOT, file_record, revision, write_json
from graphlib import build_csr
from manual_links import link_hours


GRAPH = ROOT / "data" / "pilot_graph_build"
OUTPUT = ROOT / "data" / "pilot_candidate" / "pilots"
MODEL_VERSION = "tuva-frequency-v1"


def road_edges(points: pd.DataFrame) -> tuple[list[PilotEdge], dict]:
    terminals = pq.read_table(GRAPH / "points.parquet").to_pandas().set_index("point_id")
    terminals = terminals.loc[points.point_id]
    terminals = terminals[terminals.on_road]
    source = pq.read_table(GRAPH / "edges.parquet").to_pandas()
    ways = pq.read_table(GRAPH / "ways.parquet").to_pandas()
    node_count = pq.read_metadata(GRAPH / "nodes.parquet").num_rows
    output, provenance = [], {}
    for season in ("summer", "winter"):
        keep = ways.operating_season.isin(["all", season]).values[source.way_idx]
        edges = source[keep].sort_values("h").drop_duplicates(["src", "dst"])
        graph = build_csr(edges.src.values, edges.dst.values, edges.h.values, node_count)
        distances, predecessors = dijkstra(graph, directed=True, indices=terminals.node.values,
                                           return_predecessors=True)
        way_by_pair = {(int(a), int(b)): int(w) for a, b, w in
                       zip(edges.src, edges.dst, edges.way_idx)}
        for index, (origin_id, origin) in enumerate(terminals.iterrows()):
            for target_id, target in terminals.iterrows():
                hours = distances[index, int(target.node)]
                if origin_id == target_id or not np.isfinite(hours):
                    continue
                identifier = f"road:{season}:{origin_id}:{target_id}"
                cursor, path = int(target.node), []
                while cursor != int(origin.node):
                    previous = int(predecessors[index, cursor])
                    path.append(int(ways.way_id.iloc[way_by_pair[previous, cursor]]))
                    cursor = previous
                hours += (origin.snap_km + target.snap_km) / 15
                output.append(PilotEdge(identifier, origin_id, target_id, "road", (season,),
                                        float(hours), None, None,
                                        "https://download.geofabrik.de/russia/siberian-fed-district.html",
                                        "snapshot 2026-11-09", ("osm_operability_not_field_verified",
                                        "snap_access_15_kmh_max_5_km", "modelled_road_speeds"),
                                        editable=False, bidirectional=False))
                provenance[identifier] = {"osm_way_ids": list(reversed(path)),
                                           "source_node": int(origin.node),
                                           "target_node": int(target.node)}
    return output, provenance


def build_pilot() -> tuple[Pilot, dict]:
    with (ROOT / "data_manual" / "tuva_links.csv").open() as stream:
        records = list(csv.DictReader(stream))
    endpoints = {row[key] for row in records for key in ("from_id", "to_id")}
    with duckdb.connect(str(ROOT / "data" / "casechamp.duckdb"), read_only=True) as con:
        points = con.sql("select oktmo as point_id, settlement as name, latitude as lat, longitude as lon "
                         "from stg_settlements where object_level = 'Населенный пункт'").df()
    points = points[points.point_id.isin(endpoints)].reset_index(drop=True)
    if set(points.point_id) != endpoints or points.lat.isna().any() or points.lon.isna().any():
        raise ValueError("pilot endpoints are missing or have no coordinates")
    roads, provenance = road_edges(points)
    links = pd.DataFrame(records)
    for column in ("km", "freq_per_week"):
        links[column] = pd.to_numeric(links[column].replace("", np.nan))
    calculated = link_hours(links, points)
    manual = []
    for index, row in calculated.iterrows():
        frequency = float(row.freq_per_week) if pd.notna(row.freq_per_week) else None
        identifier = f"manual:{index}"
        manual.append(PilotEdge(
            identifier, row.from_id, row.to_id, row["mode"],
            ("summer", "winter") if row.season == "all" else (row.season,),
            float(row.travel_h), frequency, 1. if row.freq_assumed else None,
            row.source_url, row.source_date or None,
            ("historical_link_current_service_unverified", "modelled_mode_speed_and_overhead"),
            headway_intervals_h=(48., 120.) if index == 0 else ()))
    pilot = Pilot("tuva", "Поездки к центрам Тывы", MODEL_VERSION, "pending",
                  tuple(PilotPoint(row.point_id, row.name, row.lat, row.lon)
                        for row in points.itertuples()), tuple(roads + manual),
                  (PilotPair("kungurtug-kyzyl", "93643425101", "93701000001"),
                   PilotPair("toora-kyzyl", "93650444101", "93701000001"),
                   PilotPair("systyg-toora", "93650433101", "93650444101")),
                  ("uniform_headways_random_need", "independent_transfer_waits",
                   "no_current_schedule_guarantee", "no_cost_or_demand_estimate"))
    return pilot, provenance


def main() -> None:
    pilot, roads = build_pilot()
    payload = asdict(pilot)
    payload.pop("artifact_version")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["artifact_version"] = hashlib.sha256(encoded.encode()).hexdigest()
    manifest = {"model_version": MODEL_VERSION, "artifact_version": payload["artifact_version"],
                "code": revision(), "inputs": [file_record(path) for path in (
                    ROOT / "data_manual" / "tuva_links.csv",
                    ROOT / "data" / "raw" / "osm_russia" / "siberian.osm.pbf",
                    *(ROOT / "data" / "raw" / "settlements").glob("*.parquet"),
                    *(GRAPH.glob("*.parquet")))], "roads": roads,
                "coverage": {"points": len(pilot.points), "edges": len(pilot.edges),
                             "region": "Республика Тыва", "road_extract": "Siberian federal district"}}
    write_json(ROOT / "data" / "tuva-provenance.json", manifest)
    write_json(OUTPUT / "tuva.json", payload)
    print(f"exported {len(pilot.edges)} edges; version {payload['artifact_version']}")


if __name__ == "__main__":
    main()
