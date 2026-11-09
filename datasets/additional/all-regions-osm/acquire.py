import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'datasets/additional/all-regions-osm'
RAW = ROOT / 'data/additional/all-regions-osm/raw'
RAW.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()


def fetch(item):
    key, url = item
    entry = dict(id=key, url=url, retrieved_at=NOW, tls_verification=url.startswith('https://'))
    try:
        response = requests.get(url, timeout=32)
        entry.update(http_status=response.status_code, final_url=response.url)
        response.raise_for_status()
        path = RAW / key
        path.write_bytes(response.content)
        entry.update(status='downloaded', path=str(path.relative_to(ROOT)), bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest())
    except Exception as error:
        entry.update(status='failed', error=str(error))
    return entry


indexes = list(ThreadPoolExecutor(4).map(fetch, [
    ('osmlab-index.html', 'http://www.osmlab.ru/'),
    ('geofabrik-russia.html', 'https://download.geofabrik.de/russia.html'),
    ('geofabrik-index-v1.json', 'https://download.geofabrik.de/index-v1.json'),
    ('osmfr-russia-index.html', 'https://download.openstreetmap.fr/extracts/russia/'),
]))
(OUT / 'downloads.json').write_text(json.dumps(indexes, ensure_ascii=False, indent=2) + '\n')
districts = ['central_federal_district', 'far_eastern_federal_district', 'north_caucasian_federal_district', 'northwestern_federal_district', 'siberian_federal_district', 'southern_federal_district', 'ural_federal_district', 'volga_federal_district']
indexes.extend(ThreadPoolExecutor(8).map(fetch, [(f'osmfr-{d}.html', f'https://download.openstreetmap.fr/extracts/russia/{d}/') for d in districts]))
(OUT / 'downloads.json').write_text(json.dumps(indexes, ensure_ascii=False, indent=2) + '\n')
rows = []
if (RAW / 'osmlab-index.html').exists():
    soup = BeautifulSoup((RAW / 'osmlab-index.html').read_bytes(), 'html.parser')
    for tr in soup.select('tr'):
        links = tr.select('a[href]')
        for link in links:
            url = urljoin('https://www.osmlab.ru/', link['href'])
            if '.pbf' not in url:
                continue
            cells = tr.select('td')
            rows.append(dict(provider='OSMLab', name=cells[0].get_text(' ', strip=True), source_url='https://www.osmlab.ru/', url=url, source_timestamp=cells[1].get_text(' ', strip=True) if len(cells) > 1 else None, source_region_code=url.split('/')[-1].split('.')[0], coverage='provider-defined regional extract'))
if (RAW / 'geofabrik-index-v1.json').exists():
    features = json.loads((RAW / 'geofabrik-index-v1.json').read_text())['features']
    for feature in features:
        p = feature['properties']
        if p.get('id') == 'russia' or p.get('parent') == 'russia':
            rows.append(dict(provider='Geofabrik', name=p['name'], source_region_code=p['id'], source_url='https://download.geofabrik.de/russia.html', url=p['urls']['pbf'], coverage='provider-defined extract; consult saved polygon', geometry=feature.get('geometry'), urls=p.get('urls')))
if (RAW / 'osmfr-russia-index.html').exists():
    soup = BeautifulSoup((RAW / 'osmfr-russia-index.html').read_bytes(), 'html.parser')
    for link in soup.select('a[href]'):
        href = link['href']
        if href.endswith('-latest.osm.pbf'):
            rows.append(dict(provider='OpenStreetMap France', name=href.removesuffix('-latest.osm.pbf'), source_region_code=href.removesuffix('-latest.osm.pbf'), source_url='https://download.openstreetmap.fr/extracts/russia/', url=urljoin('https://download.openstreetmap.fr/extracts/russia/', href), coverage='provider-defined federal-district extract'))


def head(row):
    row.update(status='source_link_discovered', pbf_downloaded=False, checked_at=NOW)
    try:
        r = requests.head(row['url'], allow_redirects=True, timeout=15)
        row.update(http_status=r.status_code, final_url=r.url, content_length=int(r.headers['Content-Length']) if r.headers.get('Content-Length', '').isdigit() else None, last_modified=r.headers.get('Last-Modified'), etag=r.headers.get('ETag'), content_type=r.headers.get('Content-Type'))
        if r.status_code == 200:
            row['status'] = 'head_verified'
    except Exception as error:
        row['head_error'] = str(error)
    return row


for district in districts:
    path = RAW / f'osmfr-{district}.html'
    if not path.exists():
        continue
    for link in BeautifulSoup(path.read_bytes(), 'html.parser').select('a[href]'):
        href = link['href']
        if href.endswith('-latest.osm.pbf'):
            rows.append(dict(provider='OpenStreetMap France', name=href.removesuffix('-latest.osm.pbf'), source_region_code=href.removesuffix('-latest.osm.pbf'), source_url=f'https://download.openstreetmap.fr/extracts/russia/{district}/', url=urljoin(f'https://download.openstreetmap.fr/extracts/russia/{district}/', href), coverage='provider-defined regional extract', district=district))
rows = list(ThreadPoolExecutor(12).map(head, rows))
(OUT / 'sources.json').write_text(json.dumps(dict(retrieved_at=NOW, scope='source coverage labels only; no political jurisdiction assertion', indexes=indexes, sources=rows), ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(indexes=[(r['id'], r['status']) for r in indexes], sources=len(rows), head_verified=sum(r['status'] == 'head_verified' for r in rows)), ensure_ascii=False))
