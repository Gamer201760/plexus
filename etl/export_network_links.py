import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import duckdb

from network_schedules import scheduled_links

SOURCE = 'https://tochno.st/datasets/intercity_connectivity'


def region_for(oktmo, prefixes):
    return prefixes.get(oktmo[:3], prefixes.get(oktmo[:2], ''))


def export(db, atlas_path, output, research):
    atlas = json.loads(atlas_path.read_text())
    prefixes = {
        row['id'][:3] if row['id'][2] != '0' else row['id'][:2]: row['id']
        for row in atlas['regions']
    }
    connection = duckdb.connect(str(db), read_only=True)
    city_rows = connection.execute('''
        select distinct city_from, oktmo_from, lat_from, lon_from from stg_intercity
    ''').fetchall()
    cities = {
        name: {'id': f'network:{oktmo}', 'name': name, 'lat': lat, 'lon': lon,
               'region': region_for(oktmo, prefixes)}
        for name, oktmo, lat, lon in city_rows
    }
    points = {row['id']: row for row in cities.values()}
    links = []
    model_rows = connection.execute('''
        select city_from, city_to, transport_type, distance_km, distance_hr
        from stg_intercity where transport_type in ('rail','air')
        and distance_hr is not null order by transport_type, city_from, city_to
    ''').fetchall()
    for origin, destination, mode, km, hours in model_rows:
        start, end = cities[origin], cities[destination]
        if not start['region']:
            continue
        key = f'{mode}:{start["id"]}:{end["id"]}'
        links.append({
            'id': 'model:' + hashlib.sha256(key.encode()).hexdigest()[:20],
            'region': start['region'], 'from_id': start['id'], 'to_id': end['id'],
            'from_name': origin, 'to_name': destination, 'mode': mode,
            'km': km, 'season': None, 'freq_per_week': None,
            'freq_note': f'Модельная направленная связь городов, не подтверждение прямого '
                         f'рейса или поезда. Модельное время: {hours:g} ч; календарь и частота '
                         'неизвестны. Линия соединяет центры городов и не показывает трассу. '
                         'Для авиа источник использует ближайшие к городам аэропорты.',
            'vehicle': None, 'confidence': 'low', 'source_url': SOURCE,
            'source_date': '2026-06-29', 'is_model': True,
        })
    schedules, skipped = scheduled_links(connection, cities, points, prefixes, research)
    connection.close()
    links.extend(schedules)
    ids = [row['id'] for row in links]
    assert len(ids) == len(set(ids))
    assert all(row['from_id'] in points and row['to_id'] in points for row in links)
    assert all(row['region'] for row in links)
    modes = Counter(row['mode'] for row in links)
    coverage = {
        mode: len({row['region'] for row in links if row['mode'] == mode})
        for mode in modes
    }
    sources = [
        {'id': 'network-model', 'title': 'Точно: модельные ж/д и авиасвязи',
         'period': '2026', 'url': SOURCE, 'rows': sum(row['is_model'] for row in links),
         'note': 'Направленные пары городов с модельным временем, не расписание прямых рейсов.'},
        {'id': 'network-uvt', 'title': 'ЮВТ Аэро: расписание', 'period': '2026–2027',
         'url': 'https://www.uvtaero.ru/raspisanie',
         'rows': sum(row['mode'] == 'air' for row in schedules),
         'note': 'Снимок 10.11.2026. Импортированы записи с действующим периодом без конфликтов.'},
        {'id': 'network-yakutia', 'title': 'Железные дороги Якутии: цепочки станций',
         'period': None, 'url': 'https://rw-y.ru/passengers/schedule/traffic/?special=Y',
         'rows': sum(row['mode'] == 'rail' for row in schedules),
         'note': 'Снимок 10.11.2026. Период действия и частота не указаны.'},
    ]
    document = {'points': list(points.values()), 'links': links, 'sources': sources}
    output.write_text(json.dumps(document, ensure_ascii=False, separators=(',', ':')) + '\n')
    report = {
        'snapshot_date': '2026-11-10', 'model_links': sum(row['is_model'] for row in links),
        'schedule_links': len(schedules), 'links_by_mode': dict(modes),
        'regions_by_mode': coverage, 'points': len(points), 'skipped': skipped,
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'source_database_table': 'stg_intercity', 'indices_recomputed': False,
    }
    output.with_suffix('.manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', type=Path, default=Path('data/casechamp.duckdb'))
    parser.add_argument('--atlas', type=Path, default=Path('frontend/atlas/public/atlas.json'))
    parser.add_argument('--output', type=Path, default=Path('frontend/atlas/public/network-links.json'))
    parser.add_argument('--research', type=Path, default=Path('work/regional-collection/rail-air-audit'))
    args = parser.parse_args()
    export(args.db, args.atlas, args.output, args.research)
