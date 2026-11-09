import argparse
import hashlib
import itertools
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    archive = next((args.input_root / 'raw').glob('*csv.zip'))
    with zipfile.ZipFile(archive) as z:
        member = next(n for n in z.namelist() if n.endswith('.csv') and '__MACOSX' not in n)
        frame = pd.read_csv(z.open(member), sep=';')
    road = frame[frame.transport_type == 'road']
    cities = road[['city_from', 'region_from', 'population_from', 'is_capital_from']].drop_duplicates().rename(columns=lambda name: name.replace('_from', '')).sort_values('city').reset_index(drop=True)
    assert len(cities) == 180 and cities.city.nunique() == 180
    matrix = road.pivot(index='city_from', columns='city_to', values='distance_hr').reindex(index=cities.city, columns=cities.city).to_numpy(float)
    matrix = np.where(np.isfinite(matrix), matrix, np.inf)
    n = len(cities)
    nonself = ~np.eye(n, dtype=bool)
    outside = cities.region.to_numpy()[:, None] != cities.region.to_numpy()[None, :]
    capitals = cities.is_capital.to_numpy() == 1
    masks = {'all_180': nonself, 'source_capitals': nonself & capitals[None, :], 'outside_admin_region': nonself & outside, 'source_capitals_outside_admin_region': nonself & outside & capitals[None, :]}
    results = []
    for name, mask in masks.items():
        weights = mask * cities.population.to_numpy(float)[None, :]
        denominator = weights.sum(axis=1)
        assert (denominator > 0).all()
        known = np.isfinite(matrix) & mask
        value = (weights * np.exp(-matrix / 12)).sum(axis=1) / denominator
        unknown_weight = (weights * ~np.isfinite(matrix)).sum(axis=1) / denominator
        out = cities.copy()
        out['destination_set'] = name
        out['eligible_destinations'] = mask.sum(axis=1)
        out['known_destinations'] = known.sum(axis=1)
        out['known_population_share'] = (weights * np.isfinite(matrix)).sum(axis=1) / denominator
        out['potential_tau12_lower'] = value
        out['potential_tau12_upper'] = value + unknown_weight
        out['rank'] = pd.Series(value).rank(ascending=False, method='min').astype(int)
        results.append(out)
    result = pd.concat(results, ignore_index=True)
    result.to_csv(args.out / 'destination_set_accessibility.csv', index=False)
    comparisons = []
    for left_name, right_name in itertools.combinations(masks, 2):
        left = result[result.destination_set == left_name].set_index('city')
        right = result[result.destination_set == right_name].set_index('city').loc[left.index]
        left_score = left.potential_tau12_lower
        right_score = right.potential_tau12_lower
        shifts = right['rank'] - left['rank']
        comparisons.append({'left_set': left_name, 'right_set': right_name, 'spearman': float(np.corrcoef(left_score.rank(), right_score.rank())[0, 1]), 'max_absolute_rank_shift': int(shifts.abs().max()), 'median_absolute_rank_shift': float(shifts.abs().median()), 'top20_common': len(set(left.nlargest(20, 'potential_tau12_lower').index) & set(right.nlargest(20, 'potential_tau12_lower').index))})
    pd.DataFrame(comparisons).to_csv(args.out / 'rank_comparisons.csv', index=False)
    wide = result.pivot(index='city', columns='destination_set', values=['rank', 'potential_tau12_lower'])
    wide.columns = ['__'.join(parts) for parts in wide.columns]
    wide = wide.reset_index().merge(cities, on='city', how='left')
    for name in masks:
        wide[f'rank_shift__{name}'] = wide[f'rank__{name}'] - wide['rank__all_180']
    wide.to_csv(args.out / 'city_rank_shifts.csv', index=False)
    examples = []
    for name in masks:
        top = result[result.destination_set == name].nlargest(10, 'potential_tau12_lower').copy()
        top['example_group'] = 'top10'
        examples.append(top)
    pd.concat(examples).to_csv(args.out / 'top_examples.csv', index=False)
    flags = cities.groupby('region', as_index=False).agg(selected_cities=('city', 'size'), flagged_capitals=('is_capital', 'sum'))
    flags.to_csv(args.out / 'capital_flags_by_region.csv', index=False)
    summary = {'rows': len(frame), 'road_rows': len(road), 'cities': n, 'source_capital_flags': int(capitals.sum()), 'source_capital_flag_values': {str(k): int(v) for k, v in cities.is_capital.value_counts().items()}, 'region_count': int(cities.region.nunique()), 'regions_with_no_capital_flag': flags.loc[flags.flagged_capitals == 0, 'region'].tolist(), 'regions_with_multiple_capital_flags': flags.loc[flags.flagged_capitals > 1, 'region'].tolist(), 'input_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'tau_hours': 12, 'mode': 'road', 'unknown_convention': 'Unknown OD contributes zero to conditional lower estimate; upper adds all unknown destination population share. This is not evidence of actual inaccessibility.', 'denominator': 'Population of eligible destination cities, recomputed for each origin and destination-set mask; self excluded.', 'admin_region_note': 'Uses exact region labels from the source, not functional agglomerations. Moscow and Moscow Oblast remain distinct administrative labels.', 'comparisons': comparisons}
    (args.out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    assert len(result) == 720
    assert (result.potential_tau12_lower >= 0).all()
    assert (result.potential_tau12_upper <= 1 + 1e-12).all()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
