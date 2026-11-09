import json
from datetime import datetime, timezone

import pyarrow.parquet as pq

from artifacts import ROOT, file_record, write_json


def main() -> None:
    provenance = ROOT / "docs/results/tuva-provenance.json"
    manifest = json.loads(provenance.read_text())
    identifiers = {way for route in manifest["roads"].values() for way in route["osm_way_ids"]}
    source = ROOT / "data/pilot_graph_build/ways.parquet"
    ways = pq.read_table(source).to_pandas()
    selected = ways[ways.way_id.isin(identifiers)]
    if set(selected.way_id) != identifiers:
        raise ValueError("selected route ways are missing from source")
    records = []
    restrictions = []
    for row in selected.itertuples():
        tags = json.loads(row.source_tags)
        values = {key: tags.get(key) for key in ("access", "vehicle", "motor_vehicle", "motorcar")}
        records.append({"way_id": int(row.way_id), "operating_season": row.operating_season, **values})
        if any(value in {"no", "private"} for value in values.values()):
            restrictions.append(int(row.way_id))
    report = {"measured_at": datetime.now(timezone.utc).isoformat(), "method": "inspect explicit OSM access restriction tags on selected pilot route ways",
              "inputs": [file_record(provenance), file_record(source)], "unique_ways": len(records),
              "explicit_no_or_private": restrictions, "records": records,
              "limitation": "absence of restriction tags is not field verification or proof of year-round operability"}
    write_json(ROOT / "docs/results/pilot-road-tag-audit.json", report)
    print(f"checked {len(records)} ways; explicit no/private: {len(restrictions)}")


if __name__ == "__main__":
    main()
