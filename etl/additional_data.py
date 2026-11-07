"""Join the eight acquired data families without changing the transport model.

Run: .venv/bin/python etl/additional_data.py
Output: data/additional.duckdb, frontend/atlas/public/additional.json and
public/additional/regions/<OKTMO>.json. No company identifiers are exported.
The database is built transactionally in a temporary file before replacement.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
RADIUS_KM = 5.0
EARTH_KM = 6371.0088
# Explicit concordance: RFSD labels -> existing atlas geography. Federal cities
# and source territories outside the atlas stay outside its 82-region totals.
REGION_MAP = dict(zip(
    'altai terr.|krasnodar|krasnoyarsk|primorsky terr.|stavropol|khabarovsk|amur|arkhangelsk|nenets ao|astrakhan|belgorod|bryansk|vladimir|volgograd|vologda|voronezh|nizhni novgorod|ivanovo|irkutsk|ingushetia|kaliningrad|tver|kaluga|kamchatka|kemerovo|kirov|kostroma|crimea|samara|kurgan|kursk|leningrad|lipetzk|magadan|moscow reg.|murmansk|novgorod|novosibirsk|omsk|orenburg|oryol|penza|perm|pskov|rostov|ryazan|saratov|sakhalin|sverdlovsk|smolensk|tambov|tomsk|tula|tyumen|khanty-mansijsk|yamal-nenets ao|ulyanovsk|chelyabinsk|zabaikalsk terr.|chukotka|yaroslavl|adygeya|bashkortostan|buryatia|dagestan|kabardino-balkaria|altai rep.|kalmykia|karelia|komi|marij el|mordovia|north ossetia|karachaevo-chercessia|tatarstan|tuva|udmurtia|khakasia|chechnya|chuvashia|yakutia|jewish ao'.split('|'),
    '01000000 03000000 04000000 05000000 07000000 08000000 10000000 11000000 11800000 12000000 14000000 15000000 17000000 18000000 19000000 20000000 22000000 24000000 25000000 26000000 27000000 28000000 29000000 30000000 32000000 33000000 34000000 35000000 36000000 37000000 38000000 41000000 42000000 44000000 46000000 47000000 49000000 50000000 52000000 53000000 54000000 56000000 57000000 58000000 60000000 61000000 63000000 64000000 65000000 66000000 68000000 69000000 70000000 71000000 71800000 71900000 73000000 75000000 76000000 77000000 78000000 79000000 80000000 81000000 82000000 83000000 84000000 85000000 86000000 87000000 88000000 89000000 90000000 91000000 92000000 93000000 94000000 95000000 96000000 97000000 98000000 99000000'.split(),
    strict=True,
))


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def sql_path(path: Path) -> str:
    return "'" + str(path.resolve()).replace("'", "''") + "'"


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'), default=str) + '\n')
    tmp.replace(path)


def records(con, query: str) -> list[dict]:
    result = con.execute(query)
    columns = [d[0] for d in result.description]
    return [dict(zip(columns, [float(v) if isinstance(v, Decimal) else v for v in row])) for row in result.fetchall()]


def register_rows(con, name: str, rows: list[dict]):
    if not rows:
        raise ValueError(f'{name}: empty input')
    con.register('_input', pa.Table.from_pylist(rows))
    con.execute(f'create table {name} as select * from _input')
    con.unregister('_input')


def xyz(lat, lon):
    lat, lon = np.radians(lat), np.radians(lon)
    return np.column_stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])


def normalize_name(value: str) -> str:
    value = value.lower().replace('ё', 'е').strip()
    value = re.sub(r'^(?:г\.|п\.|д\.|с\.|город\s|поселок\s|деревня\s|село\s|пгт\s)\s*', '', value)
    return re.sub(r'\s+', ' ', value).strip()


def route_matches(route: str, district: str, settlements: list[dict]):
    """Exact normalized stops inside the named district; never guess duplicates."""
    result, unresolved = [], []
    district_key = district.split()[0].lower()
    for stop in re.split(r'\s+[—–-]\s+', route):
        name = normalize_name(stop)
        candidates = [p for p in settlements if normalize_name(p['name']) == name
                      and district_key in p['mun_upper'].lower()]
        if len(candidates) == 1:
            result.append(candidates[0]['point_id'])
        else:
            unresolved.append(stop)
    return list(dict.fromkeys(result)), unresolved


def prepare_dimensions(con, root: Path, atlas):
    regions = [{k: r[k] for k in ('id', 'name', 'population')} for r in atlas['regions']]
    register_rows(con, 'dim_region', regions)
    register_rows(con, 'dim_rfsd_region', [{'source_region': s, 'region_id': r} for s, r in REGION_MAP.items()])
    settlements = []
    for p in sorted((root / 'data_manual/regions_input').glob('*.csv')):
        for r in read_rows(p):
            settlements.append(dict(point_id=r['point_id'], name=r['name'], region_id=p.stem,
                                    mun_upper=r['mun_upper'], population=int(float(r['population'] or 0)),
                                    lat=float(r['lat']), lon=float(r['lon'])))
    if len({p['point_id'] for p in settlements}) != len(settlements):
        raise ValueError('Duplicate settlement IDs')
    register_rows(con, 'dim_settlement', settlements)
    return settlements


def prepare_economy(con, base: Path):
    source = base / 'rfsd/raw/RFSD/year=2025/part-0.parquet'
    fns = base / 'fns-revexp/derived/income_expense_2025.parquet'
    con.execute(f"""create table stg_rfsd as
      select row_number() over ()::bigint as firm_id, inn, r.region as source_region,
             d.region_id, okved_section, filed, eligible, imputed, outlier,
             geocoding_quality, lat, lon, creation_date, dissolution_date,
             case when isfinite(line_2110) then line_2110 * 1000 end as revenue_rub,
             coalesce(filed=1 and eligible=1 and imputed=0 and outlier=0
               and geocoding_quality in ('house','street')
               and isfinite(lat) and isfinite(lon) and lat between -90 and 90 and lon between -180 and 180, false) as strict
      from read_parquet({sql_path(source)}) r left join dim_rfsd_region d on r.region=d.source_region""")
    con.execute(f'create table stg_fns as select * from read_parquet({sql_path(fns)})')
    for table in ('stg_rfsd', 'stg_fns'):
        n, unique = con.execute(f'select count(inn), count(distinct inn) from {table}').fetchone()
        if n != unique:
            raise ValueError(f'{table}: duplicate nonnull INN would multiply the join')
    con.execute('''create table fact_company as select r.*, f.inn is not null as fns_matched,
                   f.income_rub, f.expense_rub from stg_rfsd r left join stg_fns f using (inn)''')
    # Geographical association is a transparent proxy, not a plant location.
    con.execute('create table company_settlement (firm_id bigint, point_id varchar, distance_km double)')
    for (region_id,) in con.execute('select distinct region_id from dim_settlement').fetchall():
        points = con.execute('select point_id, lat, lon from dim_settlement where region_id=? order by point_id', [region_id]).fetchall()
        firms = con.execute('select firm_id, lat, lon from fact_company where region_id=? and strict order by firm_id', [region_id]).fetchnumpy()
        if not len(firms['firm_id']):
            continue
        tree = cKDTree(xyz([p[1] for p in points], [p[2] for p in points]))
        distance, nearest = tree.query(xyz(firms['lat'], firms['lon']))
        km = 2 * EARTH_KM * np.arcsin(np.clip(distance / 2, 0, 1))
        keep = km <= RADIUS_KM
        mapped = pa.table({'firm_id': firms['firm_id'][keep],
                           'point_id': np.array([p[0] for p in points])[nearest[keep]], 'distance_km': km[keep]})
        con.register('_mapped', mapped)
        con.execute('insert into company_settlement select * from _mapped')
        con.unregister('_mapped')
    # Both filters are exported. Do not silently replace missing revenue with income.
    con.execute('''create table mart_region_economy as
      select d.id as region_id, d.name, d.population,
        count(f.firm_id) as company_rows, count(f.revenue_rub) as revenue_rows,
        count(f.firm_id) filter (f.strict) as strict_rows,
        count(f.revenue_rub) filter (f.strict) as strict_revenue_rows,
        sum(f.revenue_rub) filter (f.strict) as strict_revenue_rub,
        count(f.firm_id) filter (f.strict and f.revenue_rub<0) as negative_revenue_rows,
        count(f.firm_id) filter (f.fns_matched) as fns_matched_rows,
        sum(f.income_rub) filter (f.strict) as strict_fns_income_rub,
        count(f.firm_id) filter (f.strict and f.fns_matched) as strict_fns_rows
      from dim_region d left join fact_company f on f.region_id=d.id group by all''')
    con.execute('''create table mart_region_sector as
      select region_id, coalesce(okved_section, 'unknown') as sector,
        count(*) as company_rows, count(revenue_rub) as revenue_rows,
        count(*) filter (strict) as strict_rows,
        count(revenue_rub) filter (strict) as strict_revenue_rows,
        sum(revenue_rub) filter (strict) as strict_revenue_rub
      from fact_company where region_id is not null group by all''')
    con.execute('''create table mart_np_economy as
      select p.point_id, p.region_id, p.name, p.population, p.lat, p.lon,
        count(f.firm_id) as company_rows, count(f.revenue_rub) as revenue_rows,
        sum(f.revenue_rub) as revenue_rub,
        sum(f.revenue_rub) filter (f.revenue_rub>=0) as market_weight_rub,
        count(f.firm_id) filter (f.fns_matched) as fns_matched_rows,
        max(m.distance_km) as max_assignment_km
      from dim_settlement p left join company_settlement m using (point_id)
      left join fact_company f using (firm_id) group by all''')
    return records(con, '''select count(*) as source_company_rows,
      count(*) filter (region_id is not null) as atlas_company_rows,
      count(*) filter (region_id is null) as outside_atlas_rows,
      count(revenue_rub) as revenue_rows,
      count(*) filter (strict) as strict_rows,
      count(revenue_rub) filter (strict) as strict_revenue_rows,
      count(*) filter (fns_matched) as fns_matched_rows,
      (select count(*) from stg_fns) as fns_source_rows,
      (select count(*) from company_settlement) as settlement_assigned_rows
      from fact_company''')[0]


def prepare_lights(con, base: Path):
    con.execute(f'''create table stg_lights as
      select point_id, year::int as year, raw_value::int as raw_value, status
      from read_csv({sql_path(base / 'nighttime-lights/settlements_opengeohub_*.csv')}, header=true, all_varchar=true)''')
    n, unique = con.execute('select count(*), count(distinct (point_id,year)) from stg_lights').fetchone()
    if n != unique:
        raise ValueError('Duplicate settlement/year in nighttime lights')
    con.execute('''create table mart_region_lights as
      select p.region_id, l.year, count(*) as points, count(*) filter (l.status='valid') as valid_points,
        avg(l.raw_value) filter (l.status='valid') as mean_raw,
        median(l.raw_value) filter (l.status='valid') as median_raw,
        count(*) filter (l.status='valid' and l.raw_value=0) as zero_points
      from dim_settlement p join stg_lights l using(point_id) group by all''')


def prepare_transport(con, base: Path, root: Path, settlements):
    tables = {
        'stg_ugra_snapshots': 'seasonal-ugra/xlsx-route-status.csv',
        'stg_ugra_crossings': 'seasonal-ugra/xlsx-crossings.csv',
        'stg_ugra_district_closures': 'seasonal-ugra/district-closure-history.csv',
        'stg_closure_events': 'seasonal-closures/events.csv',
        'stg_kap_schedule': 'transport-operations/kap_winter_2026_2027_segments.csv',
        'stg_river_schedule': 'transport-operations/hmrn_subsidy_2024_schedule.csv',
        'stg_northern_infrastructure': 'northern-delivery/infrastructure-286r-2025.csv',
        'stg_northern_territories': 'northern-delivery/territories-consolidated-2026.csv',
        'stg_northern_volumes': 'northern-delivery/regional-supply-volumes.csv',
        'stg_northern_dashboard': 'northern-delivery/dashboard-plan-actual-2026.csv',
        'stg_traffic_belovo': 'traffic-surveys/belovo-observed-vehicle-counts.csv',
        'stg_traffic_nefteyugansk': 'traffic-surveys/nefteyugansk-observed-parameters.csv',
        'stg_traffic_serov': 'traffic-surveys/serov-observed-parameters.csv',
    }
    for name, path in tables.items():
        con.execute(f'create table {name} as select * from read_csv({sql_path(base/path)}, header=true, all_varchar=true)')
    metadata = json.loads((root / 'datasets/additional/seasonal-ugra/metadata.json').read_text())
    urls = {f['filename']: f['url'] for f in metadata['files']}
    ugra = [s for s in settlements if s['region_id'] == '71800000']
    seasons = []
    for row in read_rows(base / 'seasonal-ugra/verified-route-seasons.csv'):
        stops, unresolved = route_matches(row['route'], row['district'], ugra)
        opening = date.fromisoformat(row['opening_date']) if row['opening_date'] else None
        closing = date.fromisoformat(row['closure_date']) if row['closure_date'] else None
        if closing and opening and closing < opening:
            raise ValueError('Negative season duration')
        seasons.append({**row, 'route_id': hashlib.sha256(row['route'].encode()).hexdigest()[:12],
                        'region_id': '71800000', 'season_end_year': int(row['season_end_year']),
                        'elapsed_days': (closing-opening).days if opening and closing else None,
                        'weight_limit_tonnes': float(row['weight_limit_tonnes']) if row['weight_limit_tonnes'] else None,
                        'stop_ids': stops, 'unresolved_stops': unresolved,
                        'source_url': urls.get(row['source_file']), 'pdf_page': int(row['pdf_page'])})
    register_rows(con, 'fact_route_season', seasons)
    return seasons


def check(con, economy):
    count = lambda q: con.execute(q).fetchone()[0]
    assert count('select count(*) from fact_company') == economy['source_company_rows']
    assert count('select count(*) from company_settlement') == count('select count(distinct firm_id) from company_settlement')
    assert count(f'select count(*) from company_settlement where distance_km>{RADIUS_KM}') == 0
    assert count('select sum(company_rows) from mart_region_economy') == economy['atlas_company_rows']
    assert count('select sum(company_rows) from mart_np_economy') == economy['settlement_assigned_rows']
    assert count('select count(*) from mart_np_economy') == count('select count(*) from dim_settlement')
    assert count('select count(*) from stg_lights') == 2 * count('select count(*) from dim_settlement')
    assert count('select count(*) from stg_lights l anti join dim_settlement p using(point_id)') == 0
    return {'join_preserves_company_rows': True, 'unique_company_assignment': True,
            'regional_and_settlement_counts_reconcile': True, 'lights_cover_both_years': True}


def optional_access(con, transport_db: Path):
    """Only calculate with actual saved travel times. Never fabricate a graph."""
    if not transport_db.exists():
        return {'status': 'missing_transport_graph', 'rows': 0}
    con.execute(f'attach {sql_path(transport_db)} as transport (read_only)')
    tables = {r[0] for r in con.execute("select table_name from information_schema.tables where table_catalog='transport'").fetchall()}
    if not {'np_city_times', 'market_cities', 'np_access'} <= tables:
        return {'status': 'missing_travel_time_tables', 'rows': 0}
    con.execute('''create table economic_market_targets as
      select c.city, c.oktmo as point_id, p.market_weight_rub, p.company_rows, p.revenue_rows
      from transport.market_cities c left join mart_np_economy p on p.point_id=c.oktmo''')
    con.execute('''create table idx_economic_np as
      select t.season, t.point_id,
        sum(m.market_weight_rub * exp(-ln(2)/2*t.best_h)) as economic_access_rub,
        count(*) filter (m.market_weight_rub is not null) as markets_with_weight
      from transport.np_city_times t join economic_market_targets m using(city) group by all''')
    return {'status': 'calculated_for_available_market_targets', 'rows': con.execute('select count(*) from idx_economic_np').fetchone()[0],
            'target_coverage': records(con, 'select count(*) as targets, count(market_weight_rub) as weighted_targets from economic_market_targets')[0],
            'note': 'Only observed nonnegative revenue near mapped market settlements. Missing economic weights are not zero activity.'}


def export(con, root, output, economy, seasons, checks, access):
    regions = records(con, 'select * from mart_region_economy order by region_id')
    lights = records(con, 'select * from mart_region_lights order by region_id, year')
    sectors = records(con, 'select * from mart_region_sector order by region_id, strict_revenue_rub desc nulls last')
    for r in regions:
        r['lights'] = [l for l in lights if l['region_id'] == r['region_id']]
        r['sectors'] = [s for s in sectors if s['region_id'] == r['region_id']]
    for r in regions:
        # Full settlement layer is split per region; do not ship 3m company rows.
        rows = records(con, f"""select p.*, a.raw_value as light_2023, b.raw_value as light_2024
          from mart_np_economy p
          left join stg_lights a on a.point_id=p.point_id and a.year=2023 and a.status='valid'
          left join stg_lights b on b.point_id=p.point_id and b.year=2024 and b.status='valid'
          where p.region_id='{r['region_id']}' order by p.company_rows desc, p.point_id""")
        write_json(output / 'additional/regions' / f"{r['region_id']}.json", rows)
    sources = [
        ('rfsd', 'RFSD · финансы компаний', 'fact_company', '2025', 'https://github.com/irlcode/RFSD', 'Адреса регистрации. Выручка в рублях после перевода из тысяч; пропуски сохранены.'),
        ('fns-revexp', 'ФНС · доходы и расходы', 'stg_fns', '2025', 'https://www.nalog.gov.ru/rn54/opendata/7707329152-revexp/', 'Соединение по ИНН. Доход не подменяет выручку; источники не суммируются.'),
        ('nighttime-lights', 'Освещённость · OpenGeoHub / VIIRS', 'stg_lights', '2023–2024', 'https://zenodo.org/records/17294744', 'Один пиксель в точке поселения, исходные целые значения. Ноль не означает отсутствие деятельности.'),
        ('seasonal-ugra', 'Югра · зимники и переправы', 'fact_route_season', '2024–2026', 'https://www.ugrador.ru/', 'Проверенные записи сезонов; между датами возможны неучтённые перерывы.'),
        ('seasonal-closures', 'МЧС · состояния объектов', 'stg_closure_events', '2025–2026', 'https://mchs.gov.ru/', 'Дата публикации не заменяет дату события. Конфликтные записи сохраняются отдельно.'),
        ('transport-operations', 'Расписания перевозчиков', 'stg_kap_schedule', '2026–2027', 'https://aokap.ru/uslugi/regulyarnye-perevozki/raspisanie-zima/', '72 строки сегментов и периодов, не число уникальных линий. Выполнение рейсов не измеряется.'),
        ('traffic-surveys', 'Натурные обследования', 'stg_traffic_belovo', '2018–2019', None, 'Белово, Серов, Нефтеюганск. Разные интервалы и единицы; это не текущий поток всей РФ.'),
        ('northern-delivery', 'Северный завоз', 'stg_northern_infrastructure', '2025–2026', 'https://szavoz.gov.ru/', 'Группы инфраструктуры и частичные объёмы. Пересекающиеся категории не складываются.'),
    ]
    catalog = [dict(id=i, title=t, table=table, period=period, url=url, note=note,
                    rows=con.execute(f'select count(*) from {table}').fetchone()[0]) for i,t,table,period,url,note in sources]
    # Raw excerpts with original units and provenance; no inferred geographic joins.
    context = {name: records(con, f'select * from {table}') for name, table in {
        'closure_events':'stg_closure_events', 'kap_schedule':'stg_kap_schedule',
        'river_schedule':'stg_river_schedule', 'northern_infrastructure':'stg_northern_infrastructure',
        'northern_volumes':'stg_northern_volumes', 'northern_territories':'stg_northern_territories',
        'traffic_nefteyugansk':'stg_traffic_nefteyugansk', 'traffic_serov':'stg_traffic_serov',
        'traffic_belovo':'stg_traffic_belovo', 'northern_dashboard':'stg_northern_dashboard',
        'ugra_snapshots':'stg_ugra_snapshots', 'ugra_crossings':'stg_ugra_crossings',
        'ugra_district_closures':'stg_ugra_district_closures',
    }.items()}
    source_counts = records(con, "select source_region, count(*) as rows from fact_company where region_id is null group by 1 order by 2 desc")
    data = dict(schema_version=1, generated_at=datetime.now(timezone.utc).isoformat(), financial_year=2025,
                geography='82 regions of the existing atlas; source territories outside it reported separately',
                assignment_radius_km=RADIUS_KM, strict_filter='filed=1, eligible=1, imputed=0, outlier=0, house/street, valid coordinates',
                summary=economy, regions=regions, route_seasons=seasons, sources=catalog,
                context=context, outside_atlas=source_counts, checks=checks, economic_access=access)
    write_json(output / 'additional.json', data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / 'frontend/atlas/public'
    base = root / 'data/additional'
    destination = root / 'data/additional.duckdb'
    temporary = destination.with_suffix('.building.duckdb')
    if temporary.exists():
        temporary.unlink()
    con = duckdb.connect(str(temporary))
    con.execute("set memory_limit='3GB'")
    con.execute('set threads=4')
    try:
        atlas = json.loads((root/'frontend/atlas/public/atlas.json').read_text())
        settlements = prepare_dimensions(con, root, atlas)
        print('Dimensions loaded; joining company data...', flush=True)
        economy = prepare_economy(con, base)
        print('Economy:', economy, flush=True)
        prepare_lights(con, base)
        seasons = prepare_transport(con, base, root, settlements)
        checks = check(con, economy)
        access = optional_access(con, root/'data/casechamp.duckdb')
        data = export(con, root, output, economy, seasons, checks, access)
        con.execute('checkpoint')
        con.close()
        temporary.replace(destination)
        write_json(root/'data/additional-integration.json', {k:data[k] for k in ['generated_at','summary','checks','economic_access','outside_atlas']})
        print(f'Written {destination}; {len(data["regions"])} regions; {len(seasons)} season records.', flush=True)
    finally:
        con.close()


if __name__ == '__main__':
    main()
