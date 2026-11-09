import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
args = parser.parse_args()
root = args.repo / 'datasets'
out = Path(__file__).parent
radius_km = 6371.0088
archive = next((root / 'allsettlements/raw').glob('*.zip'))
fields = ['object_level', 'object_name', 'oktmo', 'region', 'population', 'latitude', 'longitude']
with ZipFile(archive) as zipped:
    entry = next(name for name in zipped.namelist() if name.endswith('.csv') and not name.startswith('__MACOSX'))
    with zipped.open(entry) as stream:
        source = pd.read_csv(stream, sep=';', usecols=fields, keep_default_na=False, dtype={'oktmo': str})

settlements = source[source.object_level == 'Населенный пункт'].copy()
federal = source[source.object_level == 'Город федерального значения'].copy()
regional_catalog = source[source.object_level.isin(['Регион', 'Город федерального значения'])][['region', 'population', 'object_level']].copy()
assert len(settlements) == 155747
assert len(federal) == 3
assert len(regional_catalog) == regional_catalog.region.nunique() == 85

airport_path = root / 'ourairports-russia/derived/airports_ru.csv'
airports = pd.read_csv(airport_path, keep_default_na=False)
airports = airports[(airports.scheduled_service == 'yes') & (airports.type != 'closed')].copy().reset_index(drop=True)
for field in ['latitude_deg', 'longitude_deg']:
    airports[field] = pd.to_numeric(airports[field], errors='coerce')
assert airports.latitude_deg.between(-90, 90).all()
assert airports.longitude_deg.between(-180, 180).all()
assert len(airports) == 157
airport_lat = np.radians(airports.latitude_deg.to_numpy())
airport_lon = np.radians(airports.longitude_deg.to_numpy())

def nearest(latitude, longitude):
    distances = np.empty(len(latitude), dtype=float)
    indices = np.empty(len(latitude), dtype=np.int64)
    for start in range(0, len(latitude), 4096):
        stop = min(start + 4096, len(latitude))
        lat = np.radians(np.asarray(latitude[start:stop], dtype=float))[:, None]
        lon = np.radians(np.asarray(longitude[start:stop], dtype=float))[:, None]
        h = np.sin((lat - airport_lat) / 2) ** 2 + np.cos(lat) * np.cos(airport_lat) * np.sin((lon - airport_lon) / 2) ** 2
        matrix = 2 * radius_km * np.arcsin(np.sqrt(np.clip(h, 0, 1)))
        local = np.argmin(matrix, axis=1)
        indices[start:stop] = local
        distances[start:stop] = matrix[np.arange(stop - start), local]
    return distances, indices

def enrich(frame):
    frame = frame.copy()
    for field in ['latitude', 'longitude', 'population']:
        frame[field + '_numeric'] = pd.to_numeric(frame[field], errors='coerce')
    frame['valid_coordinates'] = frame.latitude_numeric.between(-90, 90) & frame.longitude_numeric.between(-180, 180)
    frame['valid_population'] = frame.population_numeric.notna() & (frame.population_numeric >= 0)
    good = frame.valid_coordinates
    distance, index = nearest(frame.loc[good, 'latitude_numeric'].to_numpy(), frame.loc[good, 'longitude_numeric'].to_numpy())
    frame.loc[good, 'nearest_scheduled_airport_km'] = distance
    frame.loc[good, 'nearest_airport_ident'] = airports.iloc[index].ident.to_numpy()
    frame.loc[good, 'nearest_airport_name'] = airports.iloc[index].name.to_numpy()
    frame.loc[good, 'nearest_airport_region'] = airports.iloc[index].iso_region.to_numpy()
    return frame

def weighted_quantile(values, weights, quantile):
    positive = weights > 0
    values = values[positive]
    weights = weights[positive]
    if not len(values):
        return None
    order = np.argsort(values, kind='stable')
    cumulative = np.cumsum(weights[order], dtype=np.float64)
    index = np.searchsorted(cumulative, quantile * cumulative[-1], side='left')
    return float(values[order[index]])

def summarize(frame):
    valid = frame.valid_coordinates & frame.valid_population
    distances = frame.loc[valid, 'nearest_scheduled_airport_km'].to_numpy(dtype=float)
    population = frame.loc[valid, 'population_numeric'].to_numpy(dtype=float)
    total = float(population.sum())
    record = {'settlements': len(frame), 'with_valid_coordinates': int(frame.valid_coordinates.sum()), 'missing_or_coded_population': int((~frame.valid_population).sum()), 'zero_population_settlements': int((frame.valid_population & (frame.population_numeric == 0)).sum()), 'population_with_valid_coordinates_and_population': total, 'population_without_valid_coordinates': float(frame.loc[~frame.valid_coordinates & frame.valid_population, 'population_numeric'].sum())}
    for threshold in [50, 100, 200]:
        within = float(population[distances <= threshold].sum())
        record[f'population_within_{threshold}km'] = within
        record[f'population_share_within_{threshold}km'] = within / total if total else None
        record[f'settlements_within_{threshold}km'] = int((distances <= threshold).sum())
    record['population_weighted_median_km'] = weighted_quantile(distances, population, 0.5)
    record['population_weighted_p90_km'] = weighted_quantile(distances, population, 0.9)
    return record

