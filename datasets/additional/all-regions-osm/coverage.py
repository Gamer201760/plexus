import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'datasets/additional/all-regions-osm'
parser = argparse.ArgumentParser()
parser.add_argument('--atlas', type=Path, default=ROOT / 'datasets/additional/all-regions/atlas-regions.json')
ATLAS = parser.parse_args().atlas
registry = json.loads((OUT / 'sources.json').read_text())
regions = json.loads(ATLAS.read_text())
aliases = {
    'Ненецкий АО': 'Ненецкий автономный округ',
    'ЯНАО': 'Ямало-Ненецкий автономный округ',
    'Чукотский АО': 'Чукотский автономный округ',
    'Ханты-Мансийский автономный округ': 'Ханты-Мансийский автономный округ — Югра',
    'Республика Северная Осетия': 'Республика Северная Осетия — Алания',
}
by_name = {r['name']: r for r in registry['sources'] if r['provider'] == 'OSMLab'}
by_slug = {r['source_region_code']: r for r in registry['sources'] if r['provider'] == 'OpenStreetMap France'}
fallbacks = {'Республика Адыгея': 'adygea_republic', 'Республика Хакасия': 'khakassia_republic'}
coverage = []
for region in regions:
    source = by_name.get(aliases.get(region['name'], region['name']))
    fallback = by_slug.get(fallbacks.get(region['name']))
    choices = [s for s in (source, fallback) if s]
    coverage.append(dict(region_id=region['region_id'], name=region['name'], source_urls=[s['url'] for s in choices], source_region_codes=[s['source_region_code'] for s in choices], source_statuses=[s['status'] for s in choices], osmlab_index_present=source is not None, downloaded=False, content_coverage_verified=False, source_mapping_method='exact source label or explicit alias; fallback slug for Adygea and Khakassia'))
result = dict(atlas_path='datasets/additional/all-regions/atlas-regions.json', atlas_sha256=hashlib.sha256(ATLAS.read_bytes()).hexdigest(), atlas_regions=len(regions), mapped_region_links=sum(bool(r['source_urls']) for r in coverage), osmlab_matches=sum(r['osmlab_index_present'] for r in coverage), regions=coverage)
(OUT / 'atlas-coverage.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
assert len(coverage) == 82
assert all(r['source_urls'] for r in coverage)
assert all(r['source_statuses'] == ['head_verified'] for r in coverage)
assert all(r['pbf_downloaded'] is False for r in registry['sources'])
assert len({r['url'] for r in registry['sources']}) == len(registry['sources'])
for item in registry['indexes']:
    if item['status'] == 'downloaded':
        path = ROOT / item['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
print(json.dumps({k:v for k,v in result.items() if k != 'regions'}, ensure_ascii=False))
