"""Извлечь дороги и паромы из OSM PBF (Geofabrik, федеральные округа) в parquet.

    uv run python etl/osm_extract.py data/raw/osm_russia/<fd>.osm.pbf

Выход: data/osm_ways/<fd>.parquet — по строке на way:
way_id, highway, ref, name, surface, tracktype, oneway, is_bridge, is_ferry, is_seasonal,
nodes (list<int64>), lat (list<double>), lon (list<double>).
Пишется пачками, чтобы не держать весь округ в памяти Python.
"""
import json
import sys
from pathlib import Path

import osmium
import pyarrow as pa
import pyarrow.parquet as pq

from seasonality import operating_season
from artifacts import file_record, revision, write_json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "osm_ways"

HIGHWAYS = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "road",
    "residential", "living_street", "track",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
}
SCHEMA = pa.schema([
    ("way_id", pa.int64()), ("highway", pa.string()), ("ref", pa.string()), ("name", pa.string()),
    ("surface", pa.string()), ("tracktype", pa.string()), ("oneway", pa.string()),
    ("operating_season", pa.string()), ("source_tags", pa.string()),
    ("is_bridge", pa.bool_()), ("is_ferry", pa.bool_()), ("is_seasonal", pa.bool_()),
    ("nodes", pa.list_(pa.int64())), ("lat", pa.list_(pa.float64())), ("lon", pa.list_(pa.float64())),
])
BATCH = 200_000


def main(pbf: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / (pbf.name.split(".")[0] + ".parquet")
    source = file_record(pbf)
    manifest = dst.with_suffix(".json")
    if dst.exists() and manifest.exists():
        record = json.loads(manifest.read_text())
        if record.get("input") == source and record.get("extractor") == file_record(Path(__file__)):
            if record.get("output") == file_record(dst):
                print(f"skip verified {dst}", flush=True)
                return
    temporary = dst.with_suffix(".part")
    writer = pq.ParquetWriter(temporary, SCHEMA, compression="zstd")
    cols = {f.name: [] for f in SCHEMA}
    n = 0

    def flush():
        if cols["way_id"]:
            writer.write_table(pa.table(cols, schema=SCHEMA))
            for v in cols.values():
                v.clear()

    fp = (osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
          .with_locations()
          .with_filter(osmium.filter.EntityFilter(osmium.osm.WAY)))
    for w in fp:
        t = w.tags
        hw = t.get("highway")
        ferry = t.get("route") == "ferry"
        if not (hw in HIGHWAYS or ferry):
            continue
        try:
            ids = [nd.ref for nd in w.nodes]
            lat = [nd.location.lat for nd in w.nodes]
            lon = [nd.location.lon for nd in w.nodes]
        except osmium.InvalidLocationError:  # узел за пределами выгрузки
            continue
        if len(ids) < 2:
            continue
        cols["way_id"].append(w.id)
        cols["highway"].append(hw or "ferry")
        cols["ref"].append(t.get("ref"))
        cols["name"].append(t.get("name"))
        cols["surface"].append(t.get("surface"))
        cols["tracktype"].append(t.get("tracktype"))
        cols["oneway"].append(t.get("oneway"))
        cols["operating_season"].append(operating_season(dict(t)))
        cols["source_tags"].append(json.dumps(dict(t), ensure_ascii=False, sort_keys=True))
        cols["is_bridge"].append(t.get("bridge", "no") != "no")
        cols["is_ferry"].append(ferry)
        cols["is_seasonal"].append(
            t.get("ice_road") == "yes" or t.get("winter_road") == "yes" or t.get("seasonal", "no") != "no")
        cols["nodes"].append(ids); cols["lat"].append(lat); cols["lon"].append(lon)
        n += 1
        if len(cols["way_id"]) >= BATCH:
            flush()
            print(f"  {pbf.name}: {n} ways", flush=True)
    flush()
    writer.close()
    temporary.replace(dst)
    write_json(manifest, {"schema_version": 2, "input": source, "output": file_record(dst),
                          "extractor": file_record(Path(__file__)), "code": revision()})
    print(f"{pbf.name}: {n} ways -> {dst}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(Path(p))
