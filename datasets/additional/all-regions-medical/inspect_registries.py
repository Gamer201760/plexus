import collections
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

BASE = Path(__file__).resolve().parents[3]
DATA = BASE / 'data/additional/all-regions-medical'
OUT = BASE / 'datasets/additional/all-regions-medical'
RAW = DATA / 'raw'
CHECKED = '2026-11-09'
SOURCE = 'https://www.kamtfoms.ru/informacionnye_resursy/paket_nsi/'
ARCHIVES = {
    'F001': 'f001_7_68_xml.zip',
    'F031': 'f031_4_167_xml.zip',
    'F032': 'f032_5_267_xml.zip',
    'F033': 'f033_3_409_xml.zip',
}
ALIASES = {
    'Кемеровская область': 'Кемеровская область - Кузбасс',
    'Республика Северная Осетия': 'Республика Северная Осетия-Алания',
    'Ханты-Мансийский автономный округ': 'Ханты-Мансийский АО',
    'ЯНАО': 'Ямало-Ненецкий АО',
    'Еврейская автономная область': 'Еврейская АО',
}


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read(name):
    archive = zipfile.ZipFile(RAW / ARCHIVES[name])
    return ET.fromstring(archive.read(name + '.xml'))


def records(root, tag):
    return [{item.tag: item.text or '' for item in row} for row in root.findall(tag)]


roots = {key: read(key) for key in ARCHIVES}
funds = records(roots['F001'], 'TFOMS')
funds_by_code = {row['tf_kod']: row for row in funds}
medical = records(roots['F032'], 'zap')
counts = collections.Counter(row['SUBJ'] for row in medical)
codes = collections.defaultdict(set)
for row in medical:
    codes[row['SUBJ']].add(row['UIDMO'][:2])
atlas_path = BASE / 'datasets/additional/all-regions/atlas-regions.json'
if not atlas_path.exists():
    atlas_path = Path('/Users/andreykuronskin/keys_champ/datasets/additional/all-regions/atlas-regions.json')
atlas = json.loads(atlas_path.read_text())
atlas_by_source_name = {ALIASES.get(row['name'], row['name']): row for row in atlas}
crosswalk = []
sources = []
for region, count in counts.items():
    atlas_row = atlas_by_source_name.get(region)
    registry_codes = sorted(codes[region])
    matched_funds = [funds_by_code[code] for code in registry_codes if code in funds_by_code]
    row = {
        'region_name': region,
        'atlas_region_name': atlas_row['name'] if atlas_row else None,
        'region_id_if_known': atlas_row['region_id'] if atlas_row else None,
        'atlas_match_method': 'explicit_name_alias' if atlas_row and atlas_row['name'] != region else 'exact_name' if atlas_row else 'outside_atlas',
        'registry_rows': count,
        'f032_uidmo_prefixes': registry_codes,
        'f001_funds': [{key: f[key] for key in ['tf_kod', 'tf_okato', 'name_tfp', 'www']} for f in matched_funds],
    }
    crosswalk.append(row)
    sources.append({
        'region_name': region, 'region_id_if_known': row['region_id_if_known'],
        'family': 'medical', 'url': SOURCE,
        'title': 'F032: реестр медицинских организаций, осуществляющих деятельность в сфере ОМС',
        'status': 'downloaded_national_registry', 'checked_at': CHECKED,
        'coverage': {'registry_rows': count, 'snapshot_date': '2026-03-03', 'programme_year': 2026},
        'download_url': 'https://www.kamtfoms.ru/files/packet_NCI/' + ARCHIVES['F032'],
        'local_path': 'data/additional/all-regions-medical/raw/' + ARCHIVES['F032'],
        'notes': 'Actual F032 records verified. SUBJ is programme/registry territory; JURADDRESS_ADDRESS is a legal address, not a verified care location. F001 homepage is a directory entry, not an individually checked regional registry.',
    })
    for fund in matched_funds:
        sources.append({
            'region_name': region, 'region_id_if_known': row['region_id_if_known'],
            'family': 'medical', 'url': fund['www'], 'title': fund['name_tfp'],
            'status': 'directory_only_not_individually_checked', 'checked_at': CHECKED,
            'coverage': 'F001 official TFOMS directory entry; site itself not fetched',
            'download_url': None, 'notes': 'Source: F001.xml packet dated 2025-10-15. Source values preserved; no homepage URL guesses or silent repairs.',
        })
with gzip.GzipFile(filename=str(DATA / 'f032-organizations.jsonl.gz'), mode='wb', mtime=0) as output:
    for row in medical:
        output.write((json.dumps(row, ensure_ascii=False) + '\n').encode())
