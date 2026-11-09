import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text())

def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()

def main():
    manifests = [META/'downloads.json',META.parent/'all-regions-medical/manifest.json',META.parent/'all-regions-osm/downloads.json',ROOT/'data/additional/all-regions-roads/downloads-manifest.json',ROOT/'data/additional/all-regions-roads/supplementary/downloads-manifest.json']
    references = []
    for manifest in manifests:
        references.extend(r for r in read(manifest) if r.get('sha256') and r.get('path'))
    base = read(META/'base-profile.json')
    references.extend(e for region in base['regions'] for e in region['exports'].values())
    references.append(base['outside_atlas'])
    references.extend(read(META/'regional-supplement-profile.json'))
    for entry in references:
        path = ROOT/entry['path']
        assert path.is_file(),path
        assert digest(path)==entry['sha256'],path
        if 'bytes' in entry:
            assert path.stat().st_size==entry['bytes'],path
        if path.suffix=='.parquet' and 'rows' in entry:
            assert pq.ParquetFile(path).metadata.num_rows==entry['rows'],path
    inventory = []
    for directory in sorted((ROOT/'data/additional').glob('all-regions*')):
        for path in sorted(directory.rglob('*')):
            if not path.is_file() or path.suffix in {'.part','.partial'}:
                continue
            entry = dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=digest(path))
            if path.suffix=='.parquet':
                parquet=pq.ParquetFile(path)
                entry.update(rows=parquet.metadata.num_rows,schema=str(parquet.schema_arrow))
            if path.suffix in {'.zip','.xlsx'}:
                with ZipFile(path) as archive:
                    assert archive.testzip() is None,path
            inventory.append(entry)
    coverage = read(META/'coverage.json')
    assert len(coverage)==len({r['region_id'] for r in coverage})==82
    assert all(r['medical_registry_rows']>0 and r['osm_url'] for r in coverage)
    bus=pq.read_table(ROOT/'data/additional/all-regions/derived/bus/schedules.parquet')
    assert bus.num_rows==53506
    assert len(set(bus.column('route_registry_id').to_pylist()))==5550
    assert len(set(bus.column('stop_region_code').to_pylist()))==81
    result=dict(validated_at=datetime.now(timezone.utc).isoformat(),status='passed',files=len(inventory),bytes=sum(r['bytes'] for r in inventory),manifest_references_checked=len(references),regional_files=len(list((ROOT/'data/additional/all-regions/derived/regions').glob('*/*.parquet'))),atlas_regions=82,checks=['all referenced file SHA256 and sizes','Parquet record counts','ZIP/XLSX CRC integrity','82 unique coverage rows','82 nonempty national medical slices and OSM source links','5550 national bus routes, 53506 schedule rows, 81 source region codes'],limits=['HEAD verification is not downloaded OSM or verified geographic completeness','old national medical and road snapshots are not current service operation','not a complete national local-transit or road-traffic inventory'])
    (META/'files.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
    (META/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
