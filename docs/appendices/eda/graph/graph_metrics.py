import numpy as np
import pandas as pd


def accessibility(matrix, cities, mode):
    population = cities['population'].to_numpy(float)
    total = population.sum() - population
    known = np.isfinite(matrix)
    weights = population[None, :] / total[:, None]
    nonself = ~np.eye(len(cities), dtype=bool)
    eligible = known & nonself
    records = cities[['city', 'region', 'population']].copy()
    records['mode'] = mode
    records['known_destinations'] = eligible.sum(axis=1)
    records['known_destination_share'] = eligible.sum(axis=1) / (len(cities) - 1)
    records['known_population_share'] = (weights * eligible).sum(axis=1)
    unknown = nonself & ~known
    for hours in [6, 12, 24]:
        reached = (matrix <= hours) & eligible
        records[f'destinations_within_{hours}h'] = reached.sum(axis=1)
        records[f'destination_share_within_{hours}h'] = reached.sum(axis=1) / (len(cities) - 1)
        records[f'population_share_within_{hours}h'] = (weights * reached).sum(axis=1)
        potential = (weights * np.exp(-matrix / hours) * nonself).sum(axis=1)
        records[f'potential_tau{hours}_lower'] = potential
        records[f'potential_tau{hours}_upper'] = potential + (weights * unknown).sum(axis=1)
        records[f'rank_tau{hours}'] = pd.Series(potential).rank(ascending=False, method='min').astype(int)
    return records


def sensitivity(access):
    records = []
    for mode in ['road', 'best_ground']:
        rows = access[access['mode'] == mode]
        for a, b in [(6, 12), (6, 24), (12, 24)]:
            left = rows[f'potential_tau{a}_lower']
            right = rows[f'potential_tau{b}_lower']
            top_left = set(rows.nlargest(20, f'potential_tau{a}_lower')['city'])
            top_right = set(rows.nlargest(20, f'potential_tau{b}_lower')['city'])
            records.append({'comparison': 'decay_parameter', 'mode': mode, 'tau_a': a, 'tau_b': b, 'spearman': float(np.corrcoef(left.rank(), right.rank())[0, 1]), 'top20_common': len(top_left & top_right), 'largest_rank_change': int((left.rank(ascending=False, method='min') - right.rank(ascending=False, method='min')).abs().max())})
    for tau in [6, 12, 24]:
        left = access[access['mode'] == 'road'].set_index('city')
        right = access[access['mode'] == 'best_ground'].set_index('city').loc[left.index]
        records.append({'comparison': 'modal_choice', 'mode': 'road_vs_best_ground', 'tau_a': tau, 'tau_b': tau, 'spearman': float(np.corrcoef(left[f'potential_tau{tau}_lower'].rank(), right[f'potential_tau{tau}_lower'].rank())[0, 1]), 'top20_common': len(set(left.nlargest(20, f'potential_tau{tau}_lower').index) & set(right.nlargest(20, f'potential_tau{tau}_lower').index)), 'largest_rank_change': int((left[f'rank_tau{tau}'] - right[f'rank_tau{tau}']).abs().max())})
    return pd.DataFrame(records)


def triangle_audit(matrix, city_names, tolerance=0.15):
    size = len(matrix)
    nonself = ~np.eye(size, dtype=bool)
    violations = np.zeros_like(matrix, dtype=bool)
    indirect_known = np.zeros_like(matrix, dtype=bool)
    comparisons = 0
    violating_triples = 0
    largest = None
    for k in range(size):
        candidate = matrix[:, k, None] + matrix[k, None, :]
        valid = nonself & np.isfinite(candidate)
        valid[k, :] = False
        valid[:, k] = False
        comparable = valid & np.isfinite(matrix)
        differences = np.zeros_like(matrix)
        np.subtract(matrix, candidate, out=differences, where=comparable)
        bad = comparable & (differences > tolerance)
        comparisons += int(comparable.sum())
        violating_triples += int(bad.sum())
        violations |= bad
        indirect_known |= valid & ~np.isfinite(matrix)
        if bad.any():
            i, j = np.unravel_index(np.argmax(np.where(bad, differences, -np.inf)), matrix.shape)
            example = {'from': city_names[i], 'via': city_names[k], 'to': city_names[j], 'direct_hours': float(matrix[i, j]), 'sum_two_od_hours': float(candidate[i, j]), 'difference_hours': float(differences[i, j])}
            if largest is None or example['difference_hours'] > largest['difference_hours']:
                largest = example
    return {'tolerance_hours': tolerance, 'comparable_ordered_triples': comparisons, 'violating_ordered_triples': violating_triples, 'unique_ordered_od_pairs_in_violations': int(violations.sum()), 'missing_direct_od_with_two_observed_od_legs': int(indirect_known.sum()), 'largest_example': largest, 'interpretation': 'Consistency diagnostic of pairwise OD estimates only. Summed OD times are not validated transfers; missing direct rows do not prove physical disconnection.'}