save('region-crosswalk.json', crosswalk)
regional_links = json.loads((RAW / 'regional-download-links.json').read_text())
sources.extend([
    {'region_name': 'Московская область', 'region_id_if_known': '46000000', 'family': 'medical', 'url': 'https://www.mofoms.ru/dokumenty/spravochniki/reestry/', 'title': 'Реестр медицинских организаций 2026 от 14.10.2026', 'status': 'downloaded_regional_registry', 'checked_at': CHECKED, 'coverage': '2026 programme; official page states 2026-10-14', 'download_url': regional_links['moscow_oblast']['url'], 'local_path': 'data/additional/all-regions-medical/raw/moscow-oblast-mo-2026.xlsx.zip', 'notes': 'ZIP archive validated; detailed workbook row extraction not performed.'},
    {'region_name': 'Донецкая Народная Республика', 'region_id_if_known': None, 'family': 'medical', 'url': 'https://fomsdnr.ru/reestrmo', 'title': 'Реестр медицинских организаций на 2026 год', 'status': 'downloaded_regional_registry', 'checked_at': CHECKED, 'coverage': '2026 programme', 'download_url': 'https://s3.twcstorage.ru/163156c1-e321-4816-8c5d-2f008b269e54/REESTR_MO_na_2026.xlsx', 'local_path': 'data/additional/all-regions-medical/raw/dnr-mo-2026.xlsx', 'notes': 'Official page links this external storage; workbook container validated; detailed row extraction not performed.'},
    {'region_name': 'Владимирская область', 'region_id_if_known': '17000000', 'family': 'medical', 'url': 'https://www.tfoms33.ru/information-omsystem-participants/medical-organizations-institutions-registry', 'title': 'Реестр медицинских организаций (учреждений)', 'status': 'search_result_only_fetch_forbidden', 'checked_at': CHECKED, 'coverage': 'Search index mentions 2026 and 2027; direct page returned 403', 'download_url': None, 'notes': 'Regional file not acquired; region is covered by downloaded national F032.'},
    {'region_name': 'Республика Дагестан', 'region_id_if_known': '82000000', 'family': 'medical', 'url': 'https://fomsrd.ru/reestr-medicinskih-organizaciy', 'title': 'Реестр медицинских организаций', 'status': 'search_result_only_fetch_timeout', 'checked_at': CHECKED, 'coverage': 'Search index mentions 2026 XLSX; direct fetch timed out', 'download_url': None, 'notes': 'Regional file not acquired; region is covered by downloaded national F032.'},
    {'region_name': 'Российская Федерация', 'region_id_if_known': None, 'family': 'medical', 'url': 'https://www.ffoms.gov.ru/system-oms/territorial-funds/', 'title': 'Территориальные фонды ОМС России', 'status': 'fetch_failed', 'checked_at': CHECKED, 'coverage': 'Official national directory linked by Moscow oblast TFOMS; direct web fetch timed out', 'download_url': None, 'notes': 'FFOMS homepage curl returned a 77-byte block page. F001 directory and national registry acquired through official regional TFOMS mirror instead.'},
])
save('sources.json', sources)
save('f001-funds.json', [{'tf_kod': row['tf_kod'], 'tf_okato': row['tf_okato'], 'name_tfp': row['name_tfp'], 'www': row['www']} for row in funds])
schemas = {}
for name, root in roots.items():
    rows = root.findall('TFOMS' if name == 'F001' else 'zap')
    schemas[name] = {
        'rows': len(rows), 'packet_attributes': root.attrib,
        'header': {x.tag: x.text or '' for x in root.find('zglv')} if root.find('zglv') is not None else None,
        'fields_present': dict(collections.Counter(x.tag for row in rows for x in row)),
    }
save('schemas.json', schemas)
matched = [row for row in crosswalk if row['region_id_if_known']]
save('coverage.json', {
    'checked_at': CHECKED, 'atlas_total': len(atlas), 'atlas_covered': len(matched),
    'atlas_missing': [r for r in atlas if r['name'] not in [x['atlas_region_name'] for x in matched]],
    'f032_rows': len(medical), 'f032_subj_categories': len(counts),
    'outside_atlas_categories': [r['region_name'] for r in crosswalk if not r['region_id_if_known']],
    'alias_matches': [r for r in crosswalk if r['atlas_match_method'] == 'explicit_name_alias'],
    'f001_funds': len(funds), 'directory_homepages_individually_checked': 0,
    'code_system_warning': 'atlas region_id is the project region identifier; F001 tf_okato is source OKATO territory; tf_kod and F032 UIDMO prefixes are OMS fund codes. They are not interchangeable. Prefix join is explicitly observed in the downloaded F032 snapshot and is not a generalized parsing contract.',
})
manifest = []
for path in sorted(DATA.rglob('*')):
    if path.is_file():
        manifest.append({'path': str(path.relative_to(BASE)), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'downloaded_at': CHECKED})
save('manifest.json', manifest)
print(json.dumps({'atlas_covered': len(matched), 'atlas_total': len(atlas), 'F032': len(medical), 'F033': schemas['F033']['rows'], 'outside_atlas': len(counts) - len(matched)}, ensure_ascii=False))
