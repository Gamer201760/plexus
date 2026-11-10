import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'etl'))
from graphlib import build_csr
from market_distances import market_distances


class MarketDistanceTests(unittest.TestCase):
    def test_parallel_market_search_matches_original_undirected_search(self):
        graph = build_csr(np.array([0, 0, 1, 1, 2, 3]), np.array([1, 1, 0, 2, 3, 4]),
                          np.array([5., 2., 3., .25, 80., 0.], dtype=np.float32), 6,
                          undirected=True).astype(np.float64)
        cities, points = np.array([4, 0, 5]), np.array([5, 1, 3, 0, 2])
        expected = np.atleast_2d(dijkstra(graph, directed=False, indices=cities))
        for workers in (1, 2):
            point_times, city_times = market_distances(graph, cities, points, workers)
            np.testing.assert_array_equal(point_times, expected[:, points].astype(np.float32))
            np.testing.assert_array_equal(city_times, expected[:, cities])
            self.assertGreater(city_times[0, 1], 72)
            self.assertTrue(np.isinf(city_times[2, 0]))


if __name__ == '__main__':
    unittest.main()
