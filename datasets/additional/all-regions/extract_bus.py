import json
from collections import Counter, defaultdict
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from read_xlsx import sheets

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
BASE = ROOT/'data/additional/all-regions'
OUT = BASE/'derived/bus'

def write(name, rows):
    pq.write_table(pa.Table.from_pylist(rows),OUT/(name+'.parquet'),compression='zstd')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    filename = 'interregional-bus-20261105.xlsx'
    book = list(sheets(BASE/'raw'/filename))
    schemas = {}
    tables = {}
    for name,(sheet,rows) in zip(['routes','vehicles','carriers'],book[:3]):
        schemas[name] = rows[0][1]
        data = [dict(source_file=filename,source_sheet=sheet,source_row=number,**{k:r.get(k,'') for k in schemas[name]}) for number,r in rows[1:] if any(r.values())]
        write(name,data)
        tables[name] = data
    fields = ['route_registry_id','route_name','route_ordinal','stop_name','stop_region_code','stop_registry_id','winter_departure_days','winter_departure_time','winter_dwell_time','winter_arrival_days','winter_arrival_time','winter_period','summer_departure_days','summer_departure_time','summer_dwell_time','summer_arrival_days','summer_arrival_time','summer_period']
    schedules = []
    blank_rows = 0
    for direction,(sheet,rows) in zip(['forward','backward'],book[3:]):
        schemas[direction] = [r for _,r in rows[:2]]
        for number,source in rows[2:]:
            if not any(source.values()):
                blank_rows += 1
                continue
            row = dict(zip(fields,[source.get(chr(65+i),'') for i in range(18)]))
            row.update(direction=direction,source_file=filename,source_sheet=sheet,source_row=number)
            schedules.append(row)
    write('schedules',schedules)
    route_ids = {r['A'] for r in tables['routes']}
    assert len(route_ids)==len(tables['routes'])
    assert {r['route_registry_id'] for r in schedules} == route_ids
    codes = defaultdict(set)
    for r in schedules:
        codes[r['stop_region_code']].add(r['route_registry_id'])
    links = [dict(stop_region_code=code,route_registry_id=identifier) for code,ids in sorted(codes.items()) for identifier in sorted(ids)]
    write('route_regions',links)
    stop_file = 'bus-stops-20261009.xlsx'
    for name,(sheet,rows) in zip(['stops','stop_capacity'],sheets(BASE/'raw'/stop_file)):
        schemas[name] = rows[0][1]
        tables[name] = [dict(source_file=stop_file,source_sheet=sheet,source_row=n,**{k:r.get(k,'') for k in schemas[name]}) for n,r in rows[1:] if any(r.values())]
        write(name,tables[name])
    known_stops = {r['C'] for r in tables['stops']}
    counts = Counter(r['stop_region_code'] for r in schedules)
    mapping = json.loads((META/'bus-region-map.json').read_text())
    assert set(codes)=={r['stop_region_code'] for r in mapping}
    regions = []
    for region in mapping:
        code = region['stop_region_code']
        regions.append(dict(**region,route_count=len(codes[code]),stop_schedule_rows=counts[code],distinct_stop_ids=len({r['stop_registry_id'] for r in schedules if r['stop_region_code']==code})))
    atlas = json.loads((META/'atlas-regions.json').read_text())
    represented = {r['atlas_region_id'] for r in regions if r['atlas_region_id']}
    profile = dict(route_date='2026-11-05',stop_date='2026-10-09',routes=len(route_ids),schedule_rows=len(schedules),stop_records=len(tables['stops']),route_region_pairs=len(links),regions_in_source=len(regions),atlas_regions_with_records=len(represented),atlas_regions_without_records=[r for r in atlas if r['region_id'] not in represented],blank_source_rows_skipped=blank_rows,schedule_stop_ids_missing_in_older_stop_registry=sorted({r['stop_registry_id'] for r in schedules}-known_stops),regions=regions)
    (META/'bus-profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
    schemas['schedule_fields'] = fields
    (META/'bus-schema.json').write_text(json.dumps(schemas,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in profile.items() if k not in {'regions','schedule_stop_ids_missing_in_older_stop_registry','atlas_regions_without_records'}})

if __name__ == '__main__':
    main()
