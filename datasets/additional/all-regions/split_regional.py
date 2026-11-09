import gzip
import hashlib
import json
from pathlib import Path
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
OUT = ROOT/'data/additional/all-regions/derived'

def main():
    with gzip.open(ROOT/'data/additional/all-regions-medical/f032-organizations.jsonl.gz','rt') as source:
        medical = pa.Table.from_pylist([dict(json.loads(line),source_record_ordinal=i) for i,line in enumerate(source,1)])
    atlas = json.loads((META/'atlas-regions.json').read_text())
    medical_map = {r['region_id_if_known']:r['region_name'] for r in json.loads((META.parent/'all-regions-medical/region-crosswalk.json').read_text()) if r['region_id_if_known']}
    bus_map = {r['atlas_region_id']:r['stop_region_code'] for r in json.loads((META/'bus-region-map.json').read_text()) if r['atlas_region_id']}
    routes = pq.read_table(OUT/'bus/routes.parquet')
    schedules = pq.read_table(OUT/'bus/schedules.parquet')
    links = pq.read_table(OUT/'bus/route_regions.parquet')
    manifest = []
    for region in atlas:
        identifier = region['region_id']
        directory = OUT/'regions'/identifier
        region_medical = medical.filter(pc.equal(medical['SUBJ'],medical_map[identifier]))
        code = bus_map.get(identifier,'not_present')
        route_ids = links.filter(pc.equal(links['stop_region_code'],code))['route_registry_id']
        region_routes = routes.filter(pc.is_in(routes['A'],value_set=route_ids))
        region_schedules = schedules.filter(pc.equal(schedules['stop_region_code'],code))
        for name,table in [('medical_2026',region_medical),('bus_routes_20261105',region_routes),('bus_stop_schedules_20261105',region_schedules)]:
            path = directory/(name+'.parquet')
            pq.write_table(table,path,compression='zstd')
            manifest.append(dict(region_id=identifier,kind=name,path=str(path.relative_to(ROOT)),rows=table.num_rows,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (META/'regional-supplement-profile.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Regional supplemental files:',len(manifest))

if __name__ == '__main__':
    main()
