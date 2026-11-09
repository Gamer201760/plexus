import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
import pyarrow.parquet as pq
from shapely.geometry import Point, shape
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
BASE = ROOT / 'data/additional/stavropol'

def csv_rows(filename):
    with (BASE/'derived'/filename).open(newline='') as source:
        return list(csv.DictReader(source))

def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()

def main():
    downloads = json.loads((META/'downloads.json').read_text())
    for row in downloads:
        if row['status'] == 'downloaded':
            path = ROOT/row['path']
            assert path.stat().st_size == row['bytes'], path
            assert digest(path) == row['sha256'], path
    inventory = []
    for path in sorted(BASE.rglob('*')):
        if not path.is_file() or path.suffix == '.part':
            continue
        row = dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=digest(path))
        if path.suffix == '.csv':
            with path.open(newline='') as source:
                reader = csv.DictReader(source)
                row['columns'] = reader.fieldnames
                row['rows'] = sum(1 for _ in reader)
        elif path.suffix == '.parquet':
            table = pq.ParquetFile(path)
            row.update(rows=table.metadata.num_rows,schema=str(table.schema_arrow))
        elif path.suffix in {'.xlsx','.docx'}:
            with ZipFile(path) as archive:
                assert archive.testzip() is None, path
        inventory.append(row)
    settlements = csv_rows('settlements.csv')
    ids = {r['point_id'] for r in settlements}
    assert len(ids) == len(settlements) == 760
    assert {r['region_id'] for r in settlements} == {'07000000'}
    lights = csv_rows('settlement_lights.csv')
    assert len(lights) == len({(r['point_id'],r['year']) for r in lights}) == 1520
    assert {r['point_id'] for r in lights} == ids
    routes = csv_rows('interregional_bus_routes.csv')
    route_ids = {r['A'] for r in routes}
    assert len(routes) == len(route_ids) == 653
    schedules = csv_rows('interregional_bus_schedules.csv')
    assert {r['route_registry_id'] for r in schedules} == route_ids
    assert {r['route_registry_id'] for r in schedules if r['stop_region_code'].strip()=='26'} == route_ids
    boundary = prep(shape(json.loads((BASE/'derived/boundary.geojson').read_text())['geometry']))
    pois = pq.read_table(BASE/'derived/osm_places.parquet').to_pylist()
    assert len(pois) == len({(r['osm_type'],r['osm_id']) for r in pois})
    assert all(boundary.covers(Point(r['lon'],r['lat'])) for r in pois)
    ways = pq.read_table(BASE/'derived/network_ways.parquet').to_pylist()
    assert len(ways) == len({r['osm_way_id'] for r in ways})
    assert all(len(r['lon'])==len(r['lat'])==len(r['node_ids'])>=2 for r in ways)
    medical_checks = {}
    for year in [2025,2026]:
        care = csv_rows(f'medical_care_rows_{year}.csv')
        org = csv_rows(f'medical_organizations_{year}.csv')
        assert {r['registry_year_id'] for r in care} == {r['registry_year_id'] for r in org}
        assert len(org) == len({r['registry_year_id'] for r in org})
        assert sum(int(r['care_source_rows']) for r in org) == len(care)
        medical_checks[year] = dict(care_rows=len(care),organizations=len(org))
    result = dict(validated_at=datetime.now(timezone.utc).isoformat(),status='passed',files=len(inventory),bytes=sum(r['bytes'] for r in inventory),checks=['download size and SHA256','XLSX/DOCX ZIP integrity','settlement uniqueness and region','lights settlement-year uniqueness and coverage','bus routes referenced by schedules and official stop region','OSM feature identity and POI boundary containment','OSM coordinate and node-array alignment','medical organization and care-row reconciliation'],medical=medical_checks,not_tested=['routing connectivity or travel times','current operation of registry services','geocoding of medical care addresses','OCR of scanned Predgorny PDF','current legal status of historical road and tax lists'])
    (META/'files.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
    (META/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
