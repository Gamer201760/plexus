import collections
import csv
import io
import json
import math
import pathlib
import re
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent


def normal(value):
    return re.sub(r'\s+', ' ', value.replace('ё', 'е').replace('Ё', 'Е').strip())


def numeric(value):
    try:
        result = float(value.replace(',', '.'))
        return result if math.isfinite(result) and result >= 0 else None
    except ValueError:
        return None


def save_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    with (ROOT / 'datasets/intercity_connectivity/derived/cities.csv').open(encoding='utf-8') as stream:
        cities = list(csv.DictReader(stream))
    region_rows = {}
    leaves = collections.defaultdict(list)
    country_population = None
    all_levels = collections.Counter()
    invalid_population = collections.Counter()
    archive_path = next((ROOT / 'datasets/allsettlements/raw').glob('*.zip'))
    with zipfile.ZipFile(archive_path) as archive:
        member = next(name for name in archive.namelist() if name.endswith('.csv') and '__MACOSX' not in name)
        with archive.open(member) as binary:
            reader = csv.DictReader(io.TextIOWrapper(binary, encoding='utf-8-sig'), delimiter=';')
            for row in reader:
                level = row['object_level']
                all_levels[level] += 1
                population = numeric(row['population'])
                if population is None:
                    invalid_population[level] += 1
                if level == 'Страна':
                    country_population = population
                if level in ('Регион', 'Город федерального значения'):
                    key = normal(row['object_name'])
                    assert key not in region_rows
                    region_rows[key] = {'name': row['object_name'], 'population': population, 'oktmo': row['oktmo']}
                if level in ('Населенный пункт', 'Город федерального значения'):
                    leaves[row['oktmo']].append({key: row[key] for key in ('object_name', 'region', 'population', 'object_level')})
    joined = []
    population_by_region = collections.Counter()
    city_count = collections.Counter()
    for city in cities:
        candidates = leaves.get(city['oktmo'], [])
        match = candidates[0] if len(candidates) == 1 else None
        match_method = 'exact_oktmo' if match else 'unmatched'
        if match is None and normal(city['city']) == normal(city['region']):
            federal = region_rows.get(normal(city['city']))
            if federal:
                match = {'object_name': federal['name'], 'population': str(federal['population'])}
                match_method = 'federal_city_exact_name_and_level'
        population = numeric(city['population'])
        region = normal(city['region'])
        population_by_region[region] += population or 0
        city_count[region] += 1
        joined.append({
            'city': city['city'], 'region': city['region'], 'oktmo': city['oktmo'],
            'graph_population': population,
            'exact_oktmo_matches': len(candidates), 'match_method': match_method,
            'settlement_name': match['object_name'] if match else '',
            'census_population': numeric(match['population']) if match else None,
            'population_difference': population - numeric(match['population'])
            if match and population is not None and numeric(match['population']) is not None else None,
        })
    region_coverage = []
    for key, count in sorted(city_count.items()):
        target = region_rows.get(key)
        population = target['population'] if target else None
        region_coverage.append({
            'region': key, 'sample_cities': count,
            'sample_population': population_by_region[key],
            'region_census_population': population,
            'sample_population_share_pct': 100 * population_by_region[key] / population if population else None,
            'exact_region_name_match': target is not None,
        })
    summary = {
        'census_year': 2021,
        'graph_snapshot_year': 2026,
        'country_population_in_census_file': country_population,
        'graph_cities': len(cities),
        'graph_population': sum(numeric(city['population']) or 0 for city in cities),
        'exact_city_oktmo_matches': sum(row['exact_oktmo_matches'] == 1 for row in joined),
        'unmatched_cities': [row['city'] for row in joined if row['match_method'] == 'unmatched'],
        'federal_city_name_level_matches': sum(row['match_method'] == 'federal_city_exact_name_and_level' for row in joined),
        'city_population_mismatches': [row for row in joined if row['population_difference'] not in (None, 0)],
        'region_count': len(region_coverage),
        'unmatched_regions': [row['region'] for row in region_coverage if not row['exact_region_name_match']],
        'city_counts_distribution': dict(collections.Counter(city_count.values())),
        'levels': dict(all_levels),
        'invalid_or_coded_population_by_level': dict(invalid_population),
        'interpretation': 'Population share is representativeness of the selected city sample using the source census, not a transport connectivity score. Exact region labels and 177 exact city OKTMO matches were used; three federal cities matched by exact same city/region name and administrative level due 8/11-digit code representation. No fuzzy or prefix matches.',
    }
    summary['sample_country_population_share_pct'] = 100 * summary['graph_population'] / country_population
    shares = [row['sample_population_share_pct'] for row in region_coverage if row['sample_population_share_pct'] is not None]
    summary['minimum_region_share_pct'] = min(shares)
    summary['maximum_region_share_pct'] = max(shares)
    save_csv(OUT / 'city_census_join.csv', joined)
    save_csv(OUT / 'region_sample_coverage.csv', region_coverage)
    (OUT / 'representativeness.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key not in ('city_population_mismatches', 'levels')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
