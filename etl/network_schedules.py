import hashlib
import json

ALIASES = {'Нижнекамск (Бегишево)': 'Нижнекамск'}
DAY_NAMES = {1: 'пн', 2: 'вт', 3: 'ср', 4: 'чт', 5: 'пт', 6: 'сб', 7: 'вс'}


def resolve(name, connection, cities, points, prefixes):
    name = ALIASES.get(name, name)
    if name in cities:
        return cities[name]
    matches = connection.execute('''
        select oktmo, latitude, longitude from stg_settlements
        where object_level = 'Населенный пункт' and latitude is not null
        and longitude is not null and settlement in (?, ?, ?, ?)
    ''', [name, 'г. '+name, 'пгт '+name, 'село '+name]).fetchall()
    if len(matches) != 1:
        return None
    oktmo, lat, lon = matches[0]
    region = prefixes.get(oktmo[:3], prefixes.get(oktmo[:2], ''))
    point = {'id': f'network:{oktmo}', 'name': name, 'lat': lat, 'lon': lon, 'region': region}
    cities[name] = point
    points[point['id']] = point
    return point


def record(key, start, end, mode, source_url, note, frequency, season, source_date):
    return {
        'id': 'schedule:' + hashlib.sha256(key.encode()).hexdigest()[:20],
        'region': start['region'], 'from_id': start['id'], 'to_id': end['id'],
        'from_name': start['name'], 'to_name': end['name'], 'mode': mode,
        'km': None, 'season': season, 'freq_per_week': frequency,
        'freq_note': note + ' Координаты центров населённых пунктов; линия схематическая, '
                           'не трасса и не точное положение аэропортов или станций.',
        'vehicle': None, 'confidence': 'medium', 'source_url': source_url,
        'source_date': source_date, 'is_model': False,
    }


def scheduled_links(connection, cities, points, prefixes, research):
    links, skipped = [], []
    uvt = json.loads((research/'uvt-routes.json').read_text())
    for row in uvt['routes']:
        if not row['eligible_for_import'] or not row['period_active_on_reference_date']:
            skipped.append({'source': 'uvt', 'id': row['id'], 'reason': 'conflict_or_period'})
            continue
        start = resolve(row['origin'], connection, cities, points, prefixes)
        end = resolve(row['destination'], connection, cities, points, prefixes)
        if not start or not end or not start['region']:
            skipped.append({'source': 'uvt', 'id': row['id'], 'reason': 'outside_atlas_or_unresolved_point'})
            continue
        days = ', '.join(DAY_NAMES[day] for day in row['days'])
        note = (f'ЮВТ Аэро, {row["flight"]}. Период {row["period_start"]} — {row["period_end"]}; '
                f'дни: {days}. Отправление {row["departure_local"]}, '
                f'прибытие {row["arrival_local"]}; время местное для каждого аэропорта. '
                'Снимок расписания на 10.11.2026, выполнение конкретного рейса не проверено.')
        link = record('uvt:'+row['id'], start, end, 'air', row['source_url'], note,
                      len(row['days']), None, uvt['retrieved_at'][:10])
        link['vehicle'] = row['aircraft']
        links.append(link)
    yakutia = json.loads((research/'yakutia-routes.json').read_text())
    for row in yakutia['chains']:
        start = resolve(row['origin'], connection, cities, points, prefixes)
        end = resolve(row['destination'], connection, cities, points, prefixes)
        if not start or not end or not start['region']:
            skipped.append({'source': 'yakutia', 'id': row['route_group_id'], 'reason': 'unresolved_point'})
            continue
        stops = ' → '.join(stop['name'] for stop in row['stops'])
        note = ('Опубликованная цепочка станций ЖДЯ. Период действия, дни движения, '
                'номер поезда и часовой пояс источником не указаны. Частота неизвестна. '
                'Промежуточные станции: '+stops+'.')
        links.append(record(row['route_group_id'], start, end, 'rail', yakutia['source_url'],
                            note, None, None, yakutia['retrieved_at'][:10]))
    return links, skipped
