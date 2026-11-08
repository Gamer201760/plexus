import sys
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))
from indices import palma
from manual_links import link_hours
from seasonality import operating_season
from graphlib import load_edges, build_csr
from scipy.sparse.csgraph import dijkstra
from graph_russia import contract


class TransportModelTests(unittest.TestCase):
    def test_palma_splits_settlement_population_at_quantiles(self):
        self.assertAlmostEqual(palma(np.ones(3), np.array([45., 45., 10.])), 0.25)

    def test_frequency_changes_wait_for_infrequent_services(self):
        links = pd.DataFrame({
            "from_id": ["a"] * 3, "to_id": ["b"] * 3,
            "mode": ["air"] * 3, "km": [200.] * 3, "freq_per_week": [1., 2., 3.],
        })
        points = pd.DataFrame({"point_id": ["a", "b"], "lat": [50., 51.], "lon": [90., 91.]})
        result = link_hours(links, points)
        np.testing.assert_allclose(result.wait_h, [84., 42., 28.])
        self.assertTrue(result.h.is_monotonic_decreasing)

    def test_palma_handles_missing_zero_and_invalid_weights(self):
        self.assertAlmostEqual(palma(np.array([1., np.nan, 1.]), np.array([45., 10., 45.])), .25)
        self.assertTrue(np.isnan(palma(np.zeros(2), np.ones(2))))
        self.assertTrue(np.isinf(palma(np.array([0., 1.]), np.array([90., 10.]))))
        with self.assertRaises(ValueError):
            palma(np.ones(2), np.array([-1., 2.]))
        self.assertAlmostEqual(palma(np.ones(3), np.array([.45, .45, .1])), .25)

    def test_unknown_frequency_is_preserved_and_assumption_marked(self):
        links = pd.DataFrame({
            "from_id": ["a"], "to_id": ["b"], "mode": ["air"],
            "km": [200.], "freq_per_week": [np.nan],
        })
        points = pd.DataFrame({"point_id": ["a", "b"], "lat": [50., 51.], "lon": [90., 91.]})
        result = link_hours(links, points)
        self.assertTrue(np.isnan(result.freq_per_week.iloc[0]))
        self.assertTrue(result.freq_assumed.iloc[0])
        self.assertEqual(result.wait_h.iloc[0], 84.)

    def test_seasonal_tags_are_conservative(self):
        for key in ("ice_road", "winter_road"):
            self.assertEqual(operating_season({key: "yes"}), "winter")
        self.assertEqual(operating_season({"seasonal": "summer"}), "summer")
        self.assertEqual(operating_season({"seasonal": "yes"}), "unknown")
        self.assertEqual(operating_season({"route": "ferry"}), "unknown")
        self.assertEqual(operating_season({"highway": "primary"}), "all")

    def test_closed_edges_are_removed_before_route_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            pq.write_table(pa.table({"src": [0, 1, 0], "dst": [1, 2, 2],
                                     "h": [1., 1., 5.], "way_idx": [0, 1, 2]}), directory / "edges.parquet")
            pq.write_table(pa.table({"operating_season": ["all", "winter", "all"]}), directory / "ways.parquet")
            with patch("graphlib.GRAPH", directory):
                for season, expected in (("summer", 5.), ("winter", 2.), ("road", 5.)):
                    edges = load_edges(season)
                    graph = build_csr(edges["src"], edges["dst"], edges["h"], 3)
                    self.assertEqual(dijkstra(graph, indices=0)[2], expected)

    def test_reverse_oneway_is_retained_in_compressed_graph(self):
        vertices = {"nid": np.array([10, 20]), "lat": np.array([50., 50.01]),
                    "lon": np.array([90., 90.]), "wov": np.array([0, 0]),
                    "starts": np.array([0]), "ends": np.array([1])}
        _, _, _, edges = contract(vertices, np.array([True, True]), np.array([30.]), np.array([2]))
        self.assertEqual(list(zip(edges["S"], edges["D"])), [(1, 0)])


if __name__ == "__main__":
    unittest.main()
