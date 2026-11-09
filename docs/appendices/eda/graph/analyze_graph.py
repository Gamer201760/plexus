import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from graph_metrics import accessibility, sensitivity, triangle_audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    archive = next((args.input_root / 'raw').glob('*csv.zip'))
    with zipfile.ZipFile(archive) as z:
        member = next(n for n in z.namelist() if n.endswith('.csv') and '__MACOSX' not in n)
        frame = pd.read_csv(z.open(member), sep=';', dtype={'oktmo_from': str, 'oktmo_to': str})
    fields = ['city', 'region', 'oktmo', 'population', 'lat', 'lon', 'is_capital', 'sber_territory_id']
    city_rows = []
    for side in ['from', 'to']:
        city_rows.append(frame[[f'{key}_{side}' for key in fields]].rename(columns={f'{key}_{side}': key for key in fields}))
    city_frame = pd.concat(city_rows, ignore_index=True)
    consistency = city_frame.groupby('city')[fields[1:]].nunique(dropna=False)
    inconsistent = consistency[(consistency != 1).any(axis=1)]
    cities = city_frame.drop_duplicates().sort_values(['region', 'city']).reset_index(drop=True)
    assert inconsistent.empty
    names = cities['city'].tolist()
    lookup = {name: i for i, name in enumerate(names)}
    n = len(cities)
    assert n == 180
    assert not frame.duplicated(['city_from', 'city_to', 'transport_type']).any()
    self_rows = frame[frame['city_from'] == frame['city_to']]
    assert self_rows.empty
    matrices = {}
    mode_summary = {}
    missing_city = []
    for mode, part in frame.groupby('transport_type'):
        matrix = np.full((n, n), np.inf)
        kms = np.full((n, n), np.inf)
        i = part['city_from'].map(lookup).to_numpy()
        j = part['city_to'].map(lookup).to_numpy()
        matrix[i, j] = part['distance_hr'].fillna(np.inf)
        kms[i, j] = part['distance_km'].fillna(np.inf)
        matrices[mode] = matrix
        assert len(part) == n * (n - 1)
        available = part.dropna(subset=['distance_km', 'distance_hr'])
        distances = available['distance_km'].to_numpy(float)
        times = available['distance_hr'].to_numpy(float)
        finite = np.isfinite(matrix)
        assert (distances > 0).all() and (times > 0).all()
        symmetric_values = np.where(finite, matrix, 0)
        residual = times - (distances / 75 + 0.5 if mode == 'road' else distances / 55 if mode == 'rail' else distances / 840 + 0.75)
        linear = np.polyfit(distances, times, 1)
        mode_summary[mode] = {'rows': len(part), 'observed': len(available), 'missing_both': int(part['distance_km'].isna().sum()), 'time_missing_only': int((part['distance_hr'].isna() & part['distance_km'].notna()).sum()), 'distance_missing_only': int((part['distance_km'].isna() & part['distance_hr'].notna()).sum()), 'asymmetric_availability_pairs': int((finite != finite.T).sum()), 'asymmetric_time_pairs': int((np.abs(symmetric_values - symmetric_values.T) > 1e-9).sum()), 'asymmetric_distance_pairs': int((np.abs(np.where(np.isfinite(kms), kms, 0) - np.where(np.isfinite(kms), kms, 0).T) > 1e-9).sum()), 'distance_km_quantiles': dict(zip(['min', 'p25', 'median', 'p75', 'max'], map(float, np.quantile(distances, [0, .25, .5, .75, 1])))), 'time_hours_quantiles': dict(zip(['min', 'p25', 'median', 'p75', 'max'], map(float, np.quantile(times, [0, .25, .5, .75, 1])))), 'time_model_residual_quantiles_hours': dict(zip(['min', 'median', 'max'], map(float, np.quantile(residual, [0, .5, 1])))), 'rows_within_0_051h_of_generic_model': int((np.abs(residual) <= .051).sum()), 'fitted_time_slope_hours_per_km': float(linear[0]), 'fitted_time_intercept_hours': float(linear[1]), 'source_counts': {str(k): int(v) for k, v in part['source'].value_counts(dropna=False).items()}, 'missing_reason_counts': {str(k): int(v) for k, v in part['missing_reason'].value_counts(dropna=False).items()}}
        for city, records in part.groupby('city_from'):
            valid = records['distance_hr'].notna()
            missing_city.append({'city': city, 'region': records['region_from'].iloc[0], 'mode': mode, 'pairs': len(records), 'observed': int(valid.sum()), 'unknown': int((~valid).sum()), 'unknown_share': float((~valid).mean())})
    matrices['best_ground'] = np.minimum(matrices['road'], matrices['rail'])
    access = pd.concat([accessibility(matrices[mode], cities, mode) for mode in ['road', 'best_ground']], ignore_index=True)
    access.to_csv(args.out / 'accessibility.csv', index=False)
    cities.to_csv(args.out / 'cities.csv', index=False)
    sensitivity(access).to_csv(args.out / 'rank_sensitivity.csv', index=False)
    missing = pd.DataFrame(missing_city)
    missing.to_csv(args.out / 'missingness_by_city_mode.csv', index=False)
    missing.groupby(['region', 'mode'], as_index=False).agg(cities=('city', 'nunique'), pairs=('pairs', 'sum'), observed=('observed', 'sum'), unknown=('unknown', 'sum')).to_csv(args.out / 'missingness_by_region_mode.csv', index=False)
    region = cities.groupby('region', as_index=False).agg(represented_cities=('city', 'size'), represented_city_population_2021=('population', 'sum'))
    region.to_csv(args.out / 'city_coverage_by_region.csv', index=False)
    examples = []
    for mode in ['road', 'best_ground']:
        subset = access[access['mode'] == mode]
        for group, selected in [('top10', subset.nlargest(10, 'potential_tau12_lower')), ('bottom10', subset.nsmallest(10, 'potential_tau12_lower'))]:
            out = selected.copy()
            out['example_group'] = group
            examples.append(out)
    pd.concat(examples).to_csv(args.out / 'ranking_examples.csv', index=False)
    triangle = {mode: triangle_audit(matrices[mode], names) for mode in ['road', 'rail', 'best_ground']}
    a = lookup['Кострома']
    b = lookup['Обнинск']
    scenario_road = matrices['road'].copy()
    before = float(scenario_road[a, b])
    scenario_road[a, b] *= .8
    scenario_road[b, a] *= .8
    scenario = []
    for mode, matrix in [('road', scenario_road), ('best_ground', np.minimum(scenario_road, matrices['rail']))]:
        after_access = accessibility(matrix, cities, mode)
        previous = access[access['mode'] == mode].reset_index(drop=True)
        metrics = [column for column in previous if column.startswith(('destinations_within_', 'population_share_within_', 'potential_tau')) and not column.endswith('_upper')]
        deltas = after_access[metrics] - previous[metrics]
        assert (deltas.to_numpy() >= -1e-12).all()
        assert np.allclose(deltas.drop(index=[a, b]).to_numpy(), 0)
        for index in [a, b]:
            for metric in metrics:
                scenario.append({'city': names[index], 'mode': mode, 'metric': metric, 'before': float(previous.loc[index, metric]), 'after': float(after_access.loc[index, metric]), 'difference': float(deltas.loc[index, metric])})
    pd.DataFrame(scenario).to_csv(args.out / 'hypothetical_scenario.csv', index=False)
    scenario_info = {'description': 'Illustrative parameter perturbation only: reduce road OD time between Kostroma and Obninsk by 20% in both directions. No physical project, feasibility, cost, new road, induced rerouting or real service benefit asserted.', 'cities': ['Кострома', 'Обнинск'], 'road_hours_before': before, 'road_hours_after': before * .8, 'monotonicity_check': 'passed for all 180 origins, both modes and all reported accessibility measures', 'propagation': 'Only the two OD cells change; no shortest-path closure or inferred transfers.'}
    zero = {mode: access.loc[(access['mode'] == mode) & (access['known_destinations'] == 0), 'city'].tolist() for mode in ['road', 'best_ground']}
    summary = {'input_archive': str(archive), 'input_archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'input_member': member, 'rows': len(frame), 'columns': len(frame.columns), 'cities': n, 'region_labels': cities['region'].nunique(), 'city_population_2021_sum': int(cities['population'].sum()), 'duplicate_od_mode_rows': 0, 'self_rows': 0, 'city_metadata_consistent_across_all_records_and_sides': inconsistent.empty, 'unique_oktmo': int(cities['oktmo'].nunique()), 'unique_sber_territory_ids': int(cities['sber_territory_id'].nunique()), 'city_latitude_range': [float(cities.lat.min()), float(cities.lat.max())], 'city_longitude_range': [float(cities.lon.min()), float(cities.lon.max())], 'city_population_range': [int(cities.population.min()), int(cities.population.max())], 'modes': mode_summary, 'triangle_diagnostics': triangle, 'region_city_count_distribution': {str(k): int(v) for k, v in region['represented_cities'].value_counts().sort_index().items()}, 'no_observed_destinations': zero, 'scenario': scenario_info, 'measure_conventions': {'comparison_universe': 'Other 179 cities in the supplied 180-city selection; excludes self.', 'ground_mode_choice': 'Minimum of observed road and rail OD time, no transfers.', 'unknown_od': 'Missing time contributes zero to lower-bound measures; unknown accessibility is not asserted to be zero.', 'population_potential': 'sum_j population_j exp(-time_ij/tau) / sum_j population_j, j!=i, tau=6/12/24h; population fixed at census2021.', 'potential_upper': 'Lower bound plus all population share of unknown OD, a loose mathematical upper bound under nonnegative times; no probabilistic interpretation.', 'ranking': 'Exploratory ordering under these conventions; not validated transport wellbeing or region rankings.', 'source_average_error': 'Publisher claims average error about11% on an unspecified validation sample; not an uncertainty interval for each OD.'}}
    (args.out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=lambda v: bool(v) if isinstance(v, np.bool_) else int(v)))
    assert (access.filter(regex='^potential_tau.*_lower').to_numpy() >= -1e-12).all()
    assert (access.filter(regex='^potential_tau.*_upper').to_numpy() <= 1 + 1e-12).all()
    print(json.dumps({'rows': len(frame), 'cities': n, 'zero_observed': zero, 'triangle': triangle, 'scenario': scenario_info}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
