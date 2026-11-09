import ast
import collections
import csv
import hashlib
import json
import math
import pathlib


OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def rows(path, delimiter=','):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter=delimiter))


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            value.update(chunk)
    return value.hexdigest()


def main():
    graph = json.loads((OUT / 'graph/results/summary.json').read_text())
    archive = next((ROOT / 'datasets/intercity_connectivity/raw').glob('*csv.zip'))
    assert digest(archive) == graph['input_archive_sha256']
    measures = rows(OUT / 'graph/results/accessibility.csv')
    assert len(measures) == 360
    assert len({(row['city'], row['mode']) for row in measures}) == 360
    for row in measures:
        counts = [int(row[f'destinations_within_{hours}h']) for hours in [6, 12, 24]]
        assert 0 <= counts[0] <= counts[1] <= counts[2] <= int(row['known_destinations']) <= 179
        for tau in [6, 12, 24]:
            assert 0 <= float(row[f'potential_tau{tau}_lower']) <= float(row[f'potential_tau{tau}_upper']) <= 1 + 1e-12
    scenario = rows(OUT / 'graph/results/hypothetical_scenario.csv')
    assert all(float(row['after']) >= float(row['before']) - 1e-12 for row in scenario)
    examples = [row for row in scenario if row['mode'] == 'road' and row['metric'] == 'destinations_within_6h']
    assert len(examples) == 2
    assert all(float(row['before']) == 32 and float(row['after']) == 33 for row in examples)
    population = json.loads((OUT / 'representativeness.json').read_text())
    assert population['exact_city_oktmo_matches'] == 177
    assert population['federal_city_name_level_matches'] == 3
    assert not population['unmatched_cities'] and not population['city_population_mismatches']
    assert not population['unmatched_regions']
    assert population['graph_population'] == 77396548
    municipal_path = ROOT / 'datasets/municipal_transport/derived/municipal_transport_indicators.csv'
    municipal = rows(municipal_path, ';')
    assert len(municipal) == 98220
    zeros = collections.Counter()
    for row in municipal:
        try:
            value = float(row['indicator_value'])
        except ValueError:
            continue
        if value == 0:
            zeros[row['indicator_code']] += 1
            assert row['year'] != '2024'
    assert zeros == {'Y48106005': 95, 'Y48155002': 2774}
    summary = json.loads((OUT / 'territories/summary.json').read_text())
    assert digest(municipal_path) == summary['input_municipal_sha256']
    paired = rows(OUT / 'territories/municipal-upper-paired-2024.csv')
    assert len(paired) == 1455 and len({row['region_name'] for row in paired}) == 84
    assert len({(row['region_name'], row['oktmo'], row['oktmo_stable']) for row in paired}) == 1455
    assert all(0 <= float(row[field]) <= 100 for row in paired for field in ['number_road', 'number_service'])
    assert len(rows(OUT / 'territories/municipal-balanced-changes-2023-2024.csv')) == 1328
    for row in rows(OUT / 'territories/regional-bus-intensities-2023.csv'):
        population_thousands = float(row['population_thousand'])
        turnover = float(row['bus_passenger_km_million'])
        passengers = float(row['bus_passengers_million'])
        assert population_thousands > 0 and passengers > 0
        assert math.isclose(float(row['bus_passenger_km_per_resident']), 1000 * turnover / population_thousands)
        assert math.isclose(float(row['mean_bus_trip_km']), turnover / passengers)
    assert len(rows(OUT / 'territories/regional-bus-intensities-2023.csv')) == 85
    national = rows(OUT / 'ports/national_turnover_capacity_2000_2024.csv')
    assert len(national) == 25
    assert max(abs(float(row['utilization_computed_pct']) - float(row['utilization_stated_pct'])) for row in national) < .05
    airports = json.loads((OUT / 'air-distance/results.json').read_text())
    points = airports['strict_settlements']
    assert points['settlements'] == 155747
    shares = [points[f'population_share_within_{radius}km'] for radius in [50, 100, 200]]
    assert 0 <= shares[0] <= shares[1] <= shares[2] <= 1
    regional = rows(OUT / 'air-distance/distance_by_native_region.csv')
    assert len(regional) == 85
    assert sum(float(row['settlements'] or 0) for row in regional) == 155747
    assert math.isclose(sum(float(row['population_with_valid_coordinates_and_population'] or 0) for row in regional), points['population_with_valid_coordinates_and_population'])
    source = json.loads((OUT / 'territories/municipal-methodology-source.json').read_text())
    assert digest(OUT / 'territories/description_bdmo_112_v20260928.pdf') == source['sha256']
    for path in OUT.rglob('*.py'):
        ast.parse(path.read_text())
    print('Validated source hashes, graph measures/scenario, population joins, municipal cohorts/zeros, bus units, port ratios, airport aggregates and Python syntax.')


if __name__ == '__main__':
    main()
