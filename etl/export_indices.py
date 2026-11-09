import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np

from artifacts import ROOT, file_record, revision, write_json


SCENARIOS = {"road", "road_summer", "road_winter", "summer", "winter"}
PUBLIC = ROOT / "frontend" / "atlas" / "public"


def export(database: Path, target: Path) -> dict:
    regions = json.loads((PUBLIC / "atlas.json").read_text())["regions"]
    known = {row["id"] for row in regions}
    with duckdb.connect(str(database), read_only=True) as con:
        meta = con.sql("select * from index_model_metadata").df().iloc[0].to_dict()
        frame = con.sql("""select i.*, s.oktmo as region_id from idx_region i
            join stg_settlements s on i.region = s.region and s.object_level = 'Регион' order by i.season, s.oktmo""").df()
        totals = con.sql("select season, count(*) points, sum(population) population, sum(population * hansen_idx) / sum(population) mean_index from idx_np group by season order by season").df().to_dict("records")
        targets = con.sql("select city, population from market_cities order by city").df().to_dict("records")
    if set(frame.season) != SCENARIOS or set(frame.region_id) != known:
        raise ValueError("regional export must cover the 82 known regions and all five scenarios")
    if frame.duplicated(["region_id", "season"]).any() or len(frame) != len(known) * len(SCENARIOS):
        raise ValueError("duplicate or missing regional index rows")
    if not np.isfinite(frame.hansen_idx).all() or (frame.hansen_idx < 0).any():
        raise ValueError("invalid regional Hansen values")
    road_mean = next(row["mean_index"] for row in totals if row["season"] == "road")
    if abs(road_mean - 100.) > 1e-7:
        raise ValueError("fixed road baseline is not normalized to 100")
    fields = ["region_id", "season", "hansen_idx", "hansen_1h", "hansen_2h", "hansen_4h",
              "population", "n_np", "covered_population", "covered_settlements", "aria", "rai", "gini"]
    records = frame[fields].replace({np.nan: None}).to_dict("records")
    for row in records:
        row["model_version"] = meta["model_version"]
    manifest = {"model_version": meta["model_version"], "normalization_base": meta["normalization_base"],
                "half_life_h": 2, "sensitivity_half_lives_h": [1, 2, 4], "code": revision(),
                "implementation": [file_record(ROOT / "etl" / name) for name in (
                    "access_russia.py", "access_network.py", "graphlib.py", "indices.py", "export_indices.py")],
                "measured_at": datetime.now(timezone.utc).isoformat(), "regional_rows": len(records),
                "regions": len(known), "scenarios": sorted(SCENARIOS), "totals": totals,
                "targets": targets, "inputs": [file_record(database), file_record(ROOT / "data/graph_ru/manifest.json")],
                "assumptions": ["uniform_headways_random_need", "independent_transfer_waits",
                    "unknown_trunk_frequency_assumed_one_per_week", "osm_operability_not_field_verified",
                    "roads_undirected_for_national_model"],
                "excluded_origin_regions": ["Москва", "Санкт-Петербург", "Севастополь"],
                "coverage_definition": "population and settlements with at least one finite modelled market route",
                "population_scope": "settlement population in the input snapshot, not the entire Russian population"}
    encoded = json.dumps({"rows": records, "metadata": meta}, ensure_ascii=False, sort_keys=True, allow_nan=False)
    version = hashlib.sha256(encoded.encode()).hexdigest()
    for row in records:
        row["artifact_version"] = version
    manifest["artifact_version"] = version
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".part")
    temporary.write_text(json.dumps(records, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    temporary.replace(target)
    write_json(target.with_name("index-manifest.json"), manifest)
    print(f"exported {len(records)} regional rows; artifact {version}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=ROOT / "data/casechamp.duckdb")
    parser.add_argument("--output", type=Path, default=ROOT / "data/index_candidate/indices.json")
    args = parser.parse_args()
    export(args.database, args.output)
