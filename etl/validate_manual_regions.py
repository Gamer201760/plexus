import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
LINK_FIELDS = 'from_id,to_id,from_name,to_name,mode,vehicle,km,freq_per_week,freq_note,season,months,road_ref,crossing_lat,crossing_lon,confidence,source_url,source_date'.split(',')
REMOTE_FIELDS = 'point_id,name,status,all_season_road,note,source_url'.split(',')
MODES = {'air', 'winter_road', 'river', 'ferry', 'pontoon_bridge', 'ice_crossing'}


def validate(code, root):
    errors = []
    with (root / f'data_manual/regions_input/{code}.csv').open(newline='', encoding='utf-8-sig') as stream:
        names = {row['point_id']: row['name'] for row in csv.DictReader(stream)}
    ids = set(names)
    datasets = []
    for suffix, fields in [('.csv', LINK_FIELDS), ('_remote.csv', REMOTE_FIELDS)]:
        path = root / f'data_manual/regions/{code}{suffix}'
        if not path.exists():
            errors.append(f'missing {path.name}')
            datasets.append([])
            continue
        with path.open(newline='', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != fields:
                errors.append(f'{path.name}: wrong header {reader.fieldnames}')
            rows = list(reader)
        datasets.append(rows)
        for index, row in enumerate(rows, 2):
            prefix = f'{path.name}:{index}'
            if None in row or any(value is None for value in row.values()):
                errors.append(f'{prefix}: row width')
            for field in ('from_id', 'to_id') if suffix == '.csv' else ('point_id',):
                value = row.get(field) or ''
                if value not in ids and not (value.startswith('ext:') and len(value) > 4):
                    errors.append(f'{prefix}: invalid {field}={value}')
                name_field = {'from_id': 'from_name', 'to_id': 'to_name', 'point_id': 'name'}[field]
                if value in names and row.get(name_field) != names[value]:
                    errors.append(f'{prefix}: name differs from input for {field}')
            if not re.match(r'https?://\S+$', row.get('source_url') or ''):
                errors.append(f'{prefix}: missing/invalid URL')
            if suffix == '.csv':
                if row.get('mode') not in MODES:
                    errors.append(f'{prefix}: invalid mode')
                if row.get('season') not in {'all', 'summer', 'winter'} and not (row.get('season') == '' and row.get('confidence') == 'low' and row.get('freq_note')):
                    errors.append(f'{prefix}: invalid season')
                if row.get('confidence') not in {'high', 'medium', 'low'}:
                    errors.append(f'{prefix}: invalid confidence')
                if row.get('source_date') and not re.fullmatch(r'\d{4}(-\d{2})?', row['source_date']):
                    errors.append(f'{prefix}: invalid source_date')
                for field in ['km', 'freq_per_week', 'crossing_lat', 'crossing_lon']:
                    value = row.get(field)
                    if value:
                        try:
                            number = float(value)
                            if not math.isfinite(number):
                                errors.append(f'{prefix}: nonfinite {field}')
                            if field == 'crossing_lat' and not -90 <= number <= 90:
                                errors.append(f'{prefix}: invalid latitude')
                            if field == 'crossing_lon' and not -180 <= number <= 180:
                                errors.append(f'{prefix}: invalid longitude')
                            if field in {'km', 'freq_per_week'} and number < 0:
                                errors.append(f'{prefix}: negative {field}')
                        except ValueError:
                            errors.append(f'{prefix}: nonnumeric {field}')
            elif row.get('all_season_road') not in {'yes', 'no', 'unknown'}:
                errors.append(f'{prefix}: invalid road status')
    md = root / f'data_manual/regions/{code}.md'
    if not md.exists() or not md.read_text().strip():
        errors.append('missing/empty regional note')
    links, remote = datasets
    return {'code': code, 'links': len(links), 'remote': len(remote), 'modes': dict(Counter(row.get('mode') for row in links)), 'frequencies': sum(bool(row.get('freq_per_week')) for row in links), 'errors': errors}


if __name__ == '__main__':
    codes = sys.argv[1:] or [item['code'] for item in json.loads((BASE / 'prompts/regions_todo.json').read_text())[:70]]
    results = [validate(code, BASE) for code in codes]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    sys.exit(any(result['errors'] for result in results))