settlements = enrich(settlements)
federal = enrich(federal)
records = [{'region': region, **summarize(group)} for region, group in settlements.groupby('region', sort=True)]
regional = regional_catalog.rename(columns={'population': 'native_region_population'}).merge(pd.DataFrame(records), on='region', how='left')
for column in ['settlements', 'with_valid_coordinates', 'missing_or_coded_population', 'zero_population_settlements', 'population_with_valid_coordinates_and_population', 'population_without_valid_coordinates', 'population_within_50km', 'population_within_100km', 'population_within_200km', 'settlements_within_50km', 'settlements_within_100km', 'settlements_within_200km']:
    regional[column] = regional[column].fillna(0)
regional['native_region_population'] = pd.to_numeric(regional.native_region_population, errors='coerce')
regional['settlement_population_fraction_of_native_region_total'] = regional.population_with_valid_coordinates_and_population / regional.native_region_population
regional.to_csv(out / 'distance_by_native_region.csv', index=False)
federal.drop(columns=['latitude_numeric', 'longitude_numeric', 'population_numeric']).to_csv(out / 'federal_city_centres_separate.csv', index=False)
columns = ['object_name', 'region', 'oktmo', 'population_numeric', 'latitude_numeric', 'longitude_numeric', 'nearest_scheduled_airport_km', 'nearest_airport_ident', 'nearest_airport_name', 'nearest_airport_region']
top = settlements[settlements.valid_coordinates & settlements.valid_population & (settlements.population_numeric > 0)].nlargest(20, 'nearest_scheduled_airport_km')[columns]
top.to_csv(out / 'top20_farthest_populated_settlements.csv', index=False)
top_large = settlements[settlements.valid_coordinates & settlements.valid_population & (settlements.population_numeric >= 1000)].nlargest(20, 'nearest_scheduled_airport_km')[columns]
top_large.to_csv(out / 'top20_farthest_settlements_at_least_1000_people.csv', index=False)

same, _ = nearest(airports.latitude_deg.to_numpy()[:8], airports.longitude_deg.to_numpy()[:8])
assert np.allclose(same, 0, atol=1e-8)
assert settlements.nearest_scheduled_airport_km.dropna().ge(0).all()
assert settlements.valid_coordinates.all()
assert regional.loc[regional.settlements > 0, ['population_share_within_50km', 'population_share_within_100km', 'population_share_within_200km']].apply(lambda row: row.iloc[0] <= row.iloc[1] <= row.iloc[2], axis=1).all()
assert weighted_quantile(np.array([1., 2., 3.]), np.array([1., 8., 1.]), .5) == 2.
assert weighted_quantile(np.array([1., 2., 3.]), np.array([1., 8., 1.]), .9) == 2.
assert weighted_quantile(np.array([1., 2., 3.]), np.array([1., 8., 1.]), .95) == 3.
summary = {'method': 'minimum Haversine great-circle distance to 157 nonclosed airports with scheduled_service=yes; no route or travel time inference', 'earth_radius_km': radius_km, 'population_basis': 'Census 2020–2021; source CSV version 2026-09-25', 'airports_basis': 'OurAirports downloaded 2026-11-06; schedule flag is not verified operational schedule', 'strict_settlements': summarize(settlements), 'strict_region_count': settlements.region.nunique(), 'regional_output_rows': len(regional), 'regional_rows_without_settlements': regional.loc[regional.settlements == 0, 'region'].tolist(), 'scheduled_airports': len(airports), 'federal_cities_not_added_to_settlement_population': True, 'quantile_definition': 'inverse weighted empirical CDF: first sorted distance with cumulative positive population >= q*total; no interpolation', 'top20_at_least_1000_people': top_large.to_dict('records'), 'validation': {'same_coordinate_airport_checks': len(same), 'same_coordinate_max_distance_km': float(same.max()), 'coordinate_range_checks': True, 'nonnegative_distances': True, 'threshold_monotonicity': True, 'weighted_quantile_boundary_examples': True}, 'input_sha256': {str(path.relative_to(args.repo)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [archive, airport_path]}}
discrepancies = regional[(regional.settlement_population_fraction_of_native_region_total > 1.00001) | ((regional.settlement_population_fraction_of_native_region_total < .99999) & (regional.settlements > 0))]
summary['native_region_population_discrepancies_or_partial_federal_city_coverage'] = discrepancies[['region', 'population_with_valid_coordinates_and_population', 'native_region_population', 'settlement_population_fraction_of_native_region_total']].to_dict('records')
(out / 'results.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: value for key, value in summary.items() if key not in ['top20_at_least_1000_people', 'input_sha256']}, ensure_ascii=False, indent=2))
